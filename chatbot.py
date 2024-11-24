from graph import stream_graph
from imports import *
from permission import get_user_permission, PERMISSION_NO


@slack.app.event("app_mention")
def handle_app_mention_events(event):
    handle_event(event, event)


@slack.app.event("message")
def handle_message_events(event):
    if SlackEvent(event).is_direct_message():
        handle_event(event, event)


@slack.app.action("tool_approved")
def handle_tool_approved(ack, body):
    print(body)
    ack()
    handle_event(action_body_to_event(body), None)


def action_body_to_event(body):
    return {"channel": body["channel"]["id"],
            "user": body["user"]["id"],
            "ts": body["message"]["ts"],
            "thread_ts": body["message"].get("thread_ts")}


def handle_event(event, input):
    """
    handle event and deliver to langchain graph
    :param event: event to check
    :param input: input to langchain graph if the flow is interrupted and resume again, set None
    :return:
    """
    print(event)
    slack_event = SlackEvent(event)

    try:
        if get_user_permission(slack_event.user) == PERMISSION_NO:
            return

        if slack_event.is_edited():
            return  # for conversation's consistency. not allow to answer on edited message.

        stream = stream_graph(input, slack_event.thread_ts)
        slack_event.reply_stream(stream)
    except Exception as e:
        slack_event.reply_message(f"Error occurred: {e}")
        logging.exception(e)


if __name__ == '__main__':
    slack.start()
