import threading

from module import chatbot, api, youtube_feed


def main():
    chatbot_thread = threading.Thread(target=chatbot.run, daemon=True)
    api_thread = threading.Thread(target=api.run, daemon=True)

    chatbot_thread.start()
    api_thread.start()
    youtube_feed.run()

    chatbot_thread.join()
    api_thread.join()


if __name__ == '__main__':
    main()