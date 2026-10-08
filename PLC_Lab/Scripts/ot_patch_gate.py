#!/usr/bin/env python3
"""
Patch-window gate for the NinjaOne OT reference lab (runs on SCADA01).

Read-only towards the process: only Modbus FC1 (read coils) and FC3
(read holding registers) are used, same discipline as the observer.
SCADA01 sits on the same OT network as the PLCs (10.10.30.0/24), so it
checks their live state directly instead of depending on a custom
field on another device -- no cross-device read, no API token.

Exit 0 (safe to patch) only when plc01 is READY and plc02 is CONSUME
with its tank above 40%, mirroring the observer's own idle criteria.
Exit 1 (abort, do not patch/reboot) for every other case, including
any Modbus read failure -- fail closed, not open.
"""
import datetime
import sys

from pymodbus.client import ModbusTcpClient

UNIT_ID = 1
PLCS = {
    "plc01": {"host": "10.10.30.10", "port": 502},
    "plc02": {"host": "10.10.30.10", "port": 5020},
}
IDLE_TANK_THRESHOLD = 40


def log(msg):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{ts} {msg}", flush=True)


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


def main():
    raw = {n: read_plc(p["host"], p["port"]) for n, p in PLCS.items()}

    if raw["plc01"] is None or raw["plc02"] is None:
        log("ABORT: could not read one or both PLCs live -- failing closed")
        sys.exit(1)

    st1 = plc01_state(raw["plc01"]["coils"])
    pump1 = raw["plc01"]["coils"][2]
    st2 = plc02_state(raw["plc02"]["coils"], pump1)
    tank2 = raw["plc02"]["hr"][0]

    idle = st1 == "READY" and st2 == "CONSUME" and tank2 > IDLE_TANK_THRESHOLD

    log(f"plc01={st1} plc02={st2} tank2={tank2}%")
    if idle:
        log("PROCEED: process idle, safe to patch")
        sys.exit(0)
    else:
        log("ABORT: process not idle, do not patch/reboot")
        sys.exit(1)


if __name__ == "__main__":
    main()
