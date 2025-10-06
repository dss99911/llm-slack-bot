FROM --platform=linux/arm64 python:3.11-slim-bookworm As build

RUN echo "Acquire::http::Pipeline-Depth 0;" > /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::http::No-Cache true;" >> /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::BrokenProxy    true;" >> /etc/apt/apt.conf.d/99custom

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip3 install -U pip
RUN pip3 install --no-cache-dir slack_bolt \
    langchain langchain_community langchain_experimental langchain-openai langgraph faiss-cpu \
    pandas requests[socks] Pillow flask stem \
    psycopg2-binary sqlalchemy feedparser schedule

RUN pip3 install --no-cache-dir youtube_transcript_api

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/code:${PATH}"
COPY src /opt/code/
WORKDIR /opt/code
CMD ["python", "main.py"]