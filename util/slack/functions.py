import base64
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import requests
from attr import dataclass
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from config import conversation_count_limit
from util.common import memoize

slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_app_token = os.environ["SLACK_APP_TOKEN"]

app = App(token=slack_bot_token)
client = app.client

executor = ThreadPoolExecutor(max_workers=20)


@dataclass
class SlackEvent:
    event: dict

    @property
    def channel(self):
        return self.event["channel"]

    @property
    def channel_type(self):
        return self.event.get("channel_type")

    @property
    def ts(self):
        return self.event["ts"]

    @property
    def edited(self):
        return self.event.get("edited")

    @property
    def thread_ts(self):
        return self.event.get("thread_ts") or self.ts

    @property
    def user(self):
        return self.event["user"]

    @property
    def user_name(self):
        return get_user_name(self.user)

    @property
    def text(self):
        return self.event.get("text")

    @property
    def files(self):
        return self.event.get("files")

    def is_direct_message(self):
        return self.channel_type == "im"

    def is_edited(self):
        return self.edited is not None

    def is_in_thread(self):
        return self.event.get("thread_ts") is not None

    def reply_message(self, message):
        executor.submit(partial(send_message, message, channel=self.channel, thread_ts=self.ts))

    def reply_stream(self, stream):
        stop_event = threading.Event()
        reply_tokens = []
        future = executor.submit(partial(self._loop_update_message, reply_tokens, stop_event))
        try:
            for token in stream:
                reply_tokens.append(token)
        finally:
            stop_event.set()
            future.result()

    def reply_button_message(self, message, button_text, action_id):
        send_message([{"type": "section", "text": {"type": "mrkdwn", "text": message},
                              "accessory": {"type": "button", "action_id": action_id,
                                            "text": {"type": "plain_text", "text": button_text}}}],
                     channel=self.channel,
                     thread_ts=self.ts)

    def get_thread_conversation(self, limit=conversation_count_limit):
        return client.conversations_replies(channel=self.channel, ts=self.thread_ts, limit=limit)["messages"]

    def get_encoded_images(self):
        image_urls = self._extract_image_urls()
        base64_images = []
        for url in image_urls:
            base64_data = download_and_encode_image(url)
            if base64_data:
                base64_images.append(base64_data)
        return base64_images

    def _loop_update_message(self, reply_tokens, stop_event):
        message_replied = ""
        reply_ts = None
        reply_channel = None

        while True:
            completed = stop_event.is_set()

            message = "".join(reply_tokens)
            if message == message_replied:
                # if no token added or not yet added new token after the message sent
                time.sleep(0.3)
            else:
                if reply_ts is None:
                    response = send_message(message, channel=self.channel, thread_ts=self.ts)
                    reply_ts = response["ts"]
                    reply_channel = response["channel"]
                else:
                    update_message(message, reply_channel, reply_ts)
                message_replied = message

            if completed:
                # if completed, update finally and break the loop
                break

    def _extract_image_urls(self):
        image_urls = []
        for file in self.files or []:
            if file.get('mimetype', '').startswith('image/'):
                image_urls.append(file.get('url_private'))
        return image_urls


def send_message(text_or_block, channel, thread_ts):
    key = "blocks" if isinstance(text_or_block, list) else "text"

    response = client.chat_postMessage(**{"channel": channel,
                                          "thread_ts": thread_ts,
                                          key: text_or_block})
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
    return get_user_name(get_bot_user_id())


@memoize
def get_bot_user_id():
    response = client.auth_test()
    return response["user_id"]


@memoize
def get_user_name(user_id):
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
