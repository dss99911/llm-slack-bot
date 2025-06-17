from db.youtube_urls import STATUS_COMPLETED
from module.api import answer
from utils.imports import *
import feedparser
from db import youtube_urls
import schedule
import time


@dataclass
class Feed:
    url: str
    channel_id: str
    user_id: str

hyun_feed = partial(Feed, channel_id="UA2TKHJPN", user_id="UA2TKHJPN")


feeds = [
    hyun_feed("https://www.youtube.com/feeds/videos.xml?playlist_id=PLH3j6V0I2cbnKkqBX2mjhjXpY_mWMZH-S"),
    hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCeN2YeJcBCRJoXgzF_OU3qw"),
    hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCXq7NNALDnqafn3KFvIyJKA"),
    hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCC3yfxS5qC6PCwDzetUuEWg"),
    hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCOB62fKRT7b73X7tRxMuN2g"),
    hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UC1Do3xw9OuUk7FQuPTmSVOw"),
    hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCWV2Uy79TOpB1bk8hnq1nGw"),
    hyun_feed("https://www.youtube.com/feeds/videos.xml?channel_id=UCKTMvIu9a4VGSrpWy-8bUrQ"),
]

url_cache = Cache()

def run():
    job()
    schedule.every(10).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(schedule.idle_seconds())


def job():
    urls = fetch_new_youtube_urls()
    logging.info(f"youtube new urls: {len(urls)}")
    for url in urls:
        res = slack.send_message(f"<@{url['user_id']}> {url['url']}", url['channel_id'])
        answer(url['url'], url['user_id'], res['channel'], res['ts'])
        youtube_urls.complete(url['url'], url['channel_id'], url['user_id'])

def fetch_new_youtube_urls():
    # read
    urls = [(url, feed.channel_id, feed.user_id)
            for feed in feeds
            for url in fetch_youtube_urls(feed.url)]

    # insert
    new_urls = url_cache.filter_new(urls)
    for url, channel_id, user_id in new_urls:
        youtube_urls.insert(url, channel_id, user_id)

    # cache
    url_cache.add_values(new_urls)
    url_cache.clean_old_values()

    # get all
    inserted_urls = youtube_urls.get_all_inserted()
    return inserted_urls


def set_all_existing_url_completed():
    urls = [(url, feed.channel_id, feed.user_id)
            for feed in feeds
            for url in fetch_youtube_urls(feed.url)]
    for url, channel_id, user_id in urls:
        youtube_urls.insert(url, channel_id, user_id, status=STATUS_COMPLETED)



def fetch_youtube_urls(playlist_url):
    feed = feedparser.parse(playlist_url)
    return [entry.link for entry in feed.entries]
