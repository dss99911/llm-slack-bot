import db
from utils.common import memoize


@memoize
def get_user_system_prompt(slack_id):
    return db.select_one(db.Prompt, db.Prompt.slack_id == slack_id)
#     if user_id == "UA2TKHJPN":
#         return """
# - 답변은 특별한 요청이 없으면, 한국어로 해주세요.
# - 개발자이고, 주로 python을 사용합니다.
# - 추가적인 언급없이 유튜브 링크만 제공되면, 다음 포맷으로 정리해 주세요.
# 영상 내용은 구조적으로, 논리적으로 정리해 주세요.
# 답변 시, *강조*, `코드 블럭`, > blockquote, Numbered List, Bulleted List, '   ' Indent, imoji 등을 충분히 사용하요, 가독성을 높여주세요.
#
# ## 🔹 구조적 정리 (Structure)
# - '   ' indent를 통한 트리 구조로 내용을 아래와 같이 보기좋게 구조화해서 정리해주세요.
#
# *대제목1*
# • 소제목1
#    • 요약 설명1 (최소 3줄 길이로 요약)
#    • 요약 설명2
# • 소제목2
#
# *대제목2*
# *대제목3*
# ...
#
# ## 🔹 3줄 요약 (TL;DR)
# - 핵심 포인트를 *키워드 중심*으로 3줄 이내로 요약해 주세요.
#
# ## 🔹 인사이트 (Insights)
# - 요약에 없는 *중요해보이는 인사이트 3가지*를 간결하게 정리해 주세요. (각 1줄)
#
# ## 🔹 투자 관점 분석 (Investment Angle)
# - 앞으로 예상되는 미래변화를 논리적으로 설명해주세요
# - *투자에 미치는 영향*을 알려주세요
# - *위험요소(Risks)* 3가지
# - *기회요소(Opportunities)* 3가지
#
# ## 🔹 Q&A
# - *청중이 가질 수 있는 질문 3가지*를 제시하고,
# - *각 답변은 300자 이상으로 깊이 있게 설명*해 주세요.
# """
#     else:
#         return None


def get_channel_system_prompt(channel_id):
    return db.select_one(db.Prompt, db.Prompt.channel_id == channel_id)
