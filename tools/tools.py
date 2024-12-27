from typing import Union
from youtube_transcript_api import YouTubeTranscriptApi

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool

from tools.retriever_tool import *
from tools.slack_tool import *
from users.permission import *

python_tool = PythonREPLTool()
python_tool.description = (
    "A Python shell. Use this to execute Python commands. "
    "Input should be a valid Python command. "
    "Always use `print(...)` to display outputs explicitly, even if the "
    "value would normally be returned or displayed. For example, instead of "
    "`x` or `x + 1`, use `print(x)` or `print(x + 1)`."
)
search_tool = TavilySearchResults(name="Search", max_results=2)


@tool
def use_better_llm(state: Annotated[dict, InjectedState]):
    """ call this tool to use better LLM model
    Use this tool when:
    - the human tell answer is not correct
    - the human ask to use better model
    """
    state["better_llm"] = True
    # todo need to save on memory if multiple process run at the same time
    return "Activated better LLM"


@tool
def fetch_youtube_script(video_id: str) -> List[Tuple[float, str]]:
    """ fetch youtube script by video id

    :param video_id: https://www.youtube.com/watch?v={video_id}
    :return: list of transcript start time seconds and text. ex) [(15, "abc"), (20, "def")]
    """
    def fetch():
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id, proxies={
            "https": "socks5://torproxy:9050",
            "http": "socks5://torproxy:9050",
        })

        transcripts = [transcript.fetch() for transcript in transcripts][0]
        transcripts = [(f'{item["start"]}s', item["text"]) for item in transcripts]
        return transcripts

    return retry_action(fetch, 3)


def get_tools(permission):
    tools = []
    if permission >= PERMISSION_USE:
        tools.extend(filter(None, [
            search_tool,
            retrieve_data_tool,
            show_image_tool,
            get_slack_thread_conversation,
            get_slack_channel_conversation,
            use_better_llm,
            python_tool,
            send_slack_dm,
            fetch_youtube_script
        ]))

    return tools

tools_approval = []
