
def get_user_system_prompt(user_id):
    # todo manage by database
    if user_id == "UA2TKHJPN":
        return """
        - 답변은 특별한 요청이 없으면, 한국어로 해주세요.
        - 개발자이고, 주로 python을 사용합니다.
        - 추가적인 언급없이 유튜브 링크만 제공되면, 핵심내용을 요약한 후에, 각 차례 별로 구체적으로 자세히 설명해주고, 제목 및 내용을 토대로 시청자가 궁금할 만한 질문 3개와 그 답변을 자세히 제공해주세요.
        """
    else:
        return None

def get_channel_system_prompt(channel_id):
    return None
