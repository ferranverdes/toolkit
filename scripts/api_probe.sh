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

for e in "${ENDPOINTS[@]}"; do
  echo "== $e =="

  res=$(curl -s --max-time 5 "$TARGET$e")

  if echo "$res" | jq . >/dev/null 2>&1; then
    echo "$res" | jq .
  else
    echo "$res"
  fi

  echo
done