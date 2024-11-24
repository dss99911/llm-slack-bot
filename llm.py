from imports import *

from langchain_aws import ChatBedrock
from langchain_openai import ChatOpenAI


def get_bedrock_client(runtime: Optional[bool] = True):
    """
    runtime :
        Optional choice of getting different client to perform operations with the Amazon Bedrock service.
    """
    if runtime:
        service_name='bedrock-runtime'
    else:
        service_name='bedrock'
    bedrock_client = boto3.client(service_name, region_name=aws_region_name)
    return bedrock_client


def get_model_bedrock(model_id, model_parameter):
    llm = ChatBedrock(model_id=model_id,
                      model_kwargs=model_parameter,
                      client=get_bedrock_client())
    return llm


def get_model_openai(model_name):
    return ChatOpenAI(temperature=0.1,  # 창의성 (0.0 ~ 2.0)
                      max_tokens=2048,  # 최대 토큰수
                      model_name=model_name)  # 모델명

# todo sonnet 성능이 너무 안좋은 듯.. 적절한 tool을 사용 못함
# llm_mini = get_model_bedrock(
#     # "meta.llama3-8b-instruct-v1:0",
#     "anthropic.claude-3-sonnet-20240229-v1:0",
#     model_parameter={"temperature": 0.0,
#                      "top_p": .9})

llm_mini = get_model_openai("gpt-4o-mini")
llm_better = get_model_openai("gpt-4o")

