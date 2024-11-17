from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel

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
    if "edited" in event:
        # for conversation's consistency. not allow to answer on edited message.
        return

    stream = chain.stream(event)
    observe_stream(stream, event)


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


def conversation_prompt(event):
    """
    if thread messages exist more than limit,
    first message is the thread's first message.
    other messages are the latest messages order by date asc (last message is the latest message)

    todo delete last message in the conversation if it's same with the event.
    """
    thread_ts = event.get("thread_ts")
    if thread_ts is None:
        return []

    conversation = slack.client.conversations_replies(channel=event["channel"], ts=thread_ts, limit=conversation_count_limit)["messages"]
    messages = convert_conversation_to_messages(conversation)
    return messages


def question_prompt(event):
    message = HumanMessage(role=slack.get_user_real_name(event["user"]), content=event["text"] or empty_content)

    images = slack.get_encoded_images(event)
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
