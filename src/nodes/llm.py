from langchain_openai import ChatOpenAI
from utils.imports import *

def get_model_openai(model_name):
    return ChatOpenAI(temperature=0.1,  # 창의성 (0.0 ~ 2.0)
                      max_tokens=2048,  # 최대 토큰수
                      model_name=model_name)  # 모델명


llm_mini = get_model_openai("gpt-4o-mini")
llm_better = get_model_openai("gpt-4o")


# from langchain_openai import ChatOpenAI
# from utils.imports import *
#
# def get_model_openai(model_name):
#     return ChatOpenAI(max_tokens=2048,  # 최대 토큰수
#                       model_name=model_name)  # 모델명
#
#
# def get_gpt5(model_name="gpt-5-nano"):
#     return ChatOpenAI(
#         model="gpt-5-nano",
#         temperature=0.1,
#         max_tokens=1024,
#         model_kwargs={
#             "reasoning_effort": "minimal",
#             "verbosity": "low"
#         }
#     )
#
#
# llm_mini = get_gpt5("gpt-5-nano")
# llm_better = get_gpt5("gpt-5-mini")
