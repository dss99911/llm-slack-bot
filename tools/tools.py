import logging

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool
from pytube import YouTube

from nodes.llm import llm_mini
from tools.retriever_tool import *
from tools.slack_tool import *
from users.permission import *
from utils.image import download_and_encode_image
from utils.tor import TOR_PROXY_URL, move_to_next_exit_node

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
def fetch_youtube_info(video_id: str) -> dict:
    """ fetch youtube info, transcript by video id

    :param video_id: https://www.youtube.com/watch?v={video_id}
    :return: title, description, publish_date, thumbnail_url, transcripts (list of transcript start time seconds and text. ex) [('15s', "abc"), ('20s', "def")])
    """

    for i in range(5):
        try:
            move_to_next_exit_node()
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}", proxies={
                "https": TOR_PROXY_URL,
                "http": TOR_PROXY_URL,
            })

            transcripts = [(f'{int(item["start"])}s', item["text"]) for item in yt.caption_tracks[0].captions]
            return {
                "title": yt.title,
                "description": yt.description,
                "publish_date": yt.publish_date.strftime("%Y-%m-%d"),
                "thumbnail_url": yt.thumbnail_url,
                "transcripts": transcripts
            }
        except Exception:
            logging.exception("fetch_youtube_info exception")
            try:
                move_to_next_exit_node()
            except:
                logging.exception("move_to_next_exit_node")

    raise Exception("Failed to fetch youtube info")


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
            fetch_youtube_info
        ]))

    return tools

tools_approval = []
