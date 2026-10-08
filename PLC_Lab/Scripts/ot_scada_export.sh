#!/bin/bash
# Scheduled export of the Rapid SCADA project/config to the JUMP01
# landing share (C-09). Runs on SCADA01 as root (cron). Packs only the
# project/config data, not the ~180 MB of application binaries -- those
# are reinstallable from the rapidscada .deb package, not evidence.
set -euo pipefail

SCADA_ROOT=/opt/scada
EXPORT_KEY=/root/.ssh/scada_export_key
REMOTE=scadaexport@10.10.30.2
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
ARCHIVE="/tmp/scada_export_${STAMP}.tar.gz"

tar -czf "$ARCHIVE" -C "$SCADA_ROOT" \
    BaseDAT Config Views Archive Project.txt Version.txt \
    ScadaAgent/Config ScadaServer/Config ScadaComm/Config ScadaWeb/config

sftp -o BatchMode=yes -o StrictHostKeyChecking=accept-new -i "$EXPORT_KEY" "$REMOTE" \
    <<< "put ${ARCHIVE} incoming/"

rm -f "$ARCHIVE"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) exported scada_export_${STAMP}.tar.gz"
