import os
import time
import uuid
from functools import partial
from typing import Tuple

import boto3

from util.common import remove_path

aws_region_name = "ap-south-1"

_s3_client: boto3.session.Session.client = boto3.client("s3", region_name=aws_region_name)


def upload_file(local_path, s3_path):
    bucket, key = s3_url_to_bucket_key(s3_path)
    _s3_client.upload_file(local_path, bucket, key)


def s3_url_to_bucket_key(s3_url: str) -> Tuple[str, str]:
    split = s3_url.split("/")
    bucket = split[2]
    key = "/".join(split[3:])
    return bucket, key


class TempFile:

    def __init__(self, file_name=None):
        suffix = str(uuid.uuid4())
        self.file_path = f"{file_name}{suffix}" if file_name else f"/tmp/{suffix}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.file_path):
            remove_path(self.file_path)

    def write_string(self, string):
        with open(self.file_path, "w") as f:
            f.write(string)

    def copy_to(self, path):
        upload_file(self.file_path, path)

    def copy_from(self, path):
        upload_file(path, self.file_path)

    def read(self, mode="r"):
        with open(self.file_path, mode) as f:
            return f.read()

    def append(self, string):
        with open(self.file_path, "a") as f:
            f.write(string)


def read_bytes(s3_url):
    bucket, key = s3_url_to_bucket_key(s3_url)

    def _read():
        # Get the object from the bucket
        obj = _s3_client.get_object(Bucket=bucket, Key=key)
        return obj['Body'].read()

    return try_times(partial(_read), 3, "NoSuchKey")


def try_times(action, count=10, ignored_exception_msg=None):
    """
    :param action: try to run this
    :param count: count to retry
    :param ignored_exception_msg: if the msg contains on the exception, not try to run again and raise the exception
    :return:
    """
    try:
        return action()
    except Exception as e:
        if ignored_exception_msg is not None and ignored_exception_msg in str(e):
            raise e
        print(f"Error occurred: {e}. try again")
        if count < 0:
            raise ValueError(f"try exceeded: {e}") from e
        time.sleep(1)
        return try_times(action, count -1, ignored_exception_msg)
