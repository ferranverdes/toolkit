#!/usr/bin/env python3

import sys
import json
import requests

def main():
    # Need at least the URL
    if len(sys.argv) < 2:
        print(f"Usage:\n  {sys.argv[0]} <host:port/path> [message]")
        print(f"  echo 'message' | {sys.argv[0]} <host:port/path>")
        sys.exit(1)

    url = f"http://{sys.argv[1]}"

    # Determine where the message comes from
    if len(sys.argv) >= 3:
        # Message passed as argument
        message = " ".join(sys.argv[2:])
    else:
        # Message from stdin (pipe)
        message = sys.stdin.read().strip()

    if not message:
        print("No message provided.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "message": message
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        # Pretty print JSON (like jq)
        parsed = response.json()
        print(json.dumps(parsed, indent=4))

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()