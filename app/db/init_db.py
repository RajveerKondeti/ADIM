import time
from sqlalchemy.exc import OperationalError
from app.db.session import engine
from app.db.base import Base

from app.models import project

def init_db():
    retries = 10
    while retries > 0:
        try:
            print("Trying to connect to DB...")
            Base.metadata.create_all(bind=engine)
            print("DB Connected ✅")
            return
        except OperationalError:
            print("DB not ready, retrying in 3 seconds...")
            time.sleep(3)
            retries -= 1

    raise Exception("Could not connect to DB after retries ❌")