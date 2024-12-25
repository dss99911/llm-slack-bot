from utils.imports import *
from nodes.llm import llm_mini
from utils.slack import slack_bot_token, slack_app_token
from users.permission import get_user_permission, PERMISSION_NO
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from graph import stream_graph

app = App(token=slack_bot_token)


@app.event("app_mention")
def handle_app_mention_events(event):
    handle_event(event)


@app.event("message")
def handle_message_events(event):
    if SlackEvent(event).is_direct_message():
        handle_event(event)


@app.action("tool_approved")
def handle_tool_approved(ack, body):
    ack()
    event = slack.action_body_to_event(body, approved=True)
    handle_event(event)


@app.shortcut("summary")
def shortcut_summary(ack, body):
    question = "Just summarize the conclusion shortly"
    event = slack.action_body_to_event(body, shortcut=True)
    handle_shortcut(ack, event, question)


@app.shortcut("translate_to_english")
def shortcut_translate_to_english(ack, body):
    ack()
    event = slack.action_body_to_event(body, shortcut=True)
    try:
        event = SlackEvent(event)

        question = f"translate the following message to english with no explanation:\n{event.text}"
        res = llm_mini.invoke(question).content
    except Exception as e:
        res = str(e)
        pass
    event.reply_ephemeral_message(res)


@app.shortcut("ask")  # Callback ID와 매칭
def shortcut_show_ask_modal(ack, body, client):
    ack()
    event = slack.action_body_to_event(body, shortcut=True)
    client.views_open(trigger_id=body["trigger_id"],
                      view={"type": "modal",
                            "callback_id": "ask_modal",
                            "title": {"type": "plain_text", "text": "Ask about the thread"},
                            "submit": {"type": "plain_text", "text": "Ask"},
                            "close": {"type": "plain_text", "text": "Cancel"},
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


@app.view("ask_modal")
def shortcut_ask(ack, body):
    question = body["view"]["state"]["values"]["input"]["input_action"]["value"]
    event = json.loads(body["view"]["private_metadata"])
    handle_shortcut(ack, event, question)


def handle_shortcut(ack, event, question):
    ack()
    event["text"] = question
    handle_event(event)


def handle_event(event):
    """
    handle event and deliver to langchain graph
    :param event: event to check
    :return:
    """
    slack_event = SlackEvent(event)
    logging.info(f"user: {slack_event.user_name}")

    try:
        if get_user_permission(slack_event.user) == PERMISSION_NO:
            return

        if slack_event.is_edited():
            return  # for conversation's consistency. not allow to answer on edited message.

        input = {"event": event} if not slack_event.approved else None
        thread_id = slack_event.thread_ts
        if slack_event.shortcut:
            thread_id += f"_{slack_event.user}"
        stream = stream_graph(input, thread_id=thread_id)
        slack_event.reply_stream(stream)
    except Exception as e:
        slack_event.reply_message(f"Error occurred: {e}")
        logging.exception(e)


if __name__ == '__main__':
    SocketModeHandler(app, slack_app_token).start()
