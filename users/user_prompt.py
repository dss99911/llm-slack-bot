
def get_user_system_prompt(user_id):
    # todo manage by database
    if user_id == "U09DPGC0P":
        return """
        - 답변은 특별한 요청이 없으면, 한국어로 해주세요.
        - 개발자이고, 주로 python을 사용합니다.
        """
    else:
        return None


def get_channel_system_prompt(channel_id):
    return None
