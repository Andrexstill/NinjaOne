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
- D-4 **Revised 2026-10-07, based on what actually happened — see section 4.** Originally: "SCADA01 starts as unmanaged-monitorable (fed by the observer); installing the agent converts the same record to managed." In practice, installing the agent via the console's generic install command did **not** convert/merge the existing unmanaged record — it created a second, independent managed device (`ubusrv-0a0203`). We are keeping both side by side on purpose rather than merging them: it demonstrates both postures NinjaOne can offer on the same physical asset (full agent-managed vs. zero-touch unmanaged-monitorable), which is a better demo than a single converted record. Do not attempt to merge them without a new decision.
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
- **Installing the agent does not convert/merge an existing unmanaged record.** Running the console's generic install command on SCADA01 created a brand-new managed device (`ubusrv-0a0203`) alongside the pre-existing unmanaged `SCADA01` record — they coexist as two separate devices with different names, not one record transitioning state. Confirmed harmless for the observer (name-based resolution in `get_unmanaged_ids()` still finds `SCADA01` uniquely; see hard rule 6). We're keeping both on purpose (see D-4) since it demonstrates two real customer postures on one physical asset. If a true single-record conversion is ever needed, it would likely require installing from that specific unmanaged record's own "Install Agent" action (untested) rather than a generic script — don't assume this works without verifying first.

## 5. Current state of the observer

`ot_observer.py` (270 lines, sha256 `5c1f08d67f2b69c998082d0d25588f3b6e8cabca9d197311e8940c153950d35e`) is deployed at `/root/otmon/ot_observer.py` on JUMP01, mode 700, owner root. **Verified working end to end on 2026-10-04**: `--dry-run`, `--init`, and one real cycle all ran cleanly and every written field was confirmed in the NinjaOne console (plc01, plc02, SCADA01, and JUMP01's own Custom tab).

Design: read-only Modbus; state inferred from coils; debounce (2 consecutive failures before LOST); writes only changed JUMP01 fields; `--dry-run`, `--init`, `--loop SECONDS`.

**Resolved issue:** the earlier 30 s `ninjarmm-cli options` hang hypothesis (inherited stdin) is refuted. With `stdin=subprocess.DEVNULL` already in the script, a full `--dry-run` cycle (≈6 CLI calls, including SSH overhead) completed in 0.64 s.

**Access to JUMP01:** `labadmin`'s SSH key is authorized (passwordless). A scoped sudoers rule at `/etc/sudoers.d/otmon-observer` grants `labadmin` NOPASSWD only for `sudo /root/otmon/bin/python3 /root/otmon/ot_observer.py [any args]` — nothing else under `/root` is passwordless. Use `ssh jump01 "sudo -n /root/otmon/bin/python3 /root/otmon/ot_observer.py ..."`.

**Access to OT-HOST01:** `labadmin`'s SSH key is also authorized there (passwordless, via `~/.ssh/config` alias `othost01`, `ProxyJump jump01`). `labadmin` is already in the `docker` group, so `docker ps/stop/start` need no sudo.

**NinjaOne custom field setup note:** text-type custom fields on unmanaged records (`otprotocol`, `otruntime`, `otsoftware`, `otserviceports`) were initially created with a permission level that blocked script/CLI writes (`unmanaged-set` failed with "Unable to update read-only attribute"), while the checkbox field `otagentauthorized` worked. Fixed in the console by setting all script-written custom fields to Read/Write (matching `otagentauthorized`'s setting). Checklist of fields that must stay Read/Write: `otprotocol`, `otruntime`, `otsoftware`, `otserviceports`, `otagentauthorized`, `otprocessstate`, `ottanklevel`, `otcommsstatus`, `otlastobserved`, `otreachability` (unmanaged records) and `otplc01comms`, `otplc02comms`, `otscada01reach`, `otprocessidle`, `otsummary` (JUMP01).

A previous attempt to paste the script as a heredoc over SSH was truncated, leaving a broken file on JUMP01. Transfer files with `scp` and verify with `sha256sum` and `wc -l`. Never paste long heredocs.

## 6. Remaining tasks (in order)

1. ~~Deploy the observer (verify hash), time CLI calls from Python, run `--dry-run`, then `--init`, then one real cycle. Verify values in the console.~~ **Done 2026-10-04.**
2. ~~Failure test AT-01/AT-02: `docker stop plc01` on OT-HOST01, confirm `LOST` within 2 cycles, then `docker start plc01` and confirm recovery.~~ **Done 2026-10-05.** AT-01: cycle 1 after stop stayed `OK` (fails=1&lt;2, debounce holds), cycle 2 flipped to `LOST` (`otProcessState=UNKNOWN`, `otCommsStatus=LOST`, `otPlc01Comms=LOST` on JUMP01) — all confirmed in console. AT-02: one cycle after `docker start plc01` recovered immediately to `OK FILL` (debounce resets `fails=0` on first success) — confirmed in console.
3. ~~Run the observer as a systemd service (`--loop 60`, restart on failure, journald logging).~~ **Done 2026-10-05.** Unit file `Scripts/ot-observer.service` (repo) installed at `/etc/systemd/system/ot-observer.service`, enabled + started. Confirmed two consecutive cycles 60 s apart in `journalctl -u ot-observer`, `NRestarts=0`. **Caution:** do not run the script manually (even via the NOPASSWD sudoers rule) while the service is active — both would read/write `/root/otmon/state.json` concurrently. Stop the service first (`sudo systemctl stop ot-observer`) for any manual/debug run, then start it again.
4. ~~Draft the NinjaOne-side objects for the user to create in the console: conditions on the JUMP01 fields, alert, ticket template, and a diagnostic runbook script (read-only).~~ **Done 2026-10-07.** Full pipeline built in the console: 3 conditions on JUMP01 (`otplc01comms`/`otplc02comms`/`otscada01reach` equals `LOST`, Severity Critical, Priority High, auto-reset only "when no longer met" — no forced timeout), each running the `OT Diagnostic Runbook` automation (ShellScript, `Run as: System`, calls `/root/otmon/bin/python3 /root/otmon/ot_diagnostic_runbook.py` directly — no sudo needed, System already runs as root; test-run live from the console, output matched the SSH test exactly) and creating a ticket via the `OT Comms Loss` condition-rule automation (tag `Critical_OT`, Status `New`→`Resolved` on reset, re-opens and appends on retrigger instead of duplicating). **Still pending:** end-to-end validation (re-run AT-01/AT-02 and confirm the alert/runbook/ticket chain actually fires), see section 8.
5. **In progress 2026-10-07.** Squid deployed and Squid part + AT-03 done; agent-on-SCADA01-via-proxy (AT-04/05) still open. Details:
   - **Squid**: installed on JUMP01, config `Scripts/squid-ot-idmz.conf` (repo) at `/etc/squid/squid.conf`. Listens **only** on `10.10.30.2:3128` (the `ot0` interface) — confirmed via `ss -tlnp`, never bound to `eth0`, so no `ufw`/firewall change was needed or made; zero risk to SSH by construction. Deny-by-default ACL: only `.ninjarmm.com`, `.ninjarmm.net`, `.ingest.sentry.io`, `ninja-attachments.s3.us-west-2.amazonaws.com`, `ninjauploads.s3.amazonaws.com`, `.cloudfront.net` allowed, source restricted to `10.10.30.0/24`. Source for the allowlist: [NinjaOne Global Allowlist Information](https://ninjarmm.zendesk.com/hc/en-us/articles/211406886) (fetched 2026-10-07) — only the global, non-region, non-Remote, non-patching entries were used, since this phase only needs core agent check-in on SCADA01, not Remote/patching yet. Verified via `/var/log/squid/access.log`: `TCP_TUNNEL/200` for `app.ninjarmm.com`, `TCP_DENIED/403` for `example.com` (AT-05 mechanism confirmed, re-test once the real agent is on SCADA01). `labadmin` added to the `proxy` group so the log is readable without sudo (evidence collection).
   - **AT-03 — done.** SCADA01 turned out to be dual-homed with an unexpected DHCP default route on `eth0` (10.10.10.0/24, same segment as JUMP01's enterprise-side interface) — this contradicted D-3 and was pre-existing, not something we added. Fixed with a new netplan drop-in `Scripts/70-eth0-no-default-route.yaml` (repo) at `/etc/netplan/70-eth0-no-default-route.yaml` (`dhcp4-overrides: use-routes: false` — keeps the DHCP IP/DNS, drops the DHCP-supplied route; deliberately a new file rather than editing the cloud-init-owned `50-cloud-init.yaml`, which cloud-init could regenerate). After `netplan apply`: `ip route` shows no `default` line, `curl https://example.com` times out (`HTTP 000`), and SSH via the `scada01` alias (which rides the `ot0`/`10.10.30.0/24` path, not `eth0`) was unaffected — verified from a fresh connection, not the same session that applied the change.
   - **AT-04/AT-05 — done.** Agent installed on SCADA01 (user ran the console-generated install command directly, token never shared in chat per the secrets rule) and proxy-configured via `ninjarmm-agent -proxy-host 10.10.30.2 -proxy-port 3128` (its own CLI prompt, no user/password set), then `systemctl restart ninjarmm-agent`. Device came online as **managed** (`ubusrv-0a0203`, Device role: Linux Server, **Policy: `Berlin_Lab_Linux_Server`** — the same policy as JUMP01's 3 OT conditions, so SCADA01 now evaluates them too; harmless since it never has the `otplc0Xcomms`/`otscada01reach` fields populated, but worth knowing if it looks odd in the console). Confirmed in `/var/log/squid/access.log`: every request from `10.10.30.20` is `TCP_TUNNEL/200 CONNECT agent-ca.ninjarmm.com:443` — only the NinjaOne agent domain, nothing else, matching AT-04/05 exactly.

Task 5 is now fully done. Only task 6 remains (see below).
6. State-gated patch window using `otprocessidle`; Rapid SCADA export to a JUMP01 share (C-09); evidence collection.

Acceptance tests AT-01..AT-10 are in section 15 of the Phase 2 document.

## 8. NinjaOne console objects (task 4 spec, console-only — create manually)

Design source: Phase 2 doc, section 7 ("Observation and alerting pipeline"). Pattern: **alert on the observer (JUMP01), document on the observed (unmanaged records)**. All field names below are the real lowercase keys, not the Phase 2 doc's display names.

**Runbook script** (already deployed): `/root/otmon/ot_diagnostic_runbook.py` on JUMP01 (sha256 `ab2b78f29160022dd4339c78643ff4c84c7adbd361cca70f8aaeb0cd1c7c5cc6`, source in repo at `Scripts/ot_diagnostic_runbook.py`). Read-only (FC3 register 0 + TCP connect checks only, same discipline as the observer). Run it as `sudo /root/otmon/bin/python3 /root/otmon/ot_diagnostic_runbook.py` (covered by the same scoped NOPASSWD sudoers rule). Prints a plain-text report: live Modbus reachability for plc01/plc02, OT-HOST01 port reachability, SCADA01 port reachability, and the observer's last known `state.json`. Test-run live on 2026-10-05, output confirmed correct.

**Conditions** (create 3, each on device JUMP01 / `ubusrv-0a0201-jump01`, evaluating its own custom field — not the unmanaged records):
1. `otplc01comms` equals `LOST`
2. `otplc02comms` equals `LOST`
3. `otscada01reach` equals `LOST`

No extra "for N cycles" debounce needed at the condition level — the observer already debounces (`FAIL_THRESHOLD=2`) before it ever writes `LOST`, so a single-observation condition is correct and matches AT-01's "≤ 2 observer cycles" target.

**Alert**: one alert (or one per condition, technician's choice), severity **Critical**, triggered by the conditions above on JUMP01. Auto-resolve when the field returns to `OK` (matches AT-02: "alert auto-resolves"). Suggested name: `OT Comms Lost — <plc01|plc02|SCADA01>`.

**Automation on alert trigger**: run `/root/otmon/ot_diagnostic_runbook.py` on JUMP01 via the agent's script engine, capture stdout, attach to the ticket (mirrors Phase 2: "Automation: diagnostic runbook ... Ticket updated with runbook output").

**Ticket template** `OT Comms Loss`: Priority **Critical**, tag **Critical OT**, assign to the OT on-call queue/technician group. Description should reference which field tripped and the device's current `otsummary` value; body gets the runbook output appended by the automation above. Leave resolution manual even though the alert auto-resolves — a comms flap on OT kit deserves a human look before the ticket closes.

**Acceptance check — done 2026-10-07.** Root cause of the first failed attempt: the 3 conditions were created on a device-level override, not on the **policy** (`Berlin_Lab_Linux_Server`) actually assigned to JUMP01 — conditions only evaluate for devices running the policy they're defined in. Fixed, then re-ran `docker stop plc01` on OT-HOST01 twice:
- Condition triggered (`otplc01comms`→`LOST`) → ticket #1012 auto-created (`Policy: Berlin_Lab_Linux_Server`, Priority High, Severity Critical, tag `Critical_OT`) → `OT Diagnostic Runbook` ran automatically and confirmed `plc01 UNREACHABLE` live → condition reset (`otplc01comms`→`OK`) → ticket auto-moved to `Resolved`.
- Re-stopped plc01 while the ticket was `Resolved` (not `Closed`): condition retriggered and **reopened the same ticket #1012** (no duplicate #1013), matching the "Append to existing ticket (if not closed)" retrigger rule. Recovered again → `Resolved` again.
- **Known gap:** the runbook's text output lands in JUMP01's own Activity log (`Automations`/`Script` group) but is **not** copied into the ticket body/activity — they're two independent reactions to the same condition, not a pipeline. Lower priority to fix; the ticket plus the device Activity log together already have everything a technician needs. If closing this gap matters later, check whether NinjaOne's automation-attachment UI (the card for "OT Diagnostic Runbook" inside the condition editor) has an option to post its result as a ticket comment.
- Condition evaluation is not instant — expect a few minutes of lag after the observer writes a field change before the condition/ticket reacts (NinjaOne's own policy-check interval, independent of the observer's 60 s loop).

## 9. Evidence to keep

Raw command output for each acceptance test, Squid allowlist and access log, `ip route` of SCADA01 and JUMP01, observer logs, NinjaOne activity log screenshots. Strip secrets before saving anything.
