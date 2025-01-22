from flask import Flask, request, jsonify

from chatbot import handle_event
from utils.imports import *

API_TOKEN = os.environ.get("API_TOKEN")

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/ask_ai", methods=["POST"])
def ask():
    auth()

    question = get_question()
    user_id = "UA2TKHJPN"
    res = slack.send_message(question, user_id)

    thread = threading.Thread(target=answer, args=(question, user_id, res['channel'], res['ts']))
    thread.start()

    return jsonify({"status": "success"}), 200


def auth():
    # 인증 확인
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized, Bearer token is missing"}), 401

    # Bearer 토큰 값 확인
    bearer_token = auth_header.split(" ")[1]
    if bearer_token != API_TOKEN:
        return jsonify({"error": "Unauthorized, Invalid token"}), 403


def get_question():
    # 요청 본문 확인
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Bad Request, question is missing"}), 400

    return data["question"]


def run():
    app.run(debug=not prod, host='0.0.0.0', port=5001)


def answer(question, user_id, channel, ts):
    handle_event({
        'channel': channel, 'ts': ts,
        'user': user_id,
        'text': question
    })
