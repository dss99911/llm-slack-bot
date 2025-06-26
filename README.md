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
- **Database**: The application now uses SQLite. The Python `sqlite3` library is part of the standard library, so no separate driver installation via pip is typically needed for it. The system-level `sqlite3` tools are installed via the Dockerfile if running in Docker. The database will be automatically created as a file at `db/app.db`. No external database server setup is required.
- Install other dependencies as specified (e.g., in the Dockerfile or a requirements.txt if provided for local setup outside Docker).
- Create a Slack app and add proper permissions.
- Set the `.env` file by referring to `.env_sample`. Note that PostgreSQL-specific environment variables (like `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`) are no longer required as the application has been migrated to SQLite.

## Slack configuration
[slack-config](slack-config.md)

## Run
```shell
python chatbot.py
```

## Deploy to server
configure `deploy/config.sh` and run the below
this requires docker and docker-compose on the server.
tested on ec2 server

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
