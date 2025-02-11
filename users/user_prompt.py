

def get_user_system_prompt(user_id):
    # todo manage by database
    if user_id == "UA2TKHJPN":
        return """
- 답변은 특별한 요청이 없으면, 한국어로 해주세요.
- 개발자이고, 주로 python을 사용합니다.
- 추가적인 언급없이 유튜브 링크만 제공되면, 아래와 같은 포맷으로 답변해주고, 중요 키워드는 * * 또는 ` ` 로 강조 표시해 주세요.
    - 3줄 요약.
    - 구조적 정리: 영상의 흐름을 이해 하기 쉽도록 주요 내용을 논리적 순서에 따라 정리 하세요. 단락의 내용은 500자 이상 자세히 설명)
    - 핵심 포인트 요약: 사용자가 기억 해야 할 핵심 포인트를 간결 하게 정리 하세요.
    - Q&A (제목과 관련된 3가지 질문을 만들고, 각 질문에 대해 답변을 300자 이상 제공)
        """
    else:
        return None


def get_channel_system_prompt(channel_id):
    return None
