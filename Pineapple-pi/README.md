# PineApple-Pi v0.2.0
Flattened Raspberry Pi wireless inventory appliance.

## Radio roles
- `wlan0`: protected management, SSH, Raspberry Pi Connect, dashboard and internet
- `wlan1`: NetworkManager-managed nearby AP inventory scanner
- `wlan2`: future password-protected Pineapple-Pi access point

## Included
- FastAPI server, SQLite, static responsive sidebar dashboard
- First-run administrator setup and server login
- Argon2id password hashes, server-side sessions, login throttling
- Network inventory and manual/scheduled scans
- Settings → AP Setup; controls remain locked until wlan2 hardware approval
- Activity audit log and Legal & Capabilities page
- systemd API service and scan timer

## Install
```bash
chmod +x install.sh update.sh uninstall.sh scripts/*.sh
sudo ./install.sh
```
Open `http://pineapplepi.local:8000` and create the administrator. There is no default password.

## Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m backend.cli init-db
pytest -q
uvicorn backend.main:app --host 0.0.0.0 --port 8001
```
Never commit `.env`, database files, environments, logs, backups, reports or scans.
