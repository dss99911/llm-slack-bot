from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from utils.imports import *

empty_content = "[empty message]"


@tool
def get_slack_thread_conversation(channel, ts, thread_ts, conversation_limit=slack.conversation_count_limit) -> List[str]:
    """
    fetch slack thread conversation by the slack link.
    If there is the slack link on human's last message, this tool should be invoked. and add the conversation to the message.
    If there is no slack link on last message, DO NOT invoke the tool

    slack link format is like https://{company_name}.slack.com/archives/{channel}/p{ts}?thread_ts={thread_ts}&cid={channel}
    If there is no information of channel, ts on the link, DO NOT invoke the tool

    :param conversation_limit: If human request the specific limit of the conversation messages, fetch that count of conversation. If it's not mentioned, fetch 50 messages
    :return: slack messages
    """

    # todo consider to use prompt instead of tool.
    #         tool을 쓰면, llm 을 한번 더 호출해서 그렇긴 한데, 더 명시적으로 스레드 대화 내용을 가져와서, AI가 이해하는게 더 수월
    #         prompt를 쓰면서도, 명시적으로 이게 현재 대화내용과 다른 스레드의 대화 내용이라는 걸 명시할 수 있는 방법이 있으면, prompt에서 하기
    thread_ts = thread_ts or ts
    if "." not in thread_ts:
        thread_ts = thread_ts[:-6] + '.' + thread_ts[-6:]
    conversation = slack.get_thread_conversation(channel, thread_ts, conversation_limit)
    messages = convert_conversation_to_messages(conversation, True)
    return [message.content for message in messages]


@tool
def get_slack_channel_conversation(channel_id, limit=slack.conversation_count_limit) -> List[str]:
    """
    If there is the channel id on human's last message,
    fetch slack channel conversation by the channel id.
    channel id on the message: <#{channel_id}|> ex: <#G01JXSCR0SE|>
    :param limit: if human mention the limit of conversation, use the limit otherwise, use default limit
    :return: slack messages
    """
    conversation = slack.get_channel_conversation(channel_id, limit)
    messages = convert_conversation_to_messages(conversation, True)
    return [message.content for message in messages]


@tool
def send_slack_dm(user_name_groups:List[List[str]], requester: str, message: str):
    """Send Slack direct messages to multiple user groups.

    :param user_name_groups: List of user groups. Each group is represented as a list of user IDs or usernames.
              Example: [['jack', 'john'], ['smith', 'kevin']]
              The function will send a DM to each group separately (e.g., one DM to ['jack', 'john'] and another DM to ['smith', 'kevin']).
    :param requester: the person who requested
    :param message: The Slack message to be sent. This should be a string containing the message content.
    """
    message = f"Sent by: <@{requester}>\n\n{message}"
    for user_name_group in user_name_groups:
        user_id_group = list(map(slack.get_user_id, user_name_group))
        slack.send_dm(user_id_group, message)
    return "success"


def convert_conversation_to_messages(conversation, include_bot_message=False) -> List[BaseMessage]:
    messages = []
    for message in conversation:
        event = SlackEvent(message)
        content = slack_content(event.user_name, event)

        if event.is_the_bot():
            if not include_bot_message:
                continue  # bot answer already saved. so, no need to get. and also, doesn't know id, so, not easy to replace
            message = AIMessage(content=content, id=message["ts"])
        else:
            # if the message already exists, update the existing message
            message = HumanMessage(content=content, id=message["ts"])

        messages.append(message)
    return messages



def make_image_content(content, *image_data):
    if not image_data:
        return content
    content = [
        content,
        *[image_content(image) for image in image_data]
    ]
    return content


def slack_content(user_name, event):
    content = event.text or slack.empty_content
    content = slack.convert_user_id_to_name(content)
    if event.is_the_bot():
        return content
    else:
        return f"{user_name}: {content}"


def image_content(image):
    return {
        "type": "image_url",
        "image_url": {"url": f"{image}"},
    }
