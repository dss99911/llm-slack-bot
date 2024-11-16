# LLM Slack Chat Bot


## Functions

- Short-term Context Retention
- Multi modal (image, text only for now)
- use BedRock model, secret from AWS

### Plan

- RAG
- Search function
- Action
- Agent flow
- 
## Usage
1. ask the bot on DM or by tagging the bot
2. whenever LLM model create next token, it's updated on the answer message in realtime
3. if you ask again on the thread of the slack message, chatbot keep the short-term context
4. attach image if you want to ask about the image


## Reference
- [Langchain-kr](https://github.com/teddylee777/langchain-kr)
- [amazon-bedrock-aistylist-lab](https://github.com/aws-samples/amazon-bedrock-aistylist-lab)
- [Slack Bolt for Python](https://tools.slack.dev/bolt-python/getting-started/)
