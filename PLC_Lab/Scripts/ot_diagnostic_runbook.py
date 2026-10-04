#!/usr/bin/env python3
"""
OT diagnostic runbook for the NinjaOne OT reference lab (runs on JUMP01).

Triggered by the NinjaOne alert on *Comms = LOST*. Gathers extra read-only
context for the ticket: live Modbus reachability, OT-HOST01 Docker host
reachability, SCADA01 port reachability, and the observer's last known
state. Prints a plain-text report to stdout for the ticket/automation
output. Never writes to the process (FC1/FC3 only, same as the observer).
"""
import datetime
import json
import socket

from pymodbus.client import ModbusTcpClient

STATE_FILE = "/root/otmon/state.json"
UNIT_ID = 1

PLCS = {
    "plc01": {"host": "10.10.30.10", "port": 502},
    "plc02": {"host": "10.10.30.10", "port": 5020},
}
OTHOST01 = "10.10.30.10"
SCADA_HOST = "10.10.30.20"
SCADA_PORTS = (10000, 443)


def tcp_open(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def modbus_alive(host, port):
    """FC3 read of holding register 0 only. Nothing else, never a write."""
    client = ModbusTcpClient(host, port=port, timeout=2)
    try:
        if not client.connect():
            return False
        hr = client.read_holding_registers(0, count=1, device_id=UNIT_ID)
        return not hr.isError()
    except Exception:
        return False
    finally:
        client.close()


def last_known_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"could not read {STATE_FILE}: {e}"}


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"OT diagnostic runbook — {now}", ""]

    lines.append("-- Live Modbus reachability (FC3, read-only) --")
    for name, p in PLCS.items():
        alive = modbus_alive(p["host"], p["port"])
        lines.append(f"{name} ({p['host']}:{p['port']}): {'OK' if alive else 'UNREACHABLE'}")

    lines.append("")
    lines.append("-- OT-HOST01 Docker host reachability --")
    othost_up = tcp_open(OTHOST01, 502) or tcp_open(OTHOST01, 5020)
    lines.append(f"{OTHOST01}: {'at least one published PLC port open' if othost_up else 'both published ports closed'}")

    lines.append("")
    lines.append("-- SCADA01 service ports --")
    for port in SCADA_PORTS:
        lines.append(f"{SCADA_HOST}:{port}: {'OPEN' if tcp_open(SCADA_HOST, port) else 'CLOSED'}")

    lines.append("")
    lines.append("-- Observer last known state (state.json) --")
    lines.append(json.dumps(last_known_state(), indent=2))

    lines.append("")
    lines.append("No write function codes were used. No PLC program or config was touched.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
