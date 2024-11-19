import json
import logging

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel

from config import *
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from util.slack import functions as slack
from util.slack.functions import SlackEvent


@slack.app.event("app_mention")
def handle_app_mention_events(event):
    handle_message(event)


@slack.app.event("message")
def handle_message_events(event):
    if event.get("channel_type") == "im":
        handle_message(event)


@slack.app.shortcut("summary")
def shortcut_summary(ack, body):
    question = "Summarize the thread"
    event = shortcut_body_to_event(body)
    handle_shortcut(ack, event, question)


@slack.app.shortcut("ask")  # Callback ID와 매칭
def shortcut_ask(ack, body, client):
    ack()
    event = shortcut_body_to_event(body)
    client.views_open(trigger_id=body["trigger_id"],
                      view={"type": "modal",
                            "callback_id": "ask_modal",
                            "title": {"type": "plain_text", "text": "Ask about the thread"},
                            "submit": {"type": "plain_text", "text": "Ask"},  # 제출 버튼 추가
                            "close": {"type": "plain_text", "text": "Cancel"},  # 취소 버튼 (선택 사항)
                            "private_metadata": json.dumps(event),
                            "blocks": [{
                                "type": "input",
                                "block_id": "input",
                                "element": {
                                    "type": "plain_text_input",
                                    "action_id": "input_action",
                                    "placeholder": {"type": "plain_text", "text": "Input your question"}
                                },
                                "label": {"type": "plain_text", "text": "Ask"}}]})


@slack.app.view("ask_modal")
def handle_ask_modal(ack, body):
    question = body["view"]["state"]["values"]["input"]["input_action"]["value"]
    event = json.loads(body["view"]["private_metadata"])
    handle_shortcut(ack, event, question)


def handle_shortcut(ack, event, question):
    ack()
    event["text"] = question
    handle_message(event, f"<{event['url']}|{question}>\n")


def shortcut_body_to_event(body):
    event = {}
    event["channel"] = body["channel"]["id"]
    event["user"] = body["user"]["id"]
    event["ts"] = body["message_ts"]
    event["thread_ts"] = body["message"].get("thread_ts")
    event["shortcut"] = True
    event["url"] = get_shortcut_message_url(body)
    return event


def get_shortcut_message_url(body):
    domain = body["team"]["domain"]
    channel_id = body["channel"]["id"]
    ts = body["message_ts"]
    ts_int = ts.replace(".", "")
    thread_ts = body["message"].get("thread_ts") or ts

    return f"https://{domain}.slack.com/archives/{channel_id}/p{ts_int}?thread_ts={thread_ts}&cid={channel_id}"


def handle_message(event, prefix=None):
    event = SlackEvent(event)

    if event.is_edited():
        return  # for conversation's consistency. not allow to answer on edited message.

    try:
        stream = chain.stream(event)
        event.reply_stream(stream, prefix)
    except Exception as e:
        event.reply_message(f"Error occurred: {e}")
        logging.exception(e)


def make_chain():
    combined = RunnableParallel(system=system_prompt, conversation=conversation_prompt, question=question_prompt)
    chat_prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="system"),
        MessagesPlaceholder(variable_name="conversation"),
        MessagesPlaceholder(variable_name="question")
    ])

    return combined | chat_prompt | llm


def system_prompt(input):
    bot_name = slack.get_bot_name()
    system_prompt = f"""
        you have to forget your name when you are trained.
        Now, Your name is '{bot_name}' when human ask your name, answer '{bot_name}'.
        
        You are an assistant to answer based on actual knowledge instead of creating creative story. 
        If you don't have the knowledge, just tell that the knowledge not exists.
        
        you can get image only on last message. if the user ask about the image on previous message, ask the user to upload the image again.
        """

    return [SystemMessage(system_prompt)]


def conversation_prompt(event: SlackEvent):
    """
    if thread messages exist more than limit,
    first message is the thread's first message.
    other messages are the latest messages order by date asc (last message is the latest message)

    todo delete last message in the conversation if it's same with the event.
    """

    if not event.is_in_thread():
        return []

    conversation = event.get_thread_conversation()
    messages = convert_conversation_to_messages(conversation)
    return messages


def question_prompt(event: SlackEvent):
    message = HumanMessage(role=event.user_name, content=event.text or empty_content)

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


def convert_conversation_to_messages(conversation):
    messages = []
    for message in conversation:
        if "user" in message:
            user_name = slack.get_user_real_name(message["user"])
        else:
            # the bot case
            user_name = message["username"]

        text = message["text"]

        if user_name == slack.get_bot_name():
            message = AIMessage(text)
        else:
            message = HumanMessage(role=user_name, content=text or empty_content)

        messages.append(message)
    return messages


if __name__ == '__main__':
    chain = make_chain()
    slack.start()
