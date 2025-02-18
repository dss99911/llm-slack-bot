import threading

from module import chatbot, api, youtube_feed


def main():
    functions = [chatbot.run, api.run, youtube_feed.run]
    threads = [threading.Thread(target=f, daemon=True) for f in functions]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()