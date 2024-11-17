from config import *
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from util.slack import functions as slack


@slack.app.event("app_mention")
def handle_app_mention_events(event):
    handle_message(event)


@slack.app.event("message")
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
        messages = [HumanMessage(role=slack.get_user_real_name(event["user"]), content=event["text"])]
    else:
        conversation = slack.client.conversations_replies(channel=event["channel"], ts=thread_ts, limit=30)["messages"]
        messages = convert_conversation_to_messages(conversation)

    for message in messages:
        if not message.content:
            message.content = "[empty message]"

    images = slack.get_encoded_images(event)
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
    Your name is 'Aya' if human ask your name, answer 'Aya'.
    You are an assistant to answer based on actual knowledge instead of creating creative story. 
    If you don't have the knowledge, just tell that the knowledge not exists.
    you can get image only on last message. if the user ask about the image on previous message, ask the user to upload the image again.
    """
    return llm.stream([SystemMessage(system_prompt), *messages])


def observe_stream(stream, event):
    with slack.ParallelSender(event) as sender:
        for token in stream:
            sender.add_token(token)


def convert_conversation_to_messages(conversation):
    messages = []
    for message in conversation:
        user_id = message["user"]
        text = message["text"]

        if user_id == slack.get_bot_user_id():
            message = AIMessage(text)
        else:
            user_name = slack.get_user_real_name(user_id)
            message = HumanMessage(role=user_name, content=text)

        messages.append(message)
    return messages


if __name__ == '__main__':
    slack.start()
