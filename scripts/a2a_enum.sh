#!/usr/bin/env bash
set -euo pipefail

# Enumerate A2A agents by probing /.well-known/agent.json on a host across a port range.
#
# Usage:
#   ./enumerate_a2a_agents.sh <host> [start-end]

HOST="${1:-}"
PORT_RANGE="${2:-8000-8010}"
CONNECT_TIMEOUT="${CONNECT_TIMEOUT:-2}"
MAX_TIME="${MAX_TIME:-4}"

if [[ -z "$HOST" ]]; then
  echo "[-] Usage: $0 <host> [start-end]" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[-] curl is required." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[-] jq is required." >&2
  exit 1
fi

if [[ ! "$PORT_RANGE" =~ ^([0-9]+)-([0-9]+)$ ]]; then
  echo "[-] Port range must be in the form start-end (example: 8000-8010)." >&2
  exit 1
fi

START_PORT="${BASH_REMATCH[1]}"
END_PORT="${BASH_REMATCH[2]}"

if (( START_PORT > END_PORT )); then
  echo "[-] Start port must be less than or equal to end port." >&2
  exit 1
fi

is_plain_ip() {
  local value="$1"

  # IPv4
  if [[ "$value" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
    return 0
  fi

  # IPv6
  if [[ "$value" =~ ^\[?[0-9a-fA-F:]+\]?$ && "$value" == *:* ]]; then
    return 0
  fi

  return 1
}

extract_url_host() {
  local url="$1"
  local without_scheme host

  without_scheme="${url#*://}"
  host="${without_scheme%%/*}"
  host="${host%%:*}"
  host="${host#[}"
  host="${host%]}"

  printf '%s\n' "$host"
}

probe_agent() {
  local host="$1"
  local port="$2"
  local url="http://${host}:${port}/.well-known/agent.json"
  local body

  body="$(curl -fsS \
    --connect-timeout "$CONNECT_TIMEOUT" \
    --max-time "$MAX_TIME" \
    "$url" 2>/dev/null || true)"

  [[ -z "$body" ]] && return 1

  # Validate basic Agent Card structure
  if ! jq -e '
      type == "object" and
      (.name? != null) and
      (.serviceEndpoint? != null or .url? != null)
    ' >/dev/null 2>&1 <<<"$body"; then
    return 1
  fi

  echo "$body" | jq --argjson port "$port" '
    {
      port: $port,
      name: (.name // null),
      description: (.description // null),
      url: (.url // null),
      serviceEndpoint: (.serviceEndpoint // null),
      skills: [
        (.skills[]? | {
          id: (.id // null),
          name: (.name // null),
          description: (.description // null)
        } | with_entries(select(.value != null and .value != "")))
      ]
    }
    | with_entries(select(.value != null and .value != "" and .value != []))
  '
}

found=0

for (( port=START_PORT; port<=END_PORT; port++ )); do
  if result="$(probe_agent "$HOST" "$port")"; then
    found=1

    echo "============================================================"

    echo "$result" | jq .

    agent_url="$(echo "$result" | jq -r '.url // empty')"

    if [[ -n "$agent_url" ]]; then
      agent_host="$(extract_url_host "$agent_url")"

      if [[ -n "$agent_host" ]] && ! is_plain_ip "$agent_host"; then
        echo "[+] Agent URL uses DNS name instead of plain IP address: ${agent_url}"
      fi
    fi
  fi
done

if (( found == 0 )); then
  echo "[-] No A2A agents found on ${HOST} in port range ${PORT_RANGE}" >&2
  exit 1
fi