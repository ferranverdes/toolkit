#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <host>"
  echo "Example: $0 192.168.1.10"
  exit 1
fi

TARGET="http://$1"

ENDPOINTS=(
  "/-/health"
  "/api/config"
  "/api/health"
  "/api/status"
)

for i in "${!ENDPOINTS[@]}"; do
  e="${ENDPOINTS[$i]}"

  echo "== $e =="

  res=$(curl -s --max-time 5 "$TARGET$e")

  if echo "$res" | jq . >/dev/null 2>&1; then
    echo "$res" | jq .
  else
    echo "$res"
  fi

  echo

  # Wait before next request
  # Rapidly testing these endpoints creates an obvious enumeration pattern in access logs
  if [ "$i" -lt $((${#ENDPOINTS[@]} - 1)) ]; then
    echo "Waiting 40 seconds..."
    sleep 40
  fi
done