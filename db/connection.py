from utils.imports import *
from psycopg2 import pool
import atexit

from psycopg2.extras import RealDictCursor
import contextlib


DB_CONFIG = {
    'dbname': os.environ["POSTGRES_DB"],
    'user': os.environ["POSTGRES_USER"],
    'password': os.environ["POSTGRES_PASSWORD"],
    'host': "db",
    'port': '5432'
}

db_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, **DB_CONFIG)


@contextlib.contextmanager
def get_db_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)


@contextlib.contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit or cursor.rowcount > 0:
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


@atexit.register
def cleanup():
    db_pool.closeall()
