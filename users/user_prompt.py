
def get_user_system_prompt(user_id):
    # todo manage by database
    if user_id == "UA2TKHJPN":
        return """
        - 답변은 특별한 요청이 없으면, 한국어로 해주세요.
        - 개발자이고, 주로 python을 사용합니다.
        - 추가적인 언급없이 유튜브 링크만 제공되면, 명시적으로 목차, 중요내용 요약, 결론을 각각 나눠서 말해주고, 목차는 <https://www.youtube.com/watch?v={video_id}&t={seconds}s|목차 내용> 형태로 작성해주세요.
        """
    else:
        return None

def get_channel_system_prompt(channel_id):
    return None
