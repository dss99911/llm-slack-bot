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


def handle_message(event):
    event = SlackEvent(event)

    if event.is_edited():
        return  # for conversation's consistency. not allow to answer on edited message.

    try:
        stream = chain.stream(event)
        observe_stream(stream, event)
    except Exception as e:
        event.reply_on_thread(f"Error occurred: {e}")
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
    system_prompt = f"""
        you have to forget your name when you are trained.
        Now, Your name is '{slack.get_bot_name()}' when human ask your name, answer '{slack.get_bot_name()}'.
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
            message = HumanMessage(role=user_name, content=text or empty_content)

        messages.append(message)
    return messages


if __name__ == '__main__':
    chain = make_chain()
    slack.start()
