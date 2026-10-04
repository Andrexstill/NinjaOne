#!/usr/bin/env python3
"""
OT observer for the NinjaOne OT reference lab (runs on JUMP01, Industrial DMZ).

Read-only towards the process: only Modbus FC1 (read coils) and FC3 (read
holding registers) are used. Results are written to NinjaOne through the local
agent CLI (ninjarmm-cli); no public-API credentials are involved.

Process state is inferred from the published coils because the internal
'State' variable of the ST programs is not mapped to any Modbus address.
"""
import argparse
import datetime
import json
import os
import socket
import subprocess
import time

from pymodbus.client import ModbusTcpClient

CLI = "/opt/NinjaRMMAgent/programdata/ninjarmm-cli"
CLI_TIMEOUT = 60
STATE_FILE = "/root/otmon/state.json"
FAIL_THRESHOLD = 2   # consecutive failures before a target is reported LOST
UNIT_ID = 1

PLCS = {
    "plc01": {"host": "10.10.30.10", "port": 502},
    "plc02": {"host": "10.10.30.10", "port": 5020},
}
SCADA_HOST = "10.10.30.20"
SCADA_PORTS = (10000, 443)
JUMP_COMMS = {"plc01": "otplc01comms", "plc02": "otplc02comms", "SCADA01": "otscada01reach"}


def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{ts} {msg}", flush=True)


def cli(*args):
    # stdin=DEVNULL: never let the CLI wait on an inherited terminal/pipe.
    r = subprocess.run([CLI, *args], capture_output=True, text=True,
                       timeout=CLI_TIMEOUT, stdin=subprocess.DEVNULL)
    return r.returncode, (r.stdout + r.stderr).strip()


def get_options(field):
    rc, out = cli("options", field)
    if rc != 0:
        raise RuntimeError(f"options {field} failed: {out}")
    mapping = {}
    for line in out.splitlines():
        if "=" in line:
            guid, label = line.split("=", 1)
            mapping[label.strip().upper()] = guid.strip()
    return mapping


def get_unmanaged_ids():
    rc, out = cli("unmanaged-get")
    if rc != 0:
        raise RuntimeError(f"unmanaged-get failed: {out}")
    return {d["name"]: d["id"] for d in json.loads(out)}


def read_plc(host, port):
    """FC3 holding registers 0..3 and FC1 coils 0..3. Nothing else."""
    client = ModbusTcpClient(host, port=port, timeout=2)
    try:
        if not client.connect():
            return None
        hr = client.read_holding_registers(0, count=4, device_id=UNIT_ID)
        co = client.read_coils(0, count=4, device_id=UNIT_ID)
        if hr.isError() or co.isError():
            return None
        return {"hr": list(hr.registers), "coils": [bool(b) for b in co.bits[:4]]}
    except Exception:
        return None
    finally:
        client.close()


def tcp_open(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def plc01_state(coils):
    inlet, mixer, pump, batch = coils
    if pump:
        return "TRANSFER"
    if mixer:
        return "MIX"
    if batch:
        return "READY"
    if inlet:
        return "FILL"
    return "UNKNOWN"


def plc02_state(coils, plc01_pump):
    _recv, cons, req, _running = coils
    if cons:
        return "CONSUME"
    if req and plc01_pump:
        return "RECEIVE"
    if req:
        return "REQUEST"
    return "UNKNOWN"


def load_state():
    try:
        with open(STATE_FILE) as f:
            s = json.load(f)
    except Exception:
        s = {}
    for k in ("fails", "status", "written"):
        s.setdefault(k, {})
    return s


def save_state(s):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
    os.replace(tmp, STATE_FILE)


def debounce(state, key, ok):
    fails = state["fails"].get(key, 0)
    if ok:
        fails, status = 0, "OK"
    else:
        fails += 1
        status = "LOST" if fails >= FAIL_THRESHOLD else state["status"].get(key, "UNKNOWN")
    state["fails"][key] = fails
    state["status"][key] = status
    return status


class Writer:
    def __init__(self, dry):
        self.dry = dry

    def unmanaged_set(self, dev_id, label, fields):
        if self.dry:
            log(f"[dry-run] unmanaged-set {label}: {fields}")
            return True
        rc, out = cli("unmanaged-set", json.dumps({"id": dev_id, "customFieldValues": fields}))
        if rc != 0:
            log(f"ERROR unmanaged-set {label}: {out}")
            return False
        return True

    def jump_set(self, field, value, state):
        if state["written"].get(field) == value:
            return
        if self.dry:
            log(f"[dry-run] set {field} = {value}")
            return
        rc, out = cli("set", field, value)
        if rc != 0:
            log(f"ERROR set {field}: {out}")
            return
        state["written"][field] = value


def run_cycle(args):
    state = load_state()
    w = Writer(args.dry_run)
    ids = get_unmanaged_ids()
    comms_opt = get_options("otcommsstatus")
    reach_opt = get_options("otreachability")
    jump_opt = {f: get_options(f) for f in JUMP_COMMS.values()}

    raw = {n: read_plc(p["host"], p["port"]) for n, p in PLCS.items()}
    scada_ok = all(tcp_open(SCADA_HOST, p) for p in SCADA_PORTS)
    status = {n: debounce(state, n, raw[n] is not None) for n in PLCS}
    status["SCADA01"] = debounce(state, "SCADA01", scada_ok)

    proc = {}
    if raw["plc01"]:
        proc["plc01"] = (plc01_state(raw["plc01"]["coils"]), raw["plc01"]["hr"][0])
    if raw["plc02"]:
        pump1 = bool(raw["plc01"] and raw["plc01"]["coils"][2])
        proc["plc02"] = (plc02_state(raw["plc02"]["coils"], pump1), raw["plc02"]["hr"][0])

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for n in PLCS:
        if n not in ids:
            log(f"WARN {n} not found in unmanaged-get (relation missing?)")
            continue
        if raw[n] is not None:
            st, tank = proc[n]
            fields = {"otprocessstate": st, "ottanklevel": tank,
                      "otcommsstatus": comms_opt["OK"], "otlastobserved": now}
        elif status[n] == "LOST":
            fields = {"otprocessstate": "UNKNOWN", "otcommsstatus": comms_opt["LOST"]}
        else:
            fields = None   # transient failure: change nothing yet
        if fields:
            w.unmanaged_set(ids[n], n, fields)

    if "SCADA01" in ids:
        w.unmanaged_set(ids["SCADA01"], "SCADA01",
                        {"otreachability": reach_opt[status["SCADA01"]]})
    else:
        log("WARN SCADA01 not found in unmanaged-get")

    idle = (status["plc01"] == "OK" and status["plc02"] == "OK"
            and "plc01" in proc and "plc02" in proc
            and proc["plc01"][0] == "READY" and proc["plc02"][0] == "CONSUME"
            and proc["plc02"][1] > 40)

    def desc(n):
        return f"{n} {status[n]}" + (f" {proc[n][0]} {proc[n][1]}%" if n in proc else "")
    summary = f"{desc('plc01')} | {desc('plc02')} | SCADA01 {status['SCADA01']}"

    for n, field in JUMP_COMMS.items():
        w.jump_set(field, jump_opt[field][status[n]], state)
    w.jump_set("otprocessidle", "true" if idle else "false", state)
    w.jump_set("otsummary", summary, state)

    log(f"{summary} | idle={idle}")
    if not args.dry_run:
        save_state(state)


def run_init(args):
    w = Writer(args.dry_run)
    ids = get_unmanaged_ids()
    static = {
        "plc01": {"otprotocol": "Modbus TCP", "otruntime": "OpenPLC Runtime v4"},
        "plc02": {"otprotocol": "Modbus TCP", "otruntime": "OpenPLC Runtime v4"},
        "SCADA01": {"otsoftware": "Rapid SCADA 6.5", "otserviceports": "10000, 443",
                    "otagentauthorized": "false"},
    }
    for name, fields in static.items():
        for field, value in fields.items():
            ok = w.unmanaged_set(ids[name], f"{name}.{field}", {field: value})
            log(f"init {name}.{field} = {value}: {'OK' if ok else 'FAILED'}")


def main():
    ap = argparse.ArgumentParser(description="OT observer (read-only towards the process)")
    ap.add_argument("--dry-run", action="store_true", help="read everything, write nothing")
    ap.add_argument("--init", action="store_true", help="write static asset fields once")
    ap.add_argument("--loop", type=int, default=0, metavar="SECONDS", help="repeat forever")
    args = ap.parse_args()
    if args.init:
        run_init(args)
        return
    while True:
        try:
            run_cycle(args)
        except Exception as e:
            log(f"ERROR cycle failed: {e}")
        if not args.loop:
            break
        time.sleep(args.loop)


if __name__ == "__main__":
    main()
