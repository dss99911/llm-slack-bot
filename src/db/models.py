from enum import StrEnum

from sqlalchemy import TIMESTAMP, func, Column, DateTime, Text, Enum
from sqlalchemy.orm import declarative_base

from db.connection import engine

Base = declarative_base()
class YoutubeStatus(StrEnum):
    INSERTED = "INSERTED"
    COMPLETED = "COMPLETED"



def ColumnCreatedAt():
    return Column(TIMESTAMP, server_default=func.current_timestamp())


def ColumnUpdatedAt():
    return Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

class Prompt(Base):
    __tablename__ = "prompts"

    slack_id = Column(Text, primary_key=True)
    channel_id = Column(Text, primary_key=True)
    prompt = Column(Text)
    created_at = ColumnCreatedAt()
    updated_at = ColumnUpdatedAt()


class YoutubeFeed(Base):
    __tablename__ = "youtube_feeds"

    url = Column(Text, primary_key=True, nullable=False)
    channel_id = Column(Text, primary_key=True, nullable=False)
    user_id = Column(Text, primary_key=True, nullable=False)
    created_at = ColumnCreatedAt()
    updated_at = ColumnUpdatedAt()


class YoutubeURL(Base):
    __tablename__ = "youtube_urls"

    url = Column(Text, primary_key=True, nullable=False)
    channel_id = Column(Text, primary_key=True, nullable=False)
    user_id = Column(Text, primary_key=True, nullable=False)
    status = Column(Enum(YoutubeStatus))
    created_at = ColumnCreatedAt()
    updated_at = ColumnUpdatedAt()


Base.metadata.create_all(bind=engine)
