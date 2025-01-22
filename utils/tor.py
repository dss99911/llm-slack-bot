import logging
import socket

import requests

from utils.common import memoize, run_periodically
from stem.control import Controller

address = "torproxy"
TOR_CONTROL_PORT = 9051
tor_ip = socket.gethostbyname(address)

TOR_PROXY_URL = f"socks5://{address}:9050"
index = 0


def move_to_next_exit_node():
    global index
    index += 1
    fingerprints = get_exit_node_fingerprints()
    fingerprint = fingerprints[index % len(fingerprints)]
    with Controller.from_port(address=tor_ip, port=TOR_CONTROL_PORT) as controller:
        controller.authenticate()
        controller.set_options({
            'ExitNodes': fingerprint,
            'StrictNodes': '1'
        })
        logging.info(f"Exit node set to: {fingerprint}")


def fetch_exit_node_fingerprints():
    url = "https://onionoo.torproject.org/details?flag=Exit"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        exit_fingerprints = [relay['fingerprint'] for relay in data['relays']]
        return exit_fingerprints
    except requests.RequestException as e:
        logging.info(f"Error fetching data: {e}")
        return []


@memoize(expiry_seconds=3600)
def get_exit_node_fingerprints():
    fingerprints = fetch_exit_node_fingerprints()
    logging.info(f"exit node count: {len(fingerprints)}")
    return fingerprints


run_periodically(3600, get_exit_node_fingerprints)