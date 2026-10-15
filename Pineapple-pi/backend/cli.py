import argparse,json
from backend.database import initialize_database
from backend.core import scan
p=argparse.ArgumentParser();p.add_argument('command',choices=['init-db','scan']);a=p.parse_args()
initialize_database()
print('Database initialized' if a.command=='init-db' else json.dumps(scan(),indent=2))
