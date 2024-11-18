import base64
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config import conversation_count_limit
from util.common import memoize

slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_app_token = os.environ["SLACK_APP_TOKEN"]

app = App(token=slack_bot_token)
client = app.client

executor = ThreadPoolExecutor(max_workers=20)

class SlackEvent:
    def __init__(self, event):
        self.event = event


    @property
    def channel(self):
        return self.event["channel"]

    @property
    def ts(self):
        return self.event["ts"]

    @property
    def edited(self):
        return self.event.get("edited")

    @property
    def thread_ts(self):
        return self.event.get("thread_ts")

    @property
    def user(self):
        return self.event["user"]

    @property
    def user_name(self):
        return get_user_real_name(self.user)

    @property
    def text(self):
        return self.event.get("text")

    @property
    def files(self):
        return self.event.get("files")

    def is_edited(self):
        return self.edited is not None

    def is_in_thread(self):
        return self.thread_ts is not None

    def reply_on_thread(self, message):
        send_message(message, self.channel, self.ts)

    def get_thread_conversation(self, limit=conversation_count_limit):
        return client.conversations_replies(channel=self.channel, ts=self.thread_ts, limit=limit)["messages"]

    def get_encoded_images(self):
        image_urls = self.extract_image_urls()
        base64_images = []
        for url in image_urls:
            base64_data = download_and_encode_image(url)
            if base64_data:
                base64_images.append(base64_data)
        return base64_images

    def extract_image_urls(self):
        image_urls = []
        for file in self.files or []:
            if file.get('mimetype', '').startswith('image/'):
                image_urls.append(file.get('url_private'))
        return image_urls



class ParallelSender:
    def __init__(self, event: SlackEvent):
        self.event = event
        self.tokens = []
        self.stop_event = threading.Event()
        self.replied_ts = None

    def add_token(self, token):
        self.tokens.append(token.content)

    def update_message_in_thread(self):
        return executor.submit(self.thread_update_message)

    def thread_update_message(self):
        while True:
            # no token to reply -> wait
            # completed -> update finally and break the loop

            completed = self.stop_event.is_set()

            if self.tokens:
                message = "".join(self.tokens)

                if self.replied_ts is None:
                    self.replied_ts = send_message(message, self.event.channel, self.event.ts)["ts"]
                else:
                    update_message(message, self.event.channel, self.replied_ts)
            else:
                time.sleep(0.5)

            if completed:
                break

    def __enter__(self):
        self.future = self.update_message_in_thread()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        self.future.result()



def send_message(text, channel, thread_ts):
    response = client.chat_postMessage(
        channel=channel,
        text=text,
        thread_ts=thread_ts
    )
    return response


def update_message(text, channel, ts):
    response = client.chat_update(
        channel=channel,
        ts=ts,
        text=text
    )
    return response


@memoize
def get_bot_name():
    return get_user_real_name(get_bot_user_id())


@memoize
def get_bot_user_id():
    response = client.auth_test()
    return response["user_id"]


@memoize
def get_user_real_name(user_id):
    response = client.users_info(user=user_id)
    real_name = response["user"]["profile"]["real_name"]
    return real_name


def download_and_encode_image(url):
    headers = {"Authorization": f"Bearer {slack_bot_token}"}
    response = requests.get(url, headers=headers)
    if url.lower().endswith((".jpg", ".jpeg")):
        mime_type = "image/jpeg"
    elif url.lower().endswith(".png"):
        mime_type = "image/png"
    else:
        mime_type = "image/unknown"
    return f"data:{mime_type};base64,{base64.b64encode(response.content).decode('utf-8')}"


def start():
    SocketModeHandler(app, slack_app_token).start()