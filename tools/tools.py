import logging

from youtube_transcript_api import YouTubeTranscriptApi
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool

from nodes.llm import llm_mini
from tools.retriever_tool import *
from tools.slack_tool import *
from users.permission import *
from utils.image import download_and_encode_image

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
def fetch_youtube_transcript(video_id: str) -> str:
    """ fetch youtube transcript by video id
    :param video_id: https://www.youtube.com/watch?v={video_id}
    """

    transcripts = YouTubeTranscriptApi().list(video_id)

    res = [transcript.fetch() for transcript in transcripts][0]
    res = "\n".join([s.text for s in res.snippets])
    return res


@tool
def ask_image_url(question: str, image_url: str, quality=25) -> str:
    """
     Processes a question related to an image on the url and returns the response using a language model.

    :param question: question for the image
    :param image_url: image url
    :param quality: compression quality. if no mention, use default value
    :return: answer text from language model
    """

    image_data = download_and_encode_image(image_url, compress_quality=quality)
    res = llm_mini.invoke([HumanMessage(make_image_content(question, image_data))])
    return res.content


def get_tools(permission):
    tools = []
    if permission >= PERMISSION_USE:
        tools.extend(filter(None, [
            search_tool,
            retrieve_data_tool,
            get_slack_thread_conversation,
            get_slack_channel_conversation,
            use_better_llm,
            python_tool,
            send_slack_dm,
            fetch_youtube_transcript
        ]))

    return tools

tools_approval = []
