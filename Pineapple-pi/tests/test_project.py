from pathlib import Path
from backend.main import app
def test_routes():
 p={r.path for r in app.routes};assert {'/healthz','/api/auth/status','/api/auth/login','/api/system/health','/api/access-point/status'}<=p
def test_no_default_password():assert 'password=' not in Path('.env.example').read_text().lower()
def test_auth_schema():
 s=Path('database/schema/schema.sql').read_text();assert 'CREATE TABLE IF NOT EXISTS users' in s and 'CREATE TABLE IF NOT EXISTS sessions' in s
