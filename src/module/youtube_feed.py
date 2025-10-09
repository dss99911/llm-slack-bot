import db
from module.api import answer
from utils.imports import *
import feedparser
import schedule
import time


def run():
    insert_youtube_urls(db.YoutubeStatus.COMPLETED)  # ignore old feeds
    job()
    schedule.every(10).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(schedule.idle_seconds())


def job():
    insert_youtube_urls()
    urls = db.select_all(db.YoutubeURL, db.YoutubeURL.status == db.YoutubeStatus.INSERTED)
    logging.info(f"youtube new urls: {len(urls)}")
    for url in urls:
        res = slack.send_message(f"<@{url.user_id}> {url.url}", url.channel_id)
        answer(f"{url.url}", url.user_id, url.channel_id, res['ts'])
        url.status = db.YoutubeStatus.COMPLETED
        db.upsert(url)


def insert_youtube_urls(status: db.YoutubeStatus = db.YoutubeStatus.INSERTED):
    for feed in db.select_all(db.YoutubeFeed):
        for url in fetch_youtube_urls(feed.url):
            youtube_url = db.YoutubeURL(url=url, channel_id=feed.channel_id, user_id=feed.user_id, status=status)
            try:
                db.insert(youtube_url)
            except db.IntegrityError:
                # ignore if already exists
                pass


def fetch_youtube_urls(playlist_url):
    feed = feedparser.parse(playlist_url)
    return [entry.link for entry in feed.entries]
