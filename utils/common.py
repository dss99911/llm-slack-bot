import os
import shutil
import time
from functools import wraps
from os.path import isdir



def memoize(f):
    memo = {}

    @wraps(f)
    def wrapper(*args):
        if args not in memo:
            memo[args] = f(*args)
        return memo[args]

    return wrapper


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
        print(f"Error occurred: {e}. Retrying... ({count} attempts left)")
        if count <= 1:
            raise ValueError(f"Retry attempts exceeded: {e}") from e

        time.sleep(1)
        return retry_action(action, count - 1)
