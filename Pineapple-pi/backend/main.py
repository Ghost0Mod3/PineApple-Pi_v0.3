from contextlib import asynccontextmanager
from pathlib import Path
import os,time,psutil
from fastapi import FastAPI,APIRouter,Cookie,Depends,HTTPException,Query,Request,Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from backend.config import settings
from backend.database import initialize_database,connect
from backend import core
class Credentials(BaseModel):username:str;password:str=Field(min_length=12,max_length=256)
class PasswordChange(BaseModel):current_password:str;new_password:str=Field(min_length=12,max_length=256)
@asynccontextmanager
async def life(app):initialize_database();yield
app=FastAPI(title=settings.app_name,version=settings.app_version,lifespan=life);api=APIRouter(prefix='/api')
def user(pineapple_session:str|None=Cookie(default=None,alias=settings.cookie_name)):
 s=core.session(pineapple_session)
 if not s:raise HTTPException(401,'Authentication required')
 return s
def admin(u=Depends(user)):
 if u['role']!='administrator':raise HTTPException(403,'Administrator required')
 return u
def cookie(resp,token):resp.set_cookie(settings.cookie_name,token,max_age=settings.session_absolute_hours*3600,httponly=True,secure=settings.cookie_secure,samesite='strict',path='/')
@api.get('/auth/status')
def auth_status(pineapple_session:str|None=Cookie(default=None,alias=settings.cookie_name)):
 s=core.session(pineapple_session);return {'setup_required':core.setup_required(),'authenticated':bool(s),'user':{'username':s['username'],'role':s['role']} if s else None}
@api.post('/auth/setup')
def setup(x:Credentials,resp:Response):
 try:uid=core.create_admin(x.username,x.password)
 except ValueError as e:raise HTTPException(400,str(e))
 cookie(resp,core.new_session(uid));core.activity('auth.setup','Administrator created',uid,'success');return {'status':'ok'}
@api.post('/auth/login')
def login(x:Credentials,req:Request,resp:Response):
 key=f"{req.client.host if req.client else 'unknown'}:{x.username.lower()}"
 if not core.login_allowed(key):raise HTTPException(429,'Too many attempts; try later')
 u=core.verify(x.username,x.password)
 if not u:core.login_failed(key);core.activity('auth.failed',f"Failed login for {x.username}",severity='warning');raise HTTPException(401,'Invalid username or password')
 core.login_clear(key);cookie(resp,core.new_session(u['id']));core.activity('auth.login','Administrator signed in',u['id'],'success');return {'status':'ok'}
@api.post('/auth/logout')
def logout(resp:Response,pineapple_session:str|None=Cookie(default=None,alias=settings.cookie_name)):
 core.revoke(pineapple_session);resp.delete_cookie(settings.cookie_name,path='/');return {'status':'ok'}
@api.post('/auth/change-password')
def change(x:PasswordChange,resp:Response,u=Depends(admin)):
 with connect() as db:r=db.execute('SELECT password_hash FROM users WHERE id=?',(u['user_id'],)).fetchone()
 try:core.PH.verify(r['password_hash'],x.current_password)
 except:raise HTTPException(400,'Current password is incorrect')
 t=core.iso()
 with connect() as db:db.execute('UPDATE users SET password_hash=?,password_changed_at=? WHERE id=?',(core.PH.hash(x.new_password),t,u['user_id']));db.execute('UPDATE sessions SET revoked_at=? WHERE user_id=?',(t,u['user_id']))
 resp.delete_cookie(settings.cookie_name,path='/');return {'status':'ok'}
@api.get('/system/health')
def health(u=Depends(user)):
 temp=None
 try:
  for v in psutil.sensors_temperatures().values():
   if v:temp=v[0].current;break
 except:pass
 return {'hostname':os.uname().nodename,'cpu_percent':psutil.cpu_percent(.1),'memory_percent':psutil.virtual_memory().percent,'disk_percent':psutil.disk_usage('/').percent,'temperature_c':temp,'uptime_seconds':int(time.time()-psutil.boot_time())}
@api.get('/radios')
def get_radios(u=Depends(user)):return {'items':core.radios()}
@api.get('/networks')
def networks(limit:int=Query(200,ge=1,le=1000),u=Depends(user)):
 with connect() as db:return {'items':[dict(r) for r in db.execute('SELECT * FROM access_points ORDER BY last_seen DESC LIMIT ?',(limit,)).fetchall()]}
@api.get('/networks/summary')
def summary(u=Depends(user)):
 with connect() as db:
  total=db.execute('SELECT COUNT(*) FROM access_points').fetchone()[0];bands=db.execute("SELECT CASE WHEN frequency_mhz<3000 THEN '2.4 GHz' ELSE '5 GHz' END b,COUNT(*) n FROM access_points GROUP BY b").fetchall();last=db.execute('SELECT started_at,result_count,status FROM scan_runs ORDER BY id DESC LIMIT 1').fetchone()
 return {'total_access_points':total,'bands':{r['b']:r['n'] for r in bands},'last_scan':dict(last) if last else None}
@api.post('/scanner/run')
def run_scan(u=Depends(admin)):
 try:return core.scan(u['user_id'])
 except RuntimeError as e:raise HTTPException(503,str(e))
@api.get('/activity')
def events(limit:int=Query(100,ge=1,le=500),u=Depends(admin)):
 with connect() as db:return {'items':[dict(r) for r in db.execute('SELECT * FROM activity_events ORDER BY id DESC LIMIT ?',(limit,)).fetchall()]}
@api.get('/access-point/status')
def ap_status(u=Depends(user)):
 r=core.radios()[2];return {'interface':settings.access_point_interface,'installed':r['installed'],'approved':False,'broadcasting':False,'ssid':None,'client_count':0,'controls_enabled':False,'reason':'Hardware approval required' if r['installed'] else 'Adapter not installed'}
@api.get('/settings')
def settings_get(u=Depends(admin)):return {'management_interface':settings.management_interface,'scanner_interface':settings.scanner_interface,'access_point_interface':settings.access_point_interface,'active_radio_changes_enabled':False,'ap_controls_enabled':False}
app.include_router(api)
app.mount('/assets',StaticFiles(directory=settings.frontend_path/'assets'),name='assets')
@app.get('/healthz')
def healthz():return {'status':'ok'}
@app.get('/{path:path}',include_in_schema=False)
def spa(path=''):return FileResponse(settings.frontend_path/'index.html')
