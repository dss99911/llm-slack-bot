import base64
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, SystemMessage
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from util.aws import bedrock
from util.common import memoize

load_dotenv()
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]
slack_app_token = os.environ["SLACK_APP_TOKEN"]

# Initializes your app with your bot token and socket mode handler
app = App(token=slack_bot_token)
client = app.client

llm = bedrock.get_model(
    # "meta.llama3-8b-instruct-v1:0",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    model_parameter={"temperature": 0.0,
                     "top_p": .9})

executor = ThreadPoolExecutor(max_workers=20)


@app.event("app_mention")
def handle_app_mention_events(event):
    handle_message(event)


@app.event("message")
def handle_message_events(event):
    if event.get("channel_type") == "im":
        handle_message(event)


def handle_message(event):
    messages = get_conversation_messages(event)
    stream = answer(messages)
    observe_stream(stream, event)


def get_conversation_messages(event):
    """
    if thread messages exist more than limit,
    first message is the thread's first message.
    other messages are the latest messages order by date asc (last message is the latest message)
    """
    thread_ts = event.get("thread_ts")
    if thread_ts is None:
        messages = [HumanMessage(role=get_user_real_name(event["user"]), content=event["text"])]
    else:
        conversation = client.conversations_replies(channel=event["channel"], ts=thread_ts, limit=30)["messages"]
        messages = convert_conversation_to_messages(conversation)

    for message in messages:
        if not message.content:
            message.content = "[empty message]"

    images = get_encoded_images(event)
    if images:
        last_message = messages[-1]
        last_message.content = [
            last_message.content,
            *[{
                "type": "image_url",
                "image_url": {"url": f"{image}"},
            } for image in images]
        ]
    return messages


def answer(messages):
    system_prompt = """
    Your name is 'Aya'.
    You are an assistant to answer based on actual knowledge instead of creating creative story. 
    If you don't have the knowledge, just tell that the knowledge not exists.
    you can get image only on last message. if the user ask about the image on previous message, ask the user to upload the image again.
    """
    return llm.stream([SystemMessage(system_prompt), *messages])


def observe_stream(stream, event):
    tokens = []
    stop_event = threading.Event()

    future = update_message_in_thread(tokens, stop_event, event)

    try:
        for token in stream:
            tokens.append(token.content)
    finally:
        stop_event.set()
        future.result()


@memoize
def get_bot_user_id():
    response = client.auth_test()
    return response["user_id"]


def get_encoded_images(event):
    image_urls = extract_image_urls(event)
    base64_images = []
    for url in image_urls:
        base64_data = download_and_encode_image(url, slack_bot_token)
        if base64_data:
            base64_images.append(base64_data)
    return base64_images


@memoize
def get_user_real_name(user_id):
    response = app.client.users_info(user=user_id)
    real_name = response["user"]["profile"]["real_name"]
    return real_name


def send_message(text, channel, thread_ts):
    response = app.client.chat_postMessage(
        channel=channel,
        text=text,
        thread_ts=thread_ts
    )
    return response


def update_message(text, channel, ts):
    response = app.client.chat_update(
        channel=channel,
        ts=ts,
        text=text
    )
    return response


def update_message_in_thread(tokens, stop_event, event):
    return executor.submit(thread_update_message, tokens, stop_event, event)


def thread_update_message(tokens, stop_event, event):
    replied_ts = None

    channel = event["channel"]
    event_ts = event["ts"]

    while True:
        # no token to reply -> wait
        # completed -> update finally and break the loop

        completed = stop_event.is_set()

        if tokens:
            message = "".join(tokens)

            if replied_ts is None:
                replied_ts = send_message(message, channel, event_ts)["ts"]
            else:
                update_message(message, channel, replied_ts)
        else:
            time.sleep(0.5)

        if completed:
            break


def convert_conversation_to_messages(history) -> List[BaseMessage]:
    messages = []
    for message in history:
        user_id = message["user"]
        text = message["text"]

        if user_id == get_bot_user_id():
            message = AIMessage(text)
        else:
            user_name = get_user_real_name(user_id)
            message = HumanMessage(role=user_name, content=text)

        messages.append(message)
    return messages


def extract_image_urls(event):
    image_urls = []
    for file in event.get('files') or []:
        if file.get('mimetype', '').startswith('image/'):
            image_urls.append(file.get('url_private'))
    return image_urls


def download_and_encode_image(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if url.lower().endswith((".jpg", ".jpeg")):
        mime_type = "image/jpeg"
    elif url.lower().endswith(".png"):
        mime_type = "image/png"
    else:
        mime_type = "image/unknown"
    return f"data:{mime_type};base64,{base64.b64encode(response.content).decode('utf-8')}"


if __name__ == '__main__':
    SocketModeHandler(app, slack_app_token).start()
