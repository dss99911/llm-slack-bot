import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from typing import List, Tuple
import re
from slack_sdk import WebClient
from typing import TypedDict
from utils.common import memoize

from dotenv import load_dotenv

from utils.image import download_and_encode_image

load_dotenv()

conversation_count_limit = 50

slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_app_token = os.environ["SLACK_APP_TOKEN"]

client = WebClient(token=slack_bot_token)
executor = ThreadPoolExecutor(max_workers=20)

empty_content = "[empty message]"


class SlackUserProfile(TypedDict):
    title: str
    phone: str
    email: str


class SlackUser(TypedDict):
    id: str
    team_id: str
    name: str
    real_name: str
    tz: str
    profile: SlackUserProfile



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
        """
        used for
        - thread id of history
        - send slack message
        """
        return self.event.get("thread_ts") or self.ts

    @property
    def message_ts(self):
        return self.event.get("message_ts")

    @property
    def user(self):
        return self.event.get("user")

    @property
    def user_name(self):
        return get_user_name(self.user) if self.user else self.event.get("username")

    @property
    def text(self):
        return self.event.get("text")

    @property
    def files(self):
        return self.event.get("files")

    @property
    def elements(self) -> list:
        return self.event.get("elements")

    @property
    def subtype(self):
        return self.event.get("subtype")

    @property
    def approved(self) -> bool:
        return "approved" in self.event and self.event["approved"]

    @property
    def shortcut(self) -> list:
        return "shortcut" in self.event and self.event["shortcut"]

    def get_links(self):
        return [e.get("url") for e in self.elements or [] if e.get("type") == "link" and e.get("url")]

    def get_slack_link_channel_thread_ts(self) -> List[Tuple[str, str]]:
        return list(filter(lambda l: l is not None, map(extract_slack_link, self.get_links())))

    def get_slack_channel_in_text(self):
        return [e.get("channel_id") for e in self.elements or [] if e.get("type") == "channel" and e.get("channel_id")]

    def is_direct_message(self):
        return self.channel_type == "im"

    def is_visible_for_user_only(self):
        return self.is_direct_message() or self.shortcut

    def is_edited(self):
        return (self.edited is not None) or (self.subtype == "message_changed")

    def is_in_thread(self):
        return self.event.get("thread_ts") is not None

    def is_the_bot(self):
        return self.user_name == get_bot_name()

    def reply_message(self, message):
        executor.submit(partial(send_message, message, channel=self.channel, thread_ts=self.thread_ts))

    def reply_stream(self, stream):
        reply_tokens = []

        if self.shortcut:
            for token in stream:
                reply_tokens.append(token)
            # can't update ephemeral_message, so, wait until all tokens are collected
            self.reply_ephemeral_message(markdown_to_slack("".join(reply_tokens)))
        else:
            stop_event = threading.Event()
            future = executor.submit(partial(self._loop_update_message, reply_tokens, stop_event))
            try:
                for token in stream:
                    reply_tokens.append(token)
            finally:
                stop_event.set()
                future.result()

    def reply_button_message(self, message, button_text, action_id):
        # todo allow only the user who request,
        # todo after click, delete it
        # can't use ephemeral_message because, difficult to see if the message is start of the thread, user won't know there is the ephemeral_message.
        return send_message([
            {"type": "section",
             "text": {"type": "mrkdwn", "text": message},
             "accessory": {"type": "button",
                           "action_id": action_id,
                           "text": {"type": "plain_text", "text": button_text}}}
        ], self.channel, self.thread_ts)

    def reply_file(self, text, file_path=None, content=None):
        return upload_file(self.channel, self.thread_ts, text, file_path, content)

    def reply_ephemeral_message(self, text_or_block):
        key = "blocks" if isinstance(text_or_block, list) else "text"
        return client.chat_postEphemeral(
            **{"channel": self.channel,
               "thread_ts": self.thread_ts,
               "user": self.user,
               key: text_or_block}
        )

    def get_thread_conversation(self, limit=conversation_count_limit):
        return client.conversations_replies(channel=self.channel, ts=self.thread_ts, limit=limit)["messages"]

    def get_encoded_images(self):
        image_urls = self._extract_image_urls()
        base64_images = []
        headers = {"Authorization": f"Bearer {slack_bot_token}"}
        for url in image_urls:
            base64_data = download_and_encode_image(url, headers)
            if base64_data:
                base64_images.append(base64_data)
        return base64_images

    def _loop_update_message(self, reply_tokens, stop_event):
        message_replied = ""
        reply_ts = None
        reply_channel = None

        while True:
            completed = stop_event.is_set()
            message = markdown_to_slack("".join(reply_tokens))
            if message == message_replied:
                # if no token added or not yet added new token after the message sent
                time.sleep(0.3)
            else:
                if reply_ts is None:
                    response = send_message(message, channel=self.channel, thread_ts=self.thread_ts)
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


def send_message(text_or_block, channel, thread_ts=None):
    params = {"channel": channel}

    if isinstance(text_or_block, list):
        params["blocks"] = text_or_block
        params["text"] = "empty"
    else:
        params["text"] = text_or_block

    if thread_ts:
        params["thread_ts"] = thread_ts

    return client.chat_postMessage(**params)


def update_message(text, channel, ts):
    response = client.chat_update(channel=channel, ts=ts, text=text)
    return response


@memoize
def get_bot_name():
    return get_user_name(get_bot_user_id())


def get_bot_user_id():
    response = client.auth_test()
    return response["user_id"]


@memoize
def get_user_name(user_id):
    response = client.users_info(user=user_id)
    real_name = response["user"]["name"]
    return real_name


def upload_file(channel_id, thread_ts, message, file_path, content=None):
    """
    :param content: create file based on text. only one of file_path or content can be used.
    :return:
    """
    response = client.files_upload_v2(
        channels=channel_id,
        thread_ts=thread_ts,
        file=file_path,
        content=content,
        initial_comment=message
    )
    if not response.get("ok"):
        raise Exception(f"Failed to upload image: {response}")
    return response


def get_thread_conversation(channel, thread_ts, limit=conversation_count_limit):
    return client.conversations_replies(channel=channel, ts=thread_ts, limit=limit)["messages"]


def get_channel_conversation(channel, limit):
    return client.conversations_history(channel=channel, limit=limit).data["messages"]


def extract_slack_link(url):
    prefix = "https://balancehero.slack.com/archives/"
    if not url.startswith(prefix):
        return None

    pattern = rf"{prefix}([^/]+)/p(\d+)(?:\?thread_ts=(\d+\.\d+))?"
    match = re.match(pattern, url)
    if match:
        channel = match.group(1)
        ts = match.group(2)
        thread_ts = match.group(3) or ts
        if "." not in thread_ts:
            thread_ts = thread_ts[:-6] + '.' + thread_ts[-6:]

        return channel, thread_ts
    else:
        return None


def action_body_to_event(body, shortcut=False, approved=False):
    return {"channel": body["channel"]["id"],
            "user": body["user"]["id"],
            "ts": body.get("action_ts") if shortcut
            else body["actions"][0]["action_ts"], # button click case
            "thread_ts": body["message"].get("thread_ts") or body["message"].get("ts") if shortcut
            else body["container"]["thread_ts"], # button click case
            "text": body.get("message", {}).get("text"),
            "shortcut": shortcut,
            "approved": approved}


def markdown_to_slack(text):
    # Bold (**text** -> *text*)
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    # Hyperlinks ([text](url) -> <url|text>)
    text = re.sub(r'\[(.*?)]\((.*?)\)', r'<\2|\1>', text)
    # Unordered lists (- item -> • item)
    text = re.sub(r'^\s*-\s+', '• ', text, flags=re.MULTILINE)
    return text

def convert_user_id_to_name(text):
    user_ids = re.findall(r"<@([A-Z0-9]+)>", text)

    for user_id in user_ids:
        user_name = get_user_name(user_id)
        text = text.replace(f"<@{user_id}>", f"@{user_name}")

    return text


def send_dm(user_ids, text):
    # DM 채널 열기
    response = client.conversations_open(users=user_ids)
    channel_id = response["channel"]["id"]

    # 메시지 전송
    client.chat_postMessage(channel=channel_id, text=text)


@memoize
def fetch_all_users():
    all_users = {}
    next_cursor = None

    while True:
        # Slack API 호출
        response = client.users_list(limit=100, cursor=next_cursor)

        members = response["members"]
        for member in members:
            if member.get("deleted") or member.get("is_bot"):
                continue
            user: SlackUser = member
            all_users[user["name"]] = user

        # 다음 페이지 확인
        next_cursor = response.get("response_metadata", {}).get("next_cursor")
        if not next_cursor:  # 더 이상 페이지가 없으면 종료
            break

    return all_users


def get_user(user_name):
    return fetch_all_users().get(user_name)


def get_user_id(user_name):
    return get_user(user_name).get("id")

