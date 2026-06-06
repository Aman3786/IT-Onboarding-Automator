# db_setup.py

from database import init_db
from seed import seed_database

init_db()
result = seed_database()

print(result)