#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/pineapple-pi;venv/bin/pip install -r requirements.txt;venv/bin/python -m backend.cli init-db;sudo systemctl restart pineapple-pi-api.service pineapple-pi-scan.timer
