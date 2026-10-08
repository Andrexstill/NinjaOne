# Evidence — Phase 3 implementation

Collected evidence for the acceptance tests defined in the Phase 2 reference architecture document (section 15), gathered during implementation (2026-10-04 to 2026-10-08). Secrets stripped before saving — see `Context/CLAUDE.md` hard rule 3.

| AT | What it proves | Evidence |
|---|---|---|
| AT-01 | `docker stop plc01` → `LOST` within 2 observer cycles | `command-output/AT-01_AT-02_comms_lost_recovery.txt`, `screenshots/` 6-7 |
| AT-02 | `docker start plc01` → alert/field auto-resolves to `OK` | `command-output/AT-01_AT-02_comms_lost_recovery.txt`, `screenshots/` 8-9 |
| — | Full Condition→Alert→Runbook→Ticket pipeline, re-validated through the real console objects (not just the observer's field writes), including re-trigger without duplicating the ticket | `command-output/AT-condition-ticket-pipeline.txt`, `screenshots/` 31-42 |
| AT-03 | SCADA01 has no default route; direct egress fails | `command-output/AT-03_scada01_ip_route.txt`, `AT-03_netplan_dropin.txt` |
| AT-04 | Agent on SCADA01 via proxy; device online in console; Squid log shows only NinjaOne destinations | `command-output/AT-04_AT-05_squid_access_log.txt`, `AT-04_squid_listen_scope.txt`, `screenshots/` 43-50 |
| AT-05 | Non-allowlisted destination gets denied by Squid | `command-output/AT-04_AT-05_squid_access_log.txt` (`TCP_DENIED/403` for `example.com`) |
| AT-07 | Patch window aborts when the process isn't idle (or can't be confirmed idle) | `command-output/AT-07_AT-08_patch_gate_full_cycle.txt` |
| AT-08 | Patch window proceeds when the process is confirmed idle | `command-output/AT-07_AT-08_patch_gate_full_cycle.txt` |
| AT-10 | SCADA export lands on the JUMP01 share and is covered by a NinjaOne Backup plan | `command-output/AT-10_sftp_receiver_config.txt`, `AT-10_scada_export_cron.txt`, `screenshots/` 43-50 |

AT-06 and AT-09 (enterprise endpoint can't reach SCADA01 directly; observer code review for write function codes) aren't separately captured here — AT-06 follows directly from AT-03/04 (SCADA01 only reachable via JUMP01's `ot0` path) and AT-09 is satisfied by `Scripts/ot_observer.py` itself being the artifact (FC1/FC3 only, no write function codes — see its own module docstring).

## Supporting artifacts

- `command-output/sudoers_jump01_scope.txt`, `sudoers_scada01_scope.txt` — the scoped NOPASSWD rules used throughout, showing they're limited to the exact observer/runbook/patch-gate scripts, nothing broader.
- `command-output/observer_journal_recent.txt`, `observer_service_status.txt` — the systemd service (task 3) running continuously.
- `command-output/JUMP01_ip_route.txt` — JUMP01's dual-homed routing (sole egress point, per D-3).
- `command-output/AT-04_AT-05_squid_config.txt` — the full Squid allowlist config.

## Source code

The actual scripts and configs referenced throughout (not duplicated here) live in `Scripts/`: `ot_observer.py`, `ot_diagnostic_runbook.py`, `ot_patch_gate.py`, `ot_scada_export.sh`, `ot-observer.service`, `squid-ot-idmz.conf`, `70-eth0-no-default-route.yaml`, `60-scadaexport-sftp.conf`, `ot-scada-export.cron`, `ot-host.mk`.
