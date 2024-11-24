from langchain_core.messages import SystemMessage, HumanMessage

from config import empty_content
from util.slack.functions import SlackEvent
from util.slack import functions as slack
import re


def system_prompt(event: SlackEvent):
    bot_name = slack.get_bot_name()
    system_prompt = f"""
    You are a helpful, kind, and friendly Slack chatbot that assists the company employees with their questions.

    ==Output Text Style==
    1. Use Slack text format. DON'T use markdown format
    2. Format links as: <LINK_URL|text>
    3. Use text styles (e.g., *bold*, _italic_, `code` blocks) where appropriate.
    4. Include emojis where relevant to make responses friendly and engaging.
    
    ==Instructions==
    - Your name is '{bot_name}'. If a user asks your name, respond with '{bot_name}'.
    - Forget any previous names or training identifiers.
    
    ==Behavior==
    - Always provide answers based on accurate, actual knowledge.
    - If the requested knowledge does not exist, simply state: "I do not have knowledge about that."
    - Handle images only from the most recent message. If a user refers to an image from a previous message, politely request that they re-upload the image.
    
    Ensure all responses follow these rules and maintain a professional yet approachable tone.
    """
    prompts = [SystemMessage(system_prompt)]

    return prompts


def conversation_prompt(event: SlackEvent):
    """
    if thread messages exist more than limit,
    first message is the thread's first message.
    other messages are the latest messages order by date asc (last message is the latest message)
    """

    if not event.is_in_thread():
        # if it's first message in thread, there are no history messages
        return []

    if event.is_direct_message():
        # as all messages are saved, no need to get conversation
        return []

    conversation = event.get_thread_conversation()
    messages = convert_conversation_to_messages(conversation)
    return messages


def convert_conversation_to_messages(conversation):
    messages = []
    for message in conversation:
        if "user" in message:
            user_name = slack.get_user_name(message["user"])
        else:
            user_name = message["username"] # the bot case

        content = message["text"] or empty_content
        content = convert_user_id_to_name(content)

        if user_name == slack.get_bot_name():
            continue  # bot answer already saved. so, no need to get
        else:
            # if the message already exists, update the existing message
            message = HumanMessage(content=f"{user_name}: {content}", id=message["ts"])

        messages.append(message)
    return messages


def question_prompt(event: SlackEvent):
    content = event.text or empty_content
    content = convert_user_id_to_name(content)
    message = HumanMessage(role=event.user_name, content=f"{event.user_name}: {content}", id=event.ts)

    images = event.get_encoded_images()
    if images:
        message.content = [
            message.content,
            *[{
                "type": "image_url",
                "image_url": {"url": f"{image}"},
            } for image in images]
        ]
    return [message]


def get_personalized_prompt(user_id):
    # todo manage by database
    if user_id == "U09DPGC0P":
        return [SystemMessage("""
        답변은 항상 한국어로 해주세요.
        개발자이고, 주로 python을 사용합니다.
        """)]
    else:
        return []


def convert_user_id_to_name(content):
    user_ids = re.findall(r"<@([A-Z0-9]+)>", content)

    for user_id in user_ids:
        user_name = slack.get_user_name(user_id)
        content = content.replace(f"<@{user_id}>", f"@{user_name}")

    return content