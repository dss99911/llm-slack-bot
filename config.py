from dotenv import load_dotenv
load_dotenv()

from llm import bedrock
from llm import openai


# llm = bedrock.get_model(
#     # "meta.llama3-8b-instruct-v1:0",
#     "anthropic.claude-3-sonnet-20240229-v1:0",
#     model_parameter={"temperature": 0.0,
#                      "top_p": .9})

llm = openai.get_model()

conversation_count_limit = 30
empty_content = "[empty message]"
