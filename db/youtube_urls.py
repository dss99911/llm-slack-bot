from db.connection import get_db_cursor

TABLE_NAME = "youtube_urls"

STATUS_INSERTED = "inserted"
STATUS_COMPLETED = "compledted"


# 데이터 조작 함수
def create_table():
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    channel_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT DEFAULT '{STATUS_INSERTED}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_url UNIQUE (url, channel_id, user_id)
);
""")

def insert(url, channel_id, user_id, status=STATUS_INSERTED):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            f"INSERT INTO {TABLE_NAME} (url, channel_id, user_id, status) VALUES (?, ?, ?, ?) ON CONFLICT (url, channel_id, user_id) DO NOTHING;",
            (url, channel_id, user_id, status)
        )

def get_all_inserted():
    with get_db_cursor() as cursor:
        cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE status = ?;", (STATUS_INSERTED,))
        return cursor.fetchall()


def complete(url, channel_id, user_id):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(f"UPDATE {TABLE_NAME} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE url = ? and channel_id = ? and user_id = ?;",
                       (STATUS_COMPLETED, url, channel_id, user_id))

create_table()