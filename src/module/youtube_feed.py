import db
from module.api import answer
from utils.imports import *
import feedparser
import schedule
import time

#
# @dataclass
# class Feed:
#     url: str
#     channel_id: str
#     user_id: str
#
# hyun_feed = partial(Feed, channel_id="D086TAF545P", user_id="UA2TKHJPN")
#
#
# feeds = [
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?playlist_id=PLH3j6V0I2cbnKkqBX2mjhjXpY_mWMZH-S"),
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCeN2YeJcBCRJoXgzF_OU3qw"),
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCXq7NNALDnqafn3KFvIyJKA"),
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCC3yfxS5qC6PCwDzetUuEWg"),
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCOB62fKRT7b73X7tRxMuN2g"),
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UC1Do3xw9OuUk7FQuPTmSVOw"),
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCWV2Uy79TOpB1bk8hnq1nGw"),
#     hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCKTMvIu9a4VGSrpWy-8bUrQ"),
# ]


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
