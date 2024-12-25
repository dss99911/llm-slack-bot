from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from utils.imports import *

empty_content = "[empty message]"


@tool
def show_image_tool(image_path, summary, state: Annotated[dict, InjectedState]):
    """this tool read image file and show the image to the user
    basically, if user want to see graph, use python_tool to save graph, and show the graph by this tool
    :param image_path: image file path
    :param summary: image summary
    """
    # todo 그래프를 보여달라고 하면, 이걸 호출하지 않음. 이 작동방식이 이미지를 저장하고, 저장된 이미지 경로를 통해서 이미지를 보여주는 형식이라서,
    #       AI가 이 tool을 사용할 생각을 못하는 것 같음
    #       그래프를 보여줘라고 했을 때, 보여준다는 행위가 슬랙에 이미지를 업로드 한다는 개념으로 받아들여져야 함
    #       고려사항
    #           - AI가 base64 인코딩을 출력하게 하고, stream을 읽어올 때, base64 인코딩 데이터면, 데이터가 다 나올 때까지 token을 읽다가,
    #           이미지가 다 나왔으면, 이미지 파일로 저장해서 slack에 이미지 보내기
    #               - 단점( messages에 크기가 큰 이미지가 누적되니, AI에 질문할 때마다, 해당 이미지도 같이 전달되고, 토큰 비용이 비싸짐)
    #                   -> 비용이 문제라면, 과거 히스토리 대화 내용을 보낼 때, 이미지는 제외할 수도 있음
    #               - 장점( AI가 출력된 이미지를 이해해서, 그래프가 잘못 나왔거나 했을 때, 정정 요청하기 쉬움)
    #           - 그래프를 보여주는 tool을 만들고, 해당 tool의 param에 python코드를 입력 받고, 해당 코드에 이미지 파일이나, base64 인코딩 출력하는 코드를 추가로 넣기
    #               - 장점(그래프를 보여준다는 행위가 직관적으로 tool로 정의가 되므로, AI가 쉽게 인식함)
    #               - 단점(구현 복잡도? 코드 추가하는게 잘 작동 하게 prompt를 작성하는게 중요.)
    #                   - 그래프를 보여준다는 행위는 그래프를 만든다와 본다는 행위가 합쳐진 것인데,
    #                   단순히 그래프만을 목적으로 tool을 만들기 보다는, 그래프를 만든다와 본다는 행위를 각각 정의 하는게 범용성이 더 커보이긴 함.

    SlackEvent(state["event"]).reply_file(summary, image_path)
    return "completed"


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
        if "user" in message:
            user_name = slack.get_user_name(message["user"])
        else:
            user_name = message["username"]  # the bot case

        content = message["text"] or empty_content
        content = slack.convert_user_id_to_name(content)

        if user_name == slack.get_bot_name():
            if not include_bot_message:
                continue  # bot answer already saved. so, no need to get. and also, doesn't know id, so, not easy to replace
            message = AIMessage(content=content, id=message["ts"])
        else:
            # if the message already exists, update the existing message
            message = make_human_message(user_name, content, message["ts"])

        messages.append(message)
    return messages


def make_human_message(user_name, content, ts):
    return HumanMessage(content=f"{user_name}: {content}", id=ts)