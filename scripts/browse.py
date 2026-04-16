#!/usr/bin/env python3

import sys
import json
import time
import threading
from urllib.parse import urlparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import requests


def main():
    if len(sys.argv) != 3:
        print(f"Usage:\n  {sys.argv[0]} <host:port> <url>")
        print(
            f"Example:\n  {sys.argv[0]} 192.168.1.22:8001 http://192.168.45.160:7777/article.html"
        )
        sys.exit(1)

    target = sys.argv[1]
    fetch_url = sys.argv[2]

    parsed = urlparse(fetch_url)

    if parsed.scheme != "http" or not parsed.hostname or not parsed.port:
        print("URL must be a full http://host:port/path URL")
        sys.exit(1)

    browse_url = f"http://{target}/browse"

    # Start a simple web server from the current directory
    server = ThreadingHTTPServer(
        (parsed.hostname, parsed.port), SimpleHTTPRequestHandler
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Small delay so the server is ready
    time.sleep(0.2)

    payload = {"url": fetch_url}

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(browse_url, headers=headers, json=payload)
        response.raise_for_status()

        parsed_json = response.json()
        print(json.dumps(parsed_json, indent=4))

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        print(response.text)
        sys.exit(1)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
