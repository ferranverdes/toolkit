#!/usr/bin/env python3

import json
import sys


def extract_paths(data_source):
    try:
        if isinstance(data_source, str):
            with open(data_source, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.load(data_source)

        paths = data.get("paths", {})

        if not isinstance(paths, dict):
            print("Error: 'paths' section is invalid.")
            sys.exit(1)

        for path in paths.keys():
            print(path)

    except FileNotFoundError:
        print(f"Error: File not found: {data_source}")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        sys.exit(1)


def main():
    if len(sys.argv) == 1 and not sys.stdin.isatty():
        extract_paths(sys.stdin)
    elif len(sys.argv) == 2:
        extract_paths(sys.argv[1])
    else:
        print(f"Usage: {sys.argv[0]} openapi.json")
        print(f"       curl -s http://host/openapi.json | {sys.argv[0]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
