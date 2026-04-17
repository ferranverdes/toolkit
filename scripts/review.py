#!/usr/bin/env python3

import sys
import json
import requests


def main():
    # Need at least host:port and local file
    if len(sys.argv) < 3:
        print(f"Usage:\n  {sys.argv[0]} <host:port> <local_file>")
        sys.exit(1)

    host = sys.argv[1]
    local_file = sys.argv[2]

    upload_url = f"http://{host}/upload"
    review_url = f"http://{host}/review"

    try:
        # Step 1: Upload file
        with open(local_file, "rb") as f:
            files = {"file": f}
            upload_resp = requests.post(upload_url, files=files)

        upload_resp.raise_for_status()
        upload_data = upload_resp.json()

        remote_path = upload_data["path"]

        print(f"[+] Uploaded: {local_file}")
        print(f"[+] Remote path: {remote_path}")

        # Step 2: Request review using returned path
        headers = {"Content-Type": "application/json"}
        payload = {"path": remote_path}

        review_resp = requests.post(review_url, headers=headers, json=payload)

        review_resp.raise_for_status()
        review_data = review_resp.json()

        print("---")
        print(review_data["review"])

    except FileNotFoundError:
        print(f"File not found: {local_file}")
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("Failed to decode JSON response.")
        sys.exit(1)

    except KeyError as e:
        print(f"Missing expected field in response: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
