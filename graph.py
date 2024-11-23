from typing import Literal, Optional

from langchain_core.messages import AIMessage, ToolMessage, RemoveMessage

from config import *
from prompt import *
from tool.ApprovalTool import sql_executor, sql_generator
from tools import *
from util.slack.functions import SlackEvent

from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages


class State(MessagesState):
    event: dict


def generate_prompt(state: State):
    event = SlackEvent(state["event"])

    messages = []

    if len(state["messages"]) == 0:
        messages = add_messages(messages, system_prompt(event))
        if event.is_direct_message():
            messages = add_messages(messages, get_personalized_prompt(event.user))

    messages = add_messages(messages, conversation_prompt(event))
    messages = add_messages(messages, question_prompt(event))

    return {"messages": messages}


def call_llm_mini(state: State):
    return {"messages": [llm_mini_with_tools.invoke(state["messages"])]}


def call_llm_better(state: State):
    return {"messages": [llm_better_with_tools.invoke(state["messages"])]}


def call_llm_fallback(state: State):
    return call_llm_better(state)


def remove_failed_tool_call_attempt(state: MessagesState):
    messages = state["messages"]
    # Remove all messages from the most recent
    # instance of AIMessage onwards.
    last_ai_message_index = next(
        i
        for i, msg in reversed(list(enumerate(messages)))
        if isinstance(msg, AIMessage)
    )
    messages_to_remove = messages[last_ai_message_index:]
    return {"messages": [RemoveMessage(id=m.id) for m in messages_to_remove]}


def route_tools(state: State) -> Literal["tools", "tools_approval", "__end__"]:
    message = state["messages"][-1]
    event = SlackEvent(state["event"])
    if not isinstance(message, AIMessage) or not message.tool_calls:
        return "__end__"

    if is_tool_approval_required(message):
        send_tool_approval_message(message, event)
        return  "tools_approval"
    else:
        send_tool_message(message, event)
        return "tools"


def is_tool_approval_required(message):
    for tool_call in message.tool_calls:
        if tool_call['name'] in tool_names_approval:
            return True
    return False


def send_tool_message(message, event):
    tool_message = f"Executing ```{','.join(get_tool_messages(message))}```"
    event.reply_message(tool_message)


def send_tool_approval_message(message, event):
    tool_message = f"Do you want to execute the below? ```{','.join(get_tool_messages(message))}```"
    event.reply_button_message(tool_message, "Yes", "tool_approved")


def get_tool_messages(message):
    tool_messages = []
    for tool_call in message.tool_calls:
        tool_name = tool_call['name']
        formatted_args = ", ".join([f"{key}='{value}'" for key, value in tool_call['args'].items()])
        tool_messages.append(f"{tool_name}({formatted_args})")
    return tool_messages


def should_fallback(state: State) -> Literal["llm_mini", "remove_failed_tool_call_attempt"]:
    messages = state["messages"]
    # todo 몇번 시도해보고 안되면 하게 하기
    failed_tool_messages = [
        msg
        for msg in messages
        if isinstance(msg, ToolMessage)
           and (msg.additional_kwargs.get("error") is not None or
                (msg.name == 'Search' and "HTTPError('400 Client Error" in msg.content)) # TavilySearchResults error
    ]
    if failed_tool_messages:
        return "remove_failed_tool_call_attempt"
    return "llm_mini"


def create_graph():
    graph_builder = StateGraph(State)
    graph_builder.add_node("prompt", generate_prompt)
    graph_builder.add_node("llm_mini", call_llm_mini)
    graph_builder.add_node("llm_fallback", call_llm_fallback)

    graph_builder.add_node("tools", tool_node)
    graph_builder.add_node("tools_approval", tool_node_approval)
    graph_builder.add_node("remove_failed_tool_call_attempt", remove_failed_tool_call_attempt)

    graph_builder.add_edge(START, "prompt")
    graph_builder.add_edge("prompt", "llm_mini")
    graph_builder.add_conditional_edges("llm_mini", route_tools)
    graph_builder.add_conditional_edges("tools", should_fallback)
    graph_builder.add_conditional_edges("tools_approval", should_fallback)
    graph_builder.add_edge("remove_failed_tool_call_attempt", "llm_fallback")
    graph_builder.add_conditional_edges("llm_fallback", route_tools)

    graph = graph_builder.compile(checkpointer=memory, interrupt_before=["tools_approval"])
    return graph


def stream_graph(event: Optional[dict], thread_id):
    config = {"configurable": {"thread_id": thread_id}}

    if event:
        state = graph.get_state(config).values
        if messages := state.get("messages"):
            last_message = messages[-1]
            if isinstance(last_message, AIMessage) and last_message.tool_calls:
                graph.update_state(config=config, values={"messages": [RemoveMessage(id=last_message.id)]})

    stream = graph.stream({"event": event} if event else None, config, stream_mode="messages")
    return filtered_stream(stream)

def filtered_stream(stream):
    for item in stream:
        if item[1]['langgraph_node'] not in ['llm_mini', 'llm_fallback']:
            continue
        if content := item[0].content:
            yield content


def visualize_graph(graph):
    from IPython.display import Image, display
    display(Image(graph.get_graph().draw_mermaid_png()))



tools = [search_tool, python_tool, sql_generator, sql_executor]
tool_node = ToolNode(tools=tools)

tool_node_approval = ToolNode(tools=tools)
tool_names_approval = [sql_executor.name]
llm_mini_with_tools = llm_mini.bind_tools(tools)
llm_better_with_tools = llm_better.bind_tools(tools)
memory = MemorySaver()
graph = create_graph()