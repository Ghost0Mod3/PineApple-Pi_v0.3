import sqlite3
from contextlib import contextmanager
from backend.config import settings
SCHEMA=settings.database_path.parent/"schema/schema.sql"
def initialize_database():
 settings.database_path.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(settings.database_path,timeout=5) as db:db.executescript(SCHEMA.read_text());db.commit()
@contextmanager
def connect():
 db=sqlite3.connect(settings.database_path,timeout=5);db.row_factory=sqlite3.Row;db.execute("PRAGMA foreign_keys=ON")
 try:yield db;db.commit()
 finally:db.close()
