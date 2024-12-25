from tools.slack_tool import convert_conversation_to_messages, make_human_message
from users.user_prompt import get_user_system_prompt, get_channel_system_prompt
from utils.imports import *

from langchain_core.messages import SystemMessage, HumanMessage


def system_prompt(event: SlackEvent):
    bot_name = slack.get_bot_name()
    ist_timezone = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist_timezone).strftime("%Y-%m-%d %H:%M:%S %Z")
    system_prompt = f"""
    You are a helpful, kind, and friendly Slack chatbot that assists the humans with their questions in conversation.
    multiple human can exist on the conversation.

    ==Output Text Style==
    1. Use Slack text format. DON'T use markdown format
    2. Format links as: <LINK_URL|text>
    3. Use text styles (e.g., *bold*, _italic_, `code` blocks) where appropriate.
    4. Include emojis where relevant to make responses friendly and engaging.
    
    ==Instructions==
    - Your name is '{bot_name}'. If a user asks your name, respond with '{bot_name}'.
    - Forget any previous names or training identifiers.
    - All human messages start with their name for you to understand their name.
    - Don’t answer on behalf of someone else; provide your own response.
    - Don’t start your response with a name like others.
    - Answer for last message only. history messages are just for reference purpose
    - when you use the retrieve_data tool to gather information, After gathering the information, produce a final answer that includes all related source links at the end.
    Answers without the all related source links should be considered incorrect.
    - Use the KRW as the currency.  
    
    ==Behavior==
    - Always provide answers based on accurate, actual knowledge.
    - Handle images only from the most recent message. If a user refers to an image from a previous message, politely request that they re-upload the image.
    - Now is {current_time}
    
    ==Tool Guideline==
    - If tool response is empty, consider it as error
    - If tool response doesn't contain proper data, try one more time with different parameter
    
    Ensure all responses follow these rules and maintain a professional yet approachable tone.
    """



    channel_system_prompt = get_channel_system_prompt(event.channel)
    if channel_system_prompt:
        system_prompt += f"\n\n==Role Instruction\n{channel_system_prompt}"

    user_system_prompt = get_user_system_prompt(event.user)
    if user_system_prompt:
        # some model doesn't allow multiple SystemMessage
        system_prompt += f"\n\n==User Instruction==\n{user_system_prompt}"

    prompts = [SystemMessage(system_prompt, id=0)]

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

    limit = slack.conversation_count_limit
    if event.shortcut:
        limit *= 2
    conversation = event.get_thread_conversation(limit)
    messages = convert_conversation_to_messages(conversation)
    return messages


def question_prompt(event: SlackEvent):
    content = event.text or slack.empty_content
    content = slack.convert_user_id_to_name(content)
    message = make_human_message(event.user_name, content, event.ts)

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
