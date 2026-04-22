#!/usr/bin/env bash
set -euo pipefail

# Enumerate A2A agents by probing /.well-known/agent.json on a host across a port range.
#
# Usage:
#   ./enumerate_a2a_agents.sh <host> [start-end]
#
# Examples:
#   ./enumerate_a2a_agents.sh 192.168.150.25
#   ./enumerate_a2a_agents.sh 192.168.150.25 8000-8010
#   ./enumerate_a2a_agents.sh 192.168.150.25 7900-8050
#
# Requirements:
#   - curl
#   - jq

HOST="${1:-}"
PORT_RANGE="${2:-8000-8010}"
CONNECT_TIMEOUT="${CONNECT_TIMEOUT:-2}"
MAX_TIME="${MAX_TIME:-4}"

if [[ -z "$HOST" ]]; then
  echo "Usage: $0 <host> [start-end]" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required." >&2
  exit 1
fi

if [[ ! "$PORT_RANGE" =~ ^([0-9]+)-([0-9]+)$ ]]; then
  echo "Error: port range must be in the form start-end, e.g. 8000-8010" >&2
  exit 1
fi

START_PORT="${BASH_REMATCH[1]}"
END_PORT="${BASH_REMATCH[2]}"

if (( START_PORT > END_PORT )); then
  echo "Error: start port must be <= end port" >&2
  exit 1
fi

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

  # Basic validation that this looks like an Agent Card.
  if ! jq -e '
      type == "object" and
      (.name? != null) and
      (.serviceEndpoint? != null or .url? != null)
    ' >/dev/null 2>&1 <<<"$body"; then
    return 1
  fi

  echo "$body" | jq --arg host "$host" --argjson port "$port" '
    {
      host: $host,
      port: $port,
      name: (.name // ""),
      description: (.description // ""),
      protocolVersion: (.protocolVersion // ""),
      url: (.url // ""),
      serviceEndpoint: (.serviceEndpoint // ""),
      provider: (.provider.organization // ""),
      agentId: (.metadata.id // ""),
      version: (.metadata.version // ""),
      status: (.metadata.status // ""),
      skills: [(.skills[]? | {id: (.id // ""), name: (.name // ""), description: (.description // "")})]
    }
  '
}

found=0

for (( port=START_PORT; port<=END_PORT; port++ )); do
  if result="$(probe_agent "$HOST" "$port")"; then
    found=1
    echo "============================================================"
    echo "$result" | jq .
  fi
done

if (( found == 0 )); then
  echo "No A2A agents found on ${HOST} in port range ${PORT_RANGE}" >&2
  exit 1
fi