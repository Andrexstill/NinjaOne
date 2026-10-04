# NinjaOne OT Reference Lab — Phase 3 Implementation Handoff

Read this file first. It is the authoritative context for continuing the work.
Chat language with the user: **Spanish**. All files, comments and documentation: **English**.

## 1. What this project is

A lab that proves how NinjaOne can govern the IT layer of an industrial network without touching the process, aligned with IEC 62443 zones/conduits and Purdue levels. Companion documents (same folder): `Phase0_...Evidence_Inventory.md`, `Phase1_...Business_Model.md`, `Phase2_...Reference_Architecture.md`. Phase 2 is the design; this phase implements and verifies it.

Guiding principle: **Manage Levels 3.5–5 like IT. Observe Level 2. Document Level 0–1. Never touch the process.**

Scope decisions already closed (do not reopen):
- D-1 Scope is PLCs + SCADA + the IDMZ components that govern them. No new PXE/provisioning profiles.
- D-2 plc01/plc02 are ITAM *unmanaged devices*, fed from JUMP01. No NinjaOne software ever on PLCs or the Docker host.
- D-3 SCADA01 gets the agent with egress **only** through an HTTP proxy on JUMP01; no default route.
- D-4 SCADA01 starts as unmanaged-monitorable (fed by the observer); installing the agent converts the same record to managed.
- D-5 Proxy is customer-supplied Squid with a NinjaOne-domain allowlist. NinjaOne Airgap/Proxy are internal roadmap context only; never present them as available.
- D-6 No Backup agent on SCADA01 (unsupported via proxy). Export Rapid SCADA project to a JUMP01 share instead.

## 2. Hard rules

1. **Read-only towards the process.** Modbus FC1 and FC3 only. Never write coils/registers, never call any write function code.
2. Do not modify the validated ST programs or the OpenPLC/Docker configuration on OT-HOST01 without explicit user approval. Exposing `State` at `%QW4` was discussed and deferred (it would reset plc02's cycle counter).
3. **Never print, request or store secrets**: NinjaOne tokens, passwords, hashes, API credentials. Do not use the NinjaOne public API from JUMP01; the observer uses the local agent CLI only, by design (no tenant-scoped secret in the IDMZ).
4. Working method: short concept, exact commands, run, show output, validate, then continue. Do not declare completion without evidence. Make a backup before changing anything that already works. Prefer reversible changes.
5. Ask before anything destructive or disruptive (`docker stop`, firewall changes that could cut SSH, reboots, deleting records).
6. Never hardcode device IDs; resolve unmanaged devices by name every cycle.

## 3. Environment (validated)

| Item | Value |
|---|---|
| JUMP01 (IDMZ) | hostname `ubusrv-0a0201` (NinjaOne name `ubusrv-0a0201-jump01`); `eth0` 10.10.10.124/24 with the only default route (via 10.10.10.1); `ot0` 10.10.30.2/24, no default route; local admin `labadmin` |
| JUMP01 tooling | venv `/root/otmon` (Python 3.12.3, pymodbus 3.15.0); agent CLI `/opt/NinjaRMMAgent/programdata/ninjarmm-cli`; `ninjarmm-agent` active; Squid **not installed**; ufw inactive |
| OT-HOST01 (Docker) | publishes plc01 at `10.10.30.10:502` and plc02 at `10.10.30.10:5020`; containers 172.30.0.11 / 172.30.0.12 on internal network `ot-field` |
| SCADA01 | 10.10.30.20, Rapid SCADA ports 10000 and 443 reachable from JUMP01 |
| NinjaOne | organization `Andres_Company`, location `Berlin_Lab`; ITAM enabled |

All JUMP01 reachability checks passed (502, 5020, 10000, 443, ping to SCADA01).

### Modbus map (zero-based, pymodbus 3.15 needs `device_id=1`)

- plc01: HR0 tank %, HR1 temp x10, HR2 mixer speed %, HR3 transfer flow L/min. Coils 0..3 = inlet valve, mixer, transfer pump, batch ready.
- plc02: HR0 tank %, HR1 temp x10, HR2 consumption flow, HR3 cycle counter (was 1246 on 2026-10-04). Coils 0..3 = receive valve, consumption pump, product request, process running.
- The internal `State` variable is **not** mapped to Modbus, so states are inferred from coils: plc01 TRANSFER (pump) > MIX (mixer) > READY (batch ready) > FILL (inlet). plc02 CONSUME (pump) / RECEIVE (request and plc01 pump) / REQUEST (request only).

## 4. NinjaOne facts learned by testing (not all are in the docs)

- Roles `OT-PLC` and `OT-SCADA-Server` exist. System relation **Monitored by / Monitors** exists. Records plc01 (id 59), plc02 (60), SCADA01 (61) exist, related to JUMP01 (IDs may change if recreated).
- `ninjarmm-cli --help` is invalid; use `help`. Subcommand help prints the generic text only.
- `unmanaged-get` lists only unmanaged devices **related to the managed device running it**, in the same org/location. Output is JSON; custom field keys are **lowercase** (`otprocessstate`).
- `unmanaged-set '{"id":N,"customFieldValues":{...}}'` works, and updates are partial.
- **Dropdown fields require the option GUID, not the label**, for both unmanaged-record fields and JUMP01 fields. `ninjarmm-cli options <field>` returns `GUID=LABEL` lines and works for both kinds, so resolve labels to GUIDs at runtime.
- Checkbox accepts `true`/`false` (read back as 1). Numeric accepts integers. DateTime accepts `YYYY-MM-DDTHH:MM:SS` (UTC).
- JUMP01 custom fields (created globally, so they also show on the unmanaged records; cleanup is a later nicety): `otplc01comms`, `otplc02comms`, `otscada01reach` (dropdowns OK/LOST/UNKNOWN), `otprocessidle` (checkbox), `otsummary` (text).
- Test residue currently in the tenant (will be overwritten by the first real cycle): test GUIDs in `otcommsstatus` of plc01/plc02, `otplc01comms`=UNKNOWN, `otprocessidle`=true, a sample `otsummary`, and `otprocessstate`/`ottanklevel` on plc01.

## 5. Current state of the observer

`ot_observer.py` (270 lines, sha256 `5c1f08d67f2b69c998082d0d25588f3b6e8cabca9d197311e8940c153950d35e`) is written and syntax-checked but **has not yet run successfully on JUMP01**. Target path: `/root/otmon/ot_observer.py`, mode 700.

Design: read-only Modbus; state inferred from coils; debounce (2 consecutive failures before LOST); writes only changed JUMP01 fields; `--dry-run`, `--init`, `--loop SECONDS`.

**Open issue:** in an earlier attempt `ninjarmm-cli options otcommsstatus` timed out after 30 s when called from Python, while it is instant in an interactive shell. Hypothesis (unverified): the CLI waits on an inherited stdin. The script now uses `stdin=subprocess.DEVNULL` and a 60 s timeout. First task is to measure CLI call times from Python and confirm or refute this.

A previous attempt to paste the script as a heredoc over SSH was truncated, leaving a broken file on JUMP01. Transfer files with `scp` and verify with `sha256sum` and `wc -l`. Never paste long heredocs.

## 6. Remaining tasks (in order)

1. Deploy the observer (verify hash), time CLI calls from Python, run `--dry-run`, then `--init`, then one real cycle. Verify values in the console (Custom tab; the Overview tab only shows some fields).
2. Failure test AT-01/AT-02: with user approval, `docker stop plc01` on OT-HOST01, confirm `LOST` within 2 cycles, then `docker start plc01` and confirm recovery.
3. Run the observer as a systemd service (`--loop 60`, restart on failure, journald logging). Do not rely on the NinjaOne scheduler's minimum interval.
4. Draft the NinjaOne-side objects for the user to create in the console: conditions on the JUMP01 fields, alert, ticket template, and a diagnostic runbook script (read-only).
5. Squid on JUMP01 bound to 10.10.30.2:3128 with a deny-by-default allowlist of NinjaOne endpoints; restrict 3128 to 10.10.30.0/24; take care not to lock out SSH. Then agent on SCADA01 through the proxy; verify no default route (AT-03/04/05).
6. State-gated patch window using `otprocessidle`; Rapid SCADA export to a JUMP01 share (C-09); evidence collection.

Acceptance tests AT-01..AT-10 are in section 15 of the Phase 2 document.

## 7. Evidence to keep

Raw command output for each acceptance test, Squid allowlist and access log, `ip route` of SCADA01 and JUMP01, observer logs, NinjaOne activity log screenshots. Strip secrets before saving anything.
