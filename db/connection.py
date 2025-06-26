from utils.imports import *
import sqlite3
import atexit
import contextlib
import os

# Define the path to the SQLite database file
# It will be created in the 'db' directory, alongside this connection.py file.
DB_FILE = os.path.join(os.path.dirname(__file__), "app.db")


@contextlib.contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # To get results as dict-like rows
    try:
        yield conn
    finally:
        conn.close()


@contextlib.contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit: # For SQLite, commit is often explicit
                conn.commit()
        except sqlite3.Error as e: # Catch SQLite specific errors
            conn.rollback()
            raise e
        finally:
            cursor.close()


# @atexit.register # No longer needed for sqlite3 simple connection
# def cleanup():
#     pass # db_pool.closeall() # Removed as db_pool is removed
