#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]]||exit 1
systemctl disable --now pineapple-pi-api.service pineapple-pi-scan.timer 2>/dev/null||true
rm -f /etc/systemd/system/pineapple-pi-{api.service,scan.service,scan.timer};systemctl daemon-reload
echo "Services removed; /opt/pineapple-pi retained."
