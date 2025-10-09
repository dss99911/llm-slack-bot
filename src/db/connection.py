from utils.imports import *
from sqlalchemy.exc import IntegrityError
import os
import atexit
import contextlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sqlalchemy

DATABASE_URL = (
    f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@db:5432/{os.environ['POSTGRES_DB']}"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)

@contextlib.contextmanager
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def insert(data):
    data = make_list(data)
    with get_db() as db:
        db.add_all(data)
        db.commit()
        
        
def upsert(data):
    data = make_list(data)
    with get_db() as db:
        for item in data:
            db.merge(item)
        db.commit()



def select_all(cls, cond=None):
    with get_db() as db:
        stmt = sqlalchemy.select(cls)
        if cond is not None:
            stmt = stmt.where(cond)
        return [row for row in db.scalars(stmt)]


def select_one(cls, cond=None):
    with get_db() as db:
        stmt = sqlalchemy.select(cls)
        if cond is not None:
            stmt = stmt.where(cond)

        return db.scalars(stmt).one_or_none()


@atexit.register
def cleanup():
    engine.dispose()
