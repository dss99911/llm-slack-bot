from functools import wraps


def memoize(f):
    memo = {}

    @wraps(f)
    def wrapper(*args):
        if args not in memo:
            memo[args] = f(*args)
        return memo[args]

    return wrapper
