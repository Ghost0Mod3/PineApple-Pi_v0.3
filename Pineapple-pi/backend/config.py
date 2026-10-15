from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv
BASE=Path(__file__).resolve().parent.parent
load_dotenv(BASE/".env")
def path_env(k,d):
 p=Path(os.getenv(k,str(d)));return p if p.is_absolute() else BASE/p
def flag(k,d=False):return os.getenv(k,str(d)).lower() in {"1","true","yes","on"}
@dataclass(frozen=True)
class Settings:
 app_name:str=os.getenv("APP_NAME","Pineapple-Pi")
 app_version:str=os.getenv("APP_VERSION","0.2.0")
 database_path:Path=path_env("DATABASE_PATH",BASE/"database/pineapple_pi.db")
 frontend_path:Path=path_env("FRONTEND_PATH",BASE/"frontend")
 management_interface:str=os.getenv("MANAGEMENT_INTERFACE","wlan0")
 scanner_interface:str=os.getenv("SCANNER_INTERFACE","wlan1")
 access_point_interface:str=os.getenv("ACCESS_POINT_INTERFACE","wlan2")
 scanner_expected_mac:str=os.getenv("SCANNER_EXPECTED_MAC","80:af:ca:eb:92:07").lower()
 scanner_expected_driver:str=os.getenv("SCANNER_EXPECTED_DRIVER","rtw88_8822bu")
 allow_active_radio_changes:bool=flag("ALLOW_ACTIVE_RADIO_CHANGES")
 cookie_name:str=os.getenv("SESSION_COOKIE_NAME","pineapple_session")
 cookie_secure:bool=flag("SESSION_COOKIE_SECURE")
 session_idle_minutes:int=int(os.getenv("SESSION_IDLE_MINUTES","30"))
 session_absolute_hours:int=int(os.getenv("SESSION_ABSOLUTE_HOURS","8"))
 login_window_seconds:int=int(os.getenv("LOGIN_WINDOW_SECONDS","300"))
 login_max_attempts:int=int(os.getenv("LOGIN_MAX_ATTEMPTS","5"))
settings=Settings()
