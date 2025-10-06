from db.database import get_db_cursor

TABLE_NAME = "prompts"

CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    slack_id VARCHAR(100),
    slack_name VARCHAR(100),
    channel_id VARCHAR(100),
    channel_name VARCHAR(100),
    prompt VARCHAR(5000),
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_slack_channel UNIQUE (slack_id, channel_id)

);
"""

# 데이터 읽기 쿼리
SELECT_ALL = f"SELECT * FROM {TABLE_NAME};"

# 데이터 삽입 (중복 시 덮어쓰기)
INSERT_OR_UPDATE = f"""
INSERT INTO {TABLE_NAME} (slack_id, slack_name, channel_id, channel_name, prompt, updated_date)
VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
ON CONFLICT (slack_id, channel_id) 
DO UPDATE SET 
    slack_name = EXCLUDED.slack_name,
    channel_name = EXCLUDED.channel_name,
    prompt = EXCLUDED.prompt,
    updated_date = CURRENT_TIMESTAMP;
"""

# 특정 slack_id와 channel_id로 데이터 조회
SELECT_BY_SLACK_CHANNEL = f"""
SELECT * FROM {TABLE_NAME} WHERE slack_id = %s AND channel_id = %s;
"""


def create_table():
    """ 테이블이 존재하지 않으면 생성 """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(CREATE_TABLE)


def insert_or_update(slack_id, slack_name, channel_id, channel_name, prompt):
    """ 중복된 slack_id + channel_id가 있으면 업데이트, 없으면 삽입 """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(INSERT_OR_UPDATE, (slack_id, slack_name, channel_id, channel_name, prompt))


def get_all_prompts():
    """ 테이블의 모든 데이터를 조회 """
    with get_db_cursor() as cursor:
        cursor.execute(SELECT_ALL)
        return cursor.fetchall()


def get_prompt(slack_id, channel_id):
    """ 특정 slack_id + channel_id에 해당하는 데이터 조회 """
    with get_db_cursor() as cursor:
        cursor.execute(SELECT_BY_SLACK_CHANNEL, (slack_id, channel_id))
        return cursor.fetchone()


create_table()