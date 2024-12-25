FROM --platform=linux/amd64 python:3.11-slim-bookworm As build

COPY requirements.txt .
RUN pip3 install -U pip
RUN pip3 install --no-cache-dir -r requirements.txt

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/bin/pip3 /usr/bin/pip

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/code:${PATH}"
COPY . /opt/code/
WORKDIR /opt/code
CMD ["python", "chatbot.py"]