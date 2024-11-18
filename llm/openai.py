from langchain_openai import ChatOpenAI


def get_model():
    return ChatOpenAI(
        temperature=0.1,  # 창의성 (0.0 ~ 2.0)
        max_tokens=2048,  # 최대 토큰수
        model_name="gpt-4o-mini",  # 모델명
    )