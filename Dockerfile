FROM --platform=linux/amd64 python:3.11-slim-bookworm As build

RUN echo "Acquire::http::Pipeline-Depth 0;" > /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::http::No-Cache true;" >> /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::BrokenProxy    true;" >> /etc/apt/apt.conf.d/99custom

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install -U pip
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/dss99911/pytube@dd0183e60485bb79cf558dc3090e13390c3c1f74

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/code:${PATH}"
COPY . /opt/code/
WORKDIR /opt/code
CMD ["python", "main.py"]