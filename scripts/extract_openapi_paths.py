#!/usr/bin/env python3

import json
import sys


def extract_paths(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        paths = data.get("paths", {})

        if not isinstance(paths, dict):
            print("Error: 'paths' section is invalid.")
            sys.exit(1)

        for path in paths.keys():
            print(path)

    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} openapi.json")
        sys.exit(1)

    extract_paths(sys.argv[1])


if __name__ == "__main__":
    main()
