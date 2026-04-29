#!/usr/bin/env python3

import json
import sys
import subprocess
import ipaddress
import re


DEFAULT_PORTS = range(8000, 8021)


def is_host(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def looks_like_ports(value):
    allowed = set("0123456789,-")
    return bool(value) and all(char in allowed for char in value)


def parse_ports(value):
    ports = set()

    for part in value.split(","):
        part = part.strip()

        if not part:
            continue

        if "-" in part:
            start, end = map(int, part.split("-", 1))
            ports.update(range(start, end + 1))
        else:
            ports.add(int(part))

    return sorted(ports)


def normalize_path(path):
    return path.lstrip("/")


def wordlist_path_format(path):
    path = normalize_path(path)
    path = re.sub(r"\{([^}]+)\}", r"\1", path)
    return path


def load_wordlist(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(wordlist_path_format(line.strip()) for line in f if line.strip())
    except FileNotFoundError:
        print(f"Error: Wordlist not found: {path}", file=sys.stderr)
        sys.exit(1)


def append_to_wordlist(path, endpoints):
    endpoints = sorted(
        wordlist_path_format(endpoint) for endpoint in endpoints if endpoint
    )

    if not endpoints:
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except FileNotFoundError:
        existing_content = ""

    with open(path, "a", encoding="utf-8") as f:
        if existing_content and not existing_content.endswith("\n"):
            f.write("\n")

        for index, endpoint in enumerate(endpoints):
            f.write(endpoint)
            if index != len(endpoints) - 1:
                f.write("\n")


def fetch_openapi_from_host(host, ports):
    found_specs = []

    for port in ports:
        url = f"http://{host}:{port}/openapi.json"

        try:
            result = subprocess.run(
                ["curl", "-fsS", "--max-time", "3", url],
                capture_output=True,
                text=True,
                check=True,
            )

            data = json.loads(result.stdout)
            found_specs.append((url, data))

        except subprocess.CalledProcessError:
            continue
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON from {url}", file=sys.stderr)

    if not found_specs:
        print(f"Error: No valid openapi.json found on {host}", file=sys.stderr)
        sys.exit(1)

    return found_specs


def load_json_from_source(source):
    try:
        if hasattr(source, "read"):
            return json.load(source)

        with open(source, "r", encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"Error: File not found: {source}", file=sys.stderr)
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)


def get_paths(data):
    paths = data.get("paths", {})

    if not isinstance(paths, dict):
        print("Error: 'paths' section is invalid.", file=sys.stderr)
        sys.exit(1)

    return set(normalize_path(path) for path in paths.keys())


def output_paths(discovered, wordlist_path=None):
    discovered = set(normalize_path(endpoint) for endpoint in discovered if endpoint)

    if wordlist_path:
        existing = load_wordlist(wordlist_path)
        missing = {p for p in discovered if wordlist_path_format(p) not in existing}

        if missing:
            append_to_wordlist(wordlist_path, missing)

        for endpoint in sorted(missing):
            print(endpoint)
    else:
        for endpoint in sorted(discovered):
            print(endpoint)


def parse_host_args(args):
    host = args[0]
    ports = DEFAULT_PORTS
    wordlist = None

    if len(args) >= 2:
        if looks_like_ports(args[1]):
            ports = parse_ports(args[1])
            wordlist = args[2] if len(args) >= 3 else None
        else:
            wordlist = args[1]

    return host, ports, wordlist


def main():
    args = sys.argv[1:]

    if not args:
        if not sys.stdin.isatty():
            data = load_json_from_source(sys.stdin)
            output_paths(get_paths(data))
            return

        print("Usage:")
        print(f"  {sys.argv[0]} openapi.json [path/to/wordlist]")
        print(f"  {sys.argv[0]} <host> [path/to/wordlist]")
        print(f"  {sys.argv[0]} <host> [ports] [path/to/wordlist]")
        print(f"  {sys.argv[0]} 127.0.0.1 [path/to/wordlist]")
        print(f"  {sys.argv[0]} 127.0.0.1 8000-8020")
        print(f"  {sys.argv[0]} 127.0.0.1 8000,8001,8080 [path/to/wordlist]")
        print(
            f"  curl -s http://host:8000/openapi.json | {sys.argv[0]} [path/to/wordlist]"
        )
        sys.exit(1)

    source = args[0]

    if not is_host(source):
        wordlist = args[1] if len(args) > 1 else None
        data = load_json_from_source(source)
        output_paths(get_paths(data), wordlist)
        return

    host, ports, wordlist = parse_host_args(args)
    specs = fetch_openapi_from_host(host, ports)

    all_discovered = set()

    for url, data in specs:
        discovered = get_paths(data)
        all_discovered.update(discovered)

        print(f"\n# {url}")
        for endpoint in sorted(discovered):
            print(endpoint)

    if wordlist:
        existing = load_wordlist(wordlist)
        missing = {
            p for p in all_discovered if wordlist_path_format(p) not in existing
        }

        if missing:
            append_to_wordlist(wordlist, missing)

            print("\n# Added to wordlist", file=sys.stderr)
            for endpoint in sorted(wordlist_path_format(p) for p in missing):
                print(endpoint, file=sys.stderr)


if __name__ == "__main__":
    main()