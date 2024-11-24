import os
import shutil
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

