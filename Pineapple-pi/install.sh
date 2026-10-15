#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]]||{ echo "Run: sudo ./install.sh";exit 1; }
APP=/opt/pineapple-pi;USER_NAME=${SUDO_USER:-ghost0mod3};[[ "$USER_NAME" != root ]]||exit 1
apt-get update;apt-get install -y python3 python3-venv python3-pip network-manager iw iproute2 usbutils ethtool sqlite3 curl
mkdir -p "$APP";cp -a ./. "$APP/";mkdir -p "$APP"/{logs,database,data/{inventory,exports,backups,raw-scans,reports}};chown -R "$USER_NAME:$USER_NAME" "$APP"
sudo -u "$USER_NAME" python3 -m venv "$APP/venv";sudo -u "$USER_NAME" "$APP/venv/bin/pip" install --upgrade pip;sudo -u "$USER_NAME" "$APP/venv/bin/pip" install -r "$APP/requirements.txt"
[[ -f "$APP/.env" ]]||cp "$APP/.env.example" "$APP/.env";chown "$USER_NAME:$USER_NAME" "$APP/.env";chmod 600 "$APP/.env"
sudo -u "$USER_NAME" bash -lc "cd '$APP'&&'$APP/venv/bin/python' -m backend.cli init-db"
for u in pineapple-pi-api.service pineapple-pi-scan.service pineapple-pi-scan.timer;do sed "s/^User=.*/User=$USER_NAME/;s/^Group=.*/Group=$USER_NAME/" "$APP/systemd/$u">"/etc/systemd/system/$u";done
systemctl daemon-reload;systemctl enable --now pineapple-pi-api.service pineapple-pi-scan.timer;sleep 3;curl -fsS http://127.0.0.1:8000/healthz
