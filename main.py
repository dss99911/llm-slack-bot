import threading

from module import chatbot, api, youtube_feed
from utils.slack import env


def main():
    if env == "dev":
        functions = [chatbot.run, api.run, youtube_feed.run]
    else:
        functions = [chatbot.run]
    threads = [threading.Thread(target=f, daemon=True) for f in functions]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()