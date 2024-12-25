# LLM Slack Chat Bot


## Functions
- Agentic work flow by Langgraph
- RAG for the personal data
- Short-term Context Retention
- Multi modal (image, text only for now)
- use OpenAI model
- permission for each user
- custom prompt for each user
- fetch youtube transcription by [Tor proxy](https://www.torproject.org/)



## Usage
1. ask the bot on DM or by tagging the bot
2. whenever LLM model create next token, it's updated on the answer message in realtime
3. if you ask again on the thread of the slack message, chatbot keep the short-term context
4. attach image if you want to ask about the image

## Requirements
- python3.11
- install requirements.txt
- create slack app and add proper permissions
- set `.env` file by referring to .env_sample

## Slack configuration
[slack-config](slack-config.md)

## Run
```shell
python chatbot.py
```

## Deploy to server
configure `deploy/config.sh` and run the below

```shell
cd deploy
sh deploy_server.sh
```

## Plan
- local chatbot for device automation
- personal AI assistant
- company chatbot (not updated here)
- RAG for source code. let user can decide scope like cursor IDE 


## Reference
- [Langchain-kr](https://github.com/teddylee777/langchain-kr)
- [amazon-bedrock-aistylist-lab](https://github.com/aws-samples/amazon-bedrock-aistylist-lab)
- [Slack Bolt for Python](https://tools.slack.dev/bolt-python/getting-started/)
- [Langchain](https://python.langchain.com/docs/introduction/)
