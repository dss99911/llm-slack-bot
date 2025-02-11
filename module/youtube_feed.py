from module.api import answer
from utils.imports import *
import feedparser
from db import youtube_urls


@dataclass
class Feed:
    url: str
    channel_id: str
    user_id: str

feeds = [
    Feed(
        url="https://www.youtube.com/feeds/videos.xml?playlist_id=PLH3j6V0I2cbnKkqBX2mjhjXpY_mWMZH-S",
        channel_id="UA2TKHJPN",
        user_id="UA2TKHJPN"
    ),
    Feed(
        url="https://www.youtube.com/feeds/videos.xml?channel_id=UCeN2YeJcBCRJoXgzF_OU3qw",
        channel_id="UA2TKHJPN",
        user_id="UA2TKHJPN"
    ),
]

url_cache = Cache()

def run():
    timer = threading.Timer(60, job)
    timer.daemon = True
    timer.start()

def job():
    urls = fetch_new_youtube_urls()
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


def fetch_youtube_urls(playlist_url):
    feed = feedparser.parse(playlist_url)
    return [entry.link for entry in feed.entries]
