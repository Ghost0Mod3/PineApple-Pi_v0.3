from datetime import datetime,timedelta,timezone
from pathlib import Path
from collections import defaultdict,deque
from threading import Lock
import hashlib,json,secrets,subprocess,time
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from backend.config import settings
from backend.database import connect
PH=PasswordHasher(time_cost=2,memory_cost=19456,parallelism=1)
ATTEMPTS=defaultdict(deque);LOCK=Lock()
def now():return datetime.now(timezone.utc)
def iso(x=None):return (x or now()).isoformat()
def command(args,timeout=25):
 try:return subprocess.run(args,text=True,capture_output=True,timeout=timeout,check=False)
 except (FileNotFoundError,subprocess.TimeoutExpired) as e:raise RuntimeError(str(e))
def activity(kind,msg,user=None,severity="info"):
 with connect() as db:db.execute("INSERT INTO activity_events(created_at,user_id,event_type,severity,message) VALUES(?,?,?,?,?)",(iso(),user,kind,severity,msg[:1000]))
def setup_required():
 with connect() as db:return db.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None
def create_admin(username,password):
 username=username.strip()
 if not 3<=len(username)<=64:raise ValueError("Username must be 3 to 64 characters")
 if len(password)<12:raise ValueError("Password must be at least 12 characters")
 if not setup_required():raise ValueError("Administrator setup is complete")
 t=iso()
 with connect() as db:return db.execute("INSERT INTO users(username,password_hash,role,enabled,created_at,password_changed_at) VALUES(?,?,?,1,?,?)",(username,PH.hash(password),"administrator",t,t)).lastrowid
def verify(username,password):
 with connect() as db:r=db.execute("SELECT * FROM users WHERE username=? AND enabled=1",(username.strip(),)).fetchone()
 if not r:return None
 try:PH.verify(r["password_hash"],password);return dict(r)
 except VerifyMismatchError:return None
def token_hash(t):return hashlib.sha256(t.encode()).hexdigest()
def new_session(uid):
 token=secrets.token_urlsafe(32);t=now()
 with connect() as db:db.execute("INSERT INTO sessions VALUES(?,?,?,?,?,NULL)",(token_hash(token),uid,iso(t),iso(t),iso(t+timedelta(hours=settings.session_absolute_hours))))
 return token
def session(token):
 if not token:return None
 t=now();idle=t-timedelta(minutes=settings.session_idle_minutes)
 with connect() as db:
  r=db.execute("SELECT s.*,u.username,u.role,u.enabled FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.id_hash=?",(token_hash(token),)).fetchone()
  if not r or r["revoked_at"] or not r["enabled"]:return None
  if datetime.fromisoformat(r["expires_at"])<=t or datetime.fromisoformat(r["last_seen_at"])<=idle:
   db.execute("UPDATE sessions SET revoked_at=? WHERE id_hash=?",(iso(t),token_hash(token)));return None
  db.execute("UPDATE sessions SET last_seen_at=? WHERE id_hash=?",(iso(t),token_hash(token)));return dict(r)
def revoke(token):
 if token:
  with connect() as db:db.execute("UPDATE sessions SET revoked_at=? WHERE id_hash=?",(iso(),token_hash(token)))
def login_allowed(key):
 t=time.monotonic()
 with LOCK:
  q=ATTEMPTS[key]
  while q and t-q[0]>settings.login_window_seconds:q.popleft()
  return len(q)<settings.login_max_attempts
def login_failed(key):
 with LOCK:ATTEMPTS[key].append(time.monotonic())
def login_clear(key):
 with LOCK:ATTEMPTS.pop(key,None)
def radio(iface,role):
 base=Path('/sys/class/net')/iface;exists=base.exists();drv=None;mac=None
 if exists:
  try:drv=(base/'device/driver').resolve().name
  except OSError:pass
  try:mac=(base/'address').read_text().strip().lower()
  except OSError:pass
 nm=command(['nmcli','-t','-f','GENERAL.STATE,GENERAL.CONNECTION','device','show',iface]) if exists else None
 vals={}
 if nm:
  for line in nm.stdout.splitlines():k,_,v=line.partition(':');vals[k]=v
 return {'interface':iface,'role':role,'installed':exists,'state':vals.get('GENERAL.STATE','missing' if not exists else 'unknown'),'connection':vals.get('GENERAL.CONNECTION'),'driver':drv,'mac_address':mac,'identity_ok':True}
def radios():
 out=[radio(settings.management_interface,'management'),radio(settings.scanner_interface,'inventory-scanner'),radio(settings.access_point_interface,'access-point')]
 s=out[1];s['identity_ok']=s['mac_address']==settings.scanner_expected_mac and s['driver']==settings.scanner_expected_driver
 return out
def split_nmcli(line):
 out=[];cur='';esc=False
 for c in line:
  if esc:cur+=c;esc=False
  elif c=='\\':esc=True
  elif c==':':out.append(cur);cur=''
  else:cur+=c
 out.append(cur);return out
def scan(uid=None):
 route=command(['ip','route','show','default']).stdout
 if f"dev {settings.management_interface}" not in route:raise RuntimeError("Management route protection failed")
 rs=radios()
 if not rs[1]['identity_ok']:raise RuntimeError("wlan1 identity does not match approved scanner")
 r=command(['nmcli','-t','--escape','yes','-f','BSSID,SSID,CHAN,FREQ,SIGNAL,SECURITY','device','wifi','list','ifname',settings.scanner_interface,'--rescan','yes'],35)
 if r.returncode:raise RuntimeError(r.stderr.strip() or 'Scan failed')
 items=[]
 for line in r.stdout.splitlines():
  f=split_nmcli(line)
  if len(f)!=6 or f[0].count(':')!=5:continue
  def num(v):
   try:return int(v)
   except:return None
  items.append((f[1] or '<hidden>',f[0].lower(),num(f[2]),num(f[3]),num(f[4]),f[5] or 'OPEN/UNKNOWN'))
 t=iso()
 with connect() as db:
  db.execute("INSERT INTO scan_runs(started_at,interface,result_count,status) VALUES(?,?,?,'ok')",(t,settings.scanner_interface,len(items)))
  for x in items:db.execute("INSERT INTO access_points(ssid,bssid,channel,frequency_mhz,signal_percent,security,first_seen,last_seen,sightings) VALUES(?,?,?,?,?,?,?, ?,1) ON CONFLICT(bssid) DO UPDATE SET ssid=excluded.ssid,channel=excluded.channel,frequency_mhz=excluded.frequency_mhz,signal_percent=excluded.signal_percent,security=excluded.security,last_seen=excluded.last_seen,sightings=access_points.sightings+1",(*x,t,t))
 activity('scan.completed',f"wlan1 scan completed with {len(items)} observations",uid,'success');return {'status':'ok','interface':settings.scanner_interface,'observed':len(items),'timestamp':t}
