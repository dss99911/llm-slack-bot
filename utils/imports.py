from dotenv import load_dotenv
load_dotenv()
# noinspection PyUnresolvedReferences
import logging
import os
# noinspection PyUnresolvedReferences
from typing import Literal, Dict, Optional, Annotated, Tuple, List
# noinspection PyUnresolvedReferences
import re
# noinspection PyUnresolvedReferences
from dataclasses import dataclass
# noinspection PyUnresolvedReferences
from itertools import chain
# noinspection PyUnresolvedReferences
import uuid
# noinspection PyUnresolvedReferences
import pandas as pd
# noinspection PyUnresolvedReferences
import threading
# noinspection PyUnresolvedReferences
from utils.common import *
# noinspection PyUnresolvedReferences
import base64
# noinspection PyUnresolvedReferences
import time
# noinspection PyUnresolvedReferences
from functools import partial
# noinspection PyUnresolvedReferences
import json
# noinspection PyUnresolvedReferences
import requests
# noinspection PyUnresolvedReferences
from requests.auth import HTTPBasicAuth
# noinspection PyUnresolvedReferences
from utils import slack
# noinspection PyUnresolvedReferences
from utils.slack import SlackEvent
# noinspection PyUnresolvedReferences
from datetime import datetime
# noinspection PyUnresolvedReferences
import pytz
from utils.cache import Cache

env = os.environ.get("ENV")
prod = env == "prod"
logging.basicConfig(
    level="INFO" if prod else "DEBUG",
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)