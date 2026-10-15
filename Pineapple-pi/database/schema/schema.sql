PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS access_points(id INTEGER PRIMARY KEY,ssid TEXT,bssid TEXT UNIQUE NOT NULL,channel INTEGER,frequency_mhz INTEGER,signal_percent INTEGER,security TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,sightings INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS scan_runs(id INTEGER PRIMARY KEY,started_at TEXT NOT NULL,interface TEXT NOT NULL,result_count INTEGER NOT NULL,status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'administrator',enabled INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,password_changed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(id_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,created_at TEXT NOT NULL,last_seen_at TEXT NOT NULL,expires_at TEXT NOT NULL,revoked_at TEXT,FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS activity_events(id INTEGER PRIMARY KEY,created_at TEXT NOT NULL,user_id INTEGER,event_type TEXT NOT NULL,severity TEXT NOT NULL,message TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(id));
CREATE INDEX IF NOT EXISTS idx_ap_last_seen ON access_points(last_seen);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
