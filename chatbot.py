import json
import logging

from graph import stream_graph
from permission import get_user_permission, PERMISSION_NO
from util.slack import functions as slack
from util.slack.functions import SlackEvent


@slack.app.event("app_mention")
def handle_app_mention_events(event):
    handle_message(event)


@slack.app.event("message")
def handle_message_events(event):
    if SlackEvent(event).is_direct_message():
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
    slack_event = SlackEvent(event)

    if get_user_permission(slack_event.user) == PERMISSION_NO:
        return

    if slack_event.is_edited():
        return  # for conversation's consistency. not allow to answer on edited message.
    try:
        stream = stream_graph(event, slack_event.thread_ts)
        slack_event.reply_stream(stream, prefix)
    except Exception as e:
        slack_event.reply_message(f"Error occurred: {e}")
        logging.exception(e)


if __name__ == '__main__':

    slack.start()
