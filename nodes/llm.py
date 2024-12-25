from langchain_openai import ChatOpenAI


def get_model_openai(model_name):
    return ChatOpenAI(temperature=0.1,  # 창의성 (0.0 ~ 2.0)
                      max_tokens=2048,  # 최대 토큰수
                      model_name=model_name)  # 모델명


llm_mini = get_model_openai("gpt-4o-mini")
llm_better = get_model_openai("gpt-4o")
