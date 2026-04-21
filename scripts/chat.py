#!/usr/bin/env python3

import sys
import json
import requests


def main():
    # Need at least the URL
    if len(sys.argv) < 2:
        print(f"Usage:\n  {sys.argv[0]} <host:port> [--session-id <id>] [message]")
        print(f"  echo 'message' | {sys.argv[0]} <host:port> [--session-id <id>]")
        sys.exit(1)

    url = f"http://{sys.argv[1]}/chat"

    # Parse args: extract --session-id if present
    args = sys.argv[2:]
    session_id = None

    if "--session-id" in args:
        idx = args.index("--session-id")
        if idx + 1 >= len(args):
            print("Error: --session-id requires a value.")
            sys.exit(1)
        session_id = args[idx + 1]
        # Remove --session-id and its value from args
        args = args[:idx] + args[idx + 2 :]

    # Determine where the message comes from
    if args:
        message = " ".join(args)
    else:
        message = sys.stdin.read().strip()

    if not message:
        print("No message provided.")
        sys.exit(1)

    headers = {"Content-Type": "application/json"}

    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        print("---")

        parsed = response.json()
        print(parsed["response"])

        # Print any extra fields besides "response"
        extra = {k: v for k, v in parsed.items() if k != "response"}
        if extra:
            print("---")
            for k, v in extra.items():
                print(f"{k}: {v}")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        print(response.text)
        sys.exit(1)


if __name__ == "__main__":
    main()
