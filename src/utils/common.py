import os
import shutil
import threading
import time
import traceback
from functools import wraps
from os.path import isdir

import time
from functools import wraps


def memoize(expiry_seconds=None):
    if callable(expiry_seconds):
        return memoize()(expiry_seconds)

    expiry_seconds = expiry_seconds or float('inf')

    def decorator(f):
        memo = {}
        timestamps = {}

        @wraps(f)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            # args와 kwargs를 조합하여 키 생성
            key = (args, frozenset(kwargs.items()))

            # 캐시 만료 확인 및 제거
            if key in memo:
                if current_time - timestamps[key] > expiry_seconds:
                    del memo[key]
                    del timestamps[key]

            # 새 값 계산 및 저장
            if key not in memo:
                memo[key] = f(*args, **kwargs)
                timestamps[key] = current_time

            return memo[key]

        return wrapper

    return decorator


def remove_path(file_path):
    if isdir(file_path):
        shutil.rmtree(file_path)
    else:
        os.remove(file_path)


def retry_action(action, count=10):
    """
    Retries a specified action up to a given number of times.

    :param action: Callable to execute.
    :param count: Maximum number of retry attempts (default: 10).
    :return: Result of the action if successful.
    :raises Exception: Re-raises the exception if retry attempts are exhausted.
    """
    try:
        return action()
    except Exception as e:
        traceback.print_exc()
        print(f"Error occurred: {e}. Retrying... ({count} attempts left)")
        if count <= 1:
            raise ValueError(f"Retry attempts exceeded: {e}") from e

        time.sleep(1)
        return retry_action(action, count - 1)


def run_periodically(interval, func):
    def worker():
        while True:
            func()
            time.sleep(interval)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    

def make_list(value):
    if value is None:
        return []

    if type(value) is set:
        return list(value)

    if type(value) is not list:
        value = [value]
    return value
