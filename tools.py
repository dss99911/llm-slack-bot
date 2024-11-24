from imports import *

from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool
from langchain.tools.retriever import create_retriever_tool
from langgraph.prebuilt import InjectedState

from prompt import convert_conversation_to_messages
from retriever import get_metadata_retriever, get_company_retriever


python_tool = PythonREPLTool()

search_tool = TavilySearchResults(name="Search", max_results=2)

retrieve_company_tool = create_retriever_tool(
    get_company_retriever(),
    "retrieve_company",
    "search and return information about the company policy, welfare, insurance, roadmap, core value, glossary",
)

retrieve_metadata_tool = create_retriever_tool(
    get_metadata_retriever(),
    "retrieve_metadata",
    "this tool searches database metadata and return the schema with json format"
    "CALL this tool before the task to run sql or to generate sql ",
)

@tool
def read_and_save_temp_data_by_sql(sql) -> dict:
    """ call Athena read sql query and save to local file path with parquet type.

    must call retrieve_metadata tool before calling this tool.

    if you need to utilize the output data, after calling this tool, read it by python tool and use it.

    you can see the column's dtype and 3 sample rows on return value.
    :return: {"column_dtypes": df.dtypes.tolist(), "file_path": 'some-path.parquet', "sample_rows": df.sample(3).to_numpy().tolist()}.
    """
    df: pd.DataFrame = wr.athena.read_sql_query(sql=sql, database="log", boto3_session=boto3.Session(region_name=aws_region_name))
    file_path = f"/tmp/{uuid.uuid4()}.parquet"
    df.to_parquet(file_path)

    return {"column_dtypes": df.dtypes.tolist(), "file_path": file_path, "sample_rows": df.sample(3).to_numpy().tolist()}



@tool
def show_image_tool(image_path, summary, state: Annotated[dict, InjectedState]):
    """this tool read image file and show the image to the user
    basically, if user want to see graph, use python_tool to save graph, and show the graph by this tool
    :param image_path: image file path
    :param summary: image summary
    """
    #todo 그래프를 보여달라고 하면, 이걸 호출하지 않음. 이 작동방식이 이미지를 저장하고, 저장된 이미지 경로를 통해서 이미지를 보여주는 형식이라서,
    #       AI가 이 tool을 사용할 생각을 못하는 것 같음
    #       그래프를 보여줘라고 했을 때, 보여준다는 행위가 슬랙에 이미지를 업로드 한다는 개념으로 받아들여져야 함
    #       고려사항
    #           - AI가 base64 인코딩을 출력하게 하고, stream을 읽어올 때, base64 인코딩 데이터면, 데이터가 다 나올 때까지 token을 읽다가,
    #           이미지가 다 나왔으면, 이미지 파일로 저장해서 slack에 이미지 보내기
    #               - 단점( messages에 크기가 큰 이미지가 누적되니, AI에 질문할 때마다, 해당 이미지도 같이 전달되고, 토큰 비용이 비싸짐)
    #                   -> 비용이 문제라면, 과거 히스토리 대화 내용을 보낼 때, 이미지는 제외할 수도 있음
    #               - 장점( AI가 출력된 이미지를 이해해서, 그래프가 잘못 나왔거나 했을 때, 정정 요청하기 쉬움)
    #           - 그래프를 보여주는 tool을 만들고, 해당 tool의 param에 python코드를 입력 받고, 해당 코드에 이미지 파일이나, base64 인코딩 출력하는 코드를 추가로 넣기
    #               - 장점(그래프를 보여준다는 행위가 직관적으로 tool로 정의가 되므로, AI가 쉽게 인식함)
    #               - 단점(구현 복잡도? 코드 추가하는게 잘 작동 하게 prompt를 작성하는게 중요.)
    #                   - 그래프를 보여준다는 행위는 그래프를 만든다와 본다는 행위가 합쳐진 것인데,
    #                   단순히 그래프만을 목적으로 tool을 만들기 보다는, 그래프를 만든다와 본다는 행위를 각각 정의 하는게 범용성이 더 커보이긴 함.


    SlackEvent(state["event"]).reply_file(summary, image_path)
    return "completed"
    # upload_image_file("@hyun", "image", image_path)


@tool
def get_slack_thread_conversation(slack_link_url, channel, ts, thread_ts):
    """
    fetch slack thread conversation by the slack link.
    If there is the slack link on user's message, this tool should be invoked. and add the conversation to the message

    slack link format is like https://{company_name}.slack.com/archives/{channel}/p{ts}?thread_ts={thread_ts}&cid={channel}
    so, other than slack link is received, this tool should not be invoked
    :return: slack message
    todo consider to use prompt instead of tool.
        tool을 쓰면, llm 을 한번 더 호출해서 그렇긴 한데, 더 명시적으로 스레드 대화 내용을 가져와서, AI가 이해하는게 더 수월
        prompt를 쓰면서도, 명시적으로 이게 현재 대화내용과 다른 스레드의 대화 내용이라는 걸 명시할 수 있는 방법이 있으면, prompt에서 하기
    """
    thread_ts = thread_ts or ts
    if "." not in thread_ts:
        thread_ts = thread_ts[:-6] + '.' + thread_ts[-6:]
    conversation = slack.get_thread_conversation(channel, thread_ts)
    return convert_conversation_to_messages(conversation, True)

tools = [search_tool, python_tool, retrieve_metadata_tool, retrieve_company_tool, read_and_save_temp_data_by_sql, show_image_tool, get_slack_thread_conversation]

tool_names_approval = [read_and_save_temp_data_by_sql.name]
