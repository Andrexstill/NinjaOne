# Screenshot index

Console screenshots captured during the Phase 3 implementation session (2026-10-04 to 2026-10-08), in chronological order. Grouped by milestone rather than captioned frame-by-frame — exact image-to-moment mapping below is a best-effort reconstruction from the session, not guaranteed frame-exact. Cross-reference with the PR history / session transcript if a specific frame's provenance matters.

| Files | Milestone |
|---|---|
| 1-5 | Task 1: first real observer cycle verified in the console (plc01, plc02, SCADA01, JUMP01 custom fields all matching the observer's output) |
| 6-7 | AT-01: `plc01` forced `LOST` (JUMP01 `otPlc01Comms` + plc01 `otCommsStatus`) |
| 8-9 | AT-02: `plc01` recovered to `OK` after `docker start` |
| 10-18 | Task 4 build-out: condition editor, Custom Fields rule (`otPlc01Comms equals LOST`), Automation Library, `OT Diagnostic Runbook` script creation and a manual test run (Activity details showing `Result: SUCCESS`), condition with the automation attached |
| 19-30 | Task 4 build-out: Ticketing admin, Condition rules, the `OT Comms Loss` ticket-automation wizard (General / Ticket creation / Condition reset / Condition retrigger tabs), Form/Status dropdown options |
| 31 | All 3 conditions (plc01/plc02/SCADA01) listed with the `OT Comms Loss` ticketing rule wired |
| 32-35 | Troubleshooting: checked the wrong device's Activities (`plc01`, an unmanaged record) first, then found the root cause — conditions were on a device-level override, not the policy actually assigned to JUMP01 |
| 36-40 | Fixed: ticket #1012 auto-created on condition trigger, `OT Diagnostic Runbook` ran automatically (Activity details with full output), ticket auto-`Resolved` on condition reset |
| 41-42 | Re-test: condition retriggered while the ticket was `Resolved` (not `Closed`) — same ticket #1012 reopened instead of a duplicate |
| 43-50 | Task 5: SCADA01 agent install coming online as managed (Policy `Berlin_Lab_Linux_Server`), and the NinjaOne Backup file/folder plan setup for the SCADA01 export landing share |

See `Context/CLAUDE.md` sections 5, 6, and 8 for the narrative this evidence supports, and `Evidence/command-output/` for the matching raw command-line evidence.
