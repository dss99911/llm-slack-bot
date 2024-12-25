# LLM Slack Chat Bot


## Functions
- Agentic work flow by Langgraph
- RAG for the company doc and database metadata
- Short-term Context Retention
- Multi modal (image, text only for now)
- use OpenAI model or Bedrock model
- permission for each user
- custom prompt for each user


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

### app-level token
- add token with the scope `connections:write`
### Socket mode
- Enable Socket Mode


### App Home
Always Show My Bot as Online
- Enable
Messages Tab
- Allow users to send Slash commands and messages from the messages tab

### Interactivity & Shortcuts
add shortcuts

### OAuth & Permissions
Bot Token Scopes
```
app_mentions:read
channels:history
channels:read
chat:write
commands
files:read
files:write
groups:history
groups:read
im:history
im:read
im:write
mpim:read
mpim:history
mpim:write
team:read
users:read
users:read.email
```


### Event Subscriptions
- Enable Events
- Subscribe to bot events
```
app_mentions
message.channels
message.groups
message.im
```

## Run
```shell
python chatbot.py
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
