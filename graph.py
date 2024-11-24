from typing import Literal

from langchain_core.messages import AIMessage, ToolMessage, RemoveMessage

from llm import *
from prompt import *
from tools import *
from util.slack import SlackEvent

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
    for tool_call in message.tool_calls:
        tool_message = f"Executing {tool_call['name']}"
        event.reply_file(tool_message, content=get_tool_func_text(tool_call))


def send_tool_approval_message(message, event):
    func_texts = [get_tool_func_text(tool_call) for tool_call in message.tool_calls]
    joiner = "\n=========\n"
    tool_message = f"Do you want to execute the below? ```{joiner.join(func_texts)}```"
    event.reply_button_message(tool_message, "Yes", "tool_approved")


def get_tool_func_text(tool_call):
    tool_name = tool_call['name']
    formatted_args = ", ".join([f"{key}='{value}'" for key, value in tool_call['args'].items()])
    return f"{tool_name}({formatted_args})"


def should_fallback(state: State) -> Literal["llm_mini", "remove_failed_tool_call_attempt"]:
    messages = state["messages"]
    # todo 몇번 시도해보고 안되면 하게 하기
    # todo 모든 에러에서 작동하는게 아닌 것 같음. error여부가 일관적이지 않은 것 같고, error여부를 어떻게 판단할지, AI보고 판단하게 할지. 고민해서 개선하는게 좋을 것 같음
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
    graph_builder.add_node("tools", ToolNode(tools=tools))
    graph_builder.add_node("tools_approval", ToolNode(tools=tools))
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


llm_mini_with_tools = llm_mini.bind_tools(tools)
llm_better_with_tools = llm_better.bind_tools(tools)
memory = MemorySaver()
graph = create_graph()
