from nodes.llm import *
from nodes.prompt import *
from tools.tools import *

from langchain_core.messages import ToolMessage, RemoveMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages


class State(MessagesState):
    event: dict
    better_llm: bool


def generate_prompt(state: State):
    event = SlackEvent(state["event"])

    messages = []

    messages = add_messages(messages, system_prompt(event))

    messages = add_messages(messages, conversation_prompt(event))
    messages = add_messages(messages, question_prompt(event))

    return {"messages": messages}


def call_llm_mini(state: State):
    return call_llm(state, False)


def call_llm_better(state: State):
    return call_llm(state, True)


def call_llm_fallback(state: State):
    return call_llm_better(state)


def call_llm(state: State, better):
    slack_event = SlackEvent(state["event"])
    permission = get_user_permission(slack_event.user)
    llm = get_llm(better, permission, slack_event.shortcut)
    return {"messages": [llm.invoke(state["messages"])]}


def route_tools(state: State) -> Literal["tools", "tools_approval", "__end__"]:
    message = state["messages"][-1]
    event = SlackEvent(state["event"])
    if not isinstance(message, AIMessage) or not message.tool_calls:
        return "__end__"

    if is_tool_approval_required(message):
        send_tool_approval_message(message, event)
        return "tools_approval"
    else:
        send_tool_message(message, event)
        return "tools"


def is_tool_approval_required(message):
    for tool_call in message.tool_calls:
        if tool_call['name'] in {t.name for t in tools_approval}:
            return True
    return False


def send_tool_message(message, event):
    for tool_call in message.tool_calls:
        tool_message = f"Executing {tool_call['name']}"
        logging.info(tool_message)


def send_tool_approval_message(message, event):
    func_texts = [get_tool_func_text(tool_call) for tool_call in message.tool_calls]
    joiner = "\n=========\n"
    tool_message = f"Do you want to execute the below? ```{joiner.join(func_texts)}```"
    event.reply_button_message(tool_message, "Yes", "tool_approved")


def get_tool_func_text(tool_call):
    tool_name = tool_call['name']
    formatted_args = ", ".join([f"{key}='{value}'" for key, value in tool_call['args'].items()])
    return f"{tool_name}({formatted_args})"


def should_fallback(state: State) -> Literal["llm_mini", "llm_fallback"]:
    messages = state["messages"]
    # todo 몇번 시도해보고 안되면 하게 하기
    # todo 모든 에러에서 작동하는게 아닌 것 같음. error여부가 일관적이지 않은 것 같고, error여부를 어떻게 판단할지, AI보고 판단하게 할지. 고민해서 개선하는게 좋을 것 같음
    last_message = messages[-1]

    if isinstance(last_message, ToolMessage):
        is_error = last_message.status == "error"
        is_error |= last_message.additional_kwargs.get("error") is not None
        is_error |=  last_message.name == 'Search' and "HTTPError('400 Client Error" in last_message.content
        is_error |= not last_message.content
        if is_error:
            return "llm_fallback"

    if state.get("better_llm"):
        # todo consider to go back to llm_mini after few trial
        return "llm_fallback"
    return "llm_mini"


def create_graph(checkpointer):
    graph_builder = StateGraph(State)
    graph_builder.add_node("prompt", generate_prompt)
    graph_builder.add_node("llm_mini", call_llm_mini)
    graph_builder.add_node("llm_fallback", call_llm_fallback)
    graph_builder.add_node("tools", ToolNode(tools=get_tools(PERMISSION_ALL)))
    graph_builder.add_node("tools_approval", ToolNode(tools=get_tools(PERMISSION_ALL)))  # include tools_without_permission because multiple tools can be invoked at one time

    graph_builder.add_edge(START, "prompt")
    graph_builder.add_edge("prompt", "llm_mini")
    graph_builder.add_conditional_edges("llm_mini", route_tools)
    graph_builder.add_conditional_edges("tools", should_fallback)
    graph_builder.add_conditional_edges("tools_approval", should_fallback)
    graph_builder.add_conditional_edges("llm_fallback", route_tools)

    graph = graph_builder.compile(checkpointer=checkpointer, interrupt_before=["tools_approval"])
    return graph


def stream_graph(input: Optional[dict], thread_id):
    config = {"configurable": {"thread_id": thread_id, "recursion_limit": 10}}
    if input:
        state = graph.get_state(config).values
        if messages := state.get("messages"):
            last_message = messages[-1]
            if isinstance(last_message, AIMessage) and last_message.tool_calls:
                graph.update_state(config=config, values={"messages": [RemoveMessage(id=last_message.id)]})

    stream = graph.stream(input, config, stream_mode="messages")
    return filtered_stream(stream)


def filtered_stream(stream):
    for item in stream:
        # todo 여기서 tool execution 하는 것들도 나오지 않나? approval message나, execution 메시지 여기서 한번 가공하고, chatbot.py에 출력하는게 더 깔끔할 듯.
        if item[1]['langgraph_node'] not in ['llm_mini', 'llm_fallback']:
            continue
        if content := item[0].content:
            # todo pydantic이나 typed dict같은거 써보기
            if isinstance(content, list):  # sonnet
                for c in content:
                    if isinstance(c, dict):
                        if text := c.get('text'):
                            yield text
            else:
                yield content


def visualize_graph(graph):
    from IPython.display import Image, display
    display(Image(graph.get_graph().draw_mermaid_png()))


@memoize
def get_llm(better, permission, shortcut):
    llm = llm_better if better else llm_mini

    if shortcut:
        return llm

    return llm.bind_tools(get_tools(permission))

memory = MemorySaver()
graph = create_graph(memory)
