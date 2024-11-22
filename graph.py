from config import *
from prompt import *
from tools import *
from util.slack.functions import SlackEvent

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages


class State(MessagesState):
    event: dict


tools = [search_tool]
llm_with_tools = llm.bind_tools(tools)
memory = MemorySaver()


def prompt(state: State):
    event = SlackEvent(state["event"])  # TypeError: Object of type SlackEvent is not serializable

    messages = []

    if len(state["messages"]) == 0:
        messages = add_messages(messages, system_prompt(event))
        if event.is_direct_message():
            messages = add_messages(messages, get_personalized_prompt(event.user))

    messages = add_messages(messages, conversation_prompt(event))
    messages = add_messages(messages, question_prompt(event))


    return {"messages": messages}


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


def create_graph():
    graph_builder = StateGraph(State)
    graph_builder.add_node("prompt", prompt)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", ToolNode(tools=tools))

    graph_builder.add_edge(START, "prompt")
    graph_builder.add_edge("prompt", "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition, {"tools": "tools", END: END})
    graph_builder.add_edge("tools", "chatbot")

    graph = graph_builder.compile(checkpointer=memory)
    return graph


graph = create_graph()

def stream_graph(event: dict, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    stream = graph.stream({"event": event}, config, stream_mode="messages")
    return filtered_stream(stream)

def filtered_stream(stream):
    for item in stream:
        if item[1]['langgraph_node'] != 'chatbot':
            continue
        if content := item[0].content:
            yield content


def visualize_graph(graph):
    from IPython.display import Image, display
    display(Image(graph.get_graph().draw_mermaid_png()))