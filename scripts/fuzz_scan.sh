#!/usr/bin/env bash
# =============================================================================
# fuzz_scan.sh — AI API endpoint fuzzer using ffuf
# Usage: ./fuzz_scan.sh <IP> [start_port] [end_port]
# Example: ./fuzz_scan.sh 192.168.1.10
#          ./fuzz_scan.sh 192.168.1.10 8080 8090
# =============================================================================

set -uo pipefail
# Ensure this script leads its own process group so `kill -- -$$` reaches
# every background child. `set -m` enables job-control / process-group
# creation; it's a no-op on shells that don't support it.
set -m 2>/dev/null || true

THREADS=3

# ─── Colours ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ─── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_PORT_START=8000
DEFAULT_PORT_END=8020
WORDLIST="/shared/toolkit/lists/ai_api_wordlist.txt"

# ─── Args ────────────────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo -e "${RED}[!] Usage: $0 <IP> [start_port] [end_port]${RESET}"
  exit 1
fi

TARGET_IP="$1"
PORT_START="${2:-$DEFAULT_PORT_START}"
PORT_END="${3:-$DEFAULT_PORT_END}"

# ─── Preflight checks ────────────────────────────────────────────────────────
if ! command -v ffuf &>/dev/null; then
  echo -e "${RED}[!] ffuf not found in PATH. Please install it first.${RESET}"
  exit 1
fi

if [[ ! -f "$WORDLIST" ]]; then
  echo -e "${RED}[!] Wordlist not found: ${WORDLIST}${RESET}"
  exit 1
fi

# ─── Output directory ────────────────────────────────────────────────────────
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="./fuzz_results_${TARGET_IP//\./_}_${TIMESTAMP}"
mkdir -p "$OUT_DIR"

SUMMARY_FILE="$OUT_DIR/summary.txt"
FFUF_LOG="$OUT_DIR/ffuf_raw.log"

# ─── Ctrl+C / TERM handler ───────────────────────────────────────────────────
cleanup() {
  echo -e "\n\n${RED}${BOLD}[!] Interrupted — killing all ffuf processes...${RESET}"
  # Kill the entire process group (dispatcher, worker subshells, ffuf children).
  kill -- -$$ 2>/dev/null || true
  # Fallback: walk direct children, then orphaned ffuf processes.
  pkill -P $$ 2>/dev/null || true
  pkill -x ffuf 2>/dev/null || true
  echo -e "${DIM}Partial results saved to: ${OUT_DIR}/${RESET}\n"
  exit 130
}
trap cleanup INT TERM

# ─── Helpers ─────────────────────────────────────────────────────────────────
banner() {
  local title="$1" width=70 line
  line=$(printf '─%.0s' $(seq 1 $width))
  echo -e "\n${CYAN}${BOLD}┌${line}┐${RESET}"
  printf "${CYAN}${BOLD}│  %-$((width - 2))s│${RESET}\n" "$title"
  echo -e "${CYAN}${BOLD}└${line}┘${RESET}"
}

info() { echo -e "  ${DIM}▸${RESET} ${BOLD}$1:${RESET} $2"; }

parse_hits() {
  local json_file="$1" method="$2"
  [[ ! -f "$json_file" ]] && { echo -e "  ${DIM}No hits found.${RESET}"; return; }

  python3 - "$json_file" "$method" <<'EOF'
import json, sys
path, method = sys.argv[1], sys.argv[2]
RESET="\033[0m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"
BOLD="\033[1m";  DIM="\033[2m";      RED="\033[0;31m"
try:
    data = json.load(open(path))
except Exception as e:
    print(f"  {RED}[!] Could not parse output: {e}{RESET}"); sys.exit(0)
results = data.get("results", [])
if not results:
    print(f"  {DIM}No hits found.{RESET}"); sys.exit(0)
results.sort(key=lambda r: (r.get("status", 0), r.get("url", "")))
for r in results:
    url = r.get("url", "")
    part = url.split("/", 3)[-1] if url.count("/") >= 3 else url
    print(f"  {DIM}{part}{RESET}")
print(f"\n  {'STATUS':<8} {'METHOD':<7} URL")
print(f"  {'─'*6:<8} {'─'*6:<7} {'─'*40}")
for r in results:
    status, url = r.get("status","?"), r.get("url","?")
    c = GREEN if str(status).startswith("2") else (YELLOW if str(status).startswith("3") else "")
    print(f"  {c}{BOLD}{str(status):<8}{RESET} {method:<7} {url}")
print(f"\n  {DIM}Total hits: {len(results)}{RESET}")
EOF
}

# ─── Worker: scan one port ────────────────────────────────────────────────────
scan_port() {
  local port="$1"
  local BASE_URL="http://${TARGET_IP}:${port}"
  local PORT_DIR="${OUT_DIR}/port_${port}"
  mkdir -p "$PORT_DIR"

  local GET_JSON="${PORT_DIR}/get_results.json"
  local POST_JSON="${PORT_DIR}/post_results.json"
  local PORT_LOG="${PORT_DIR}/ffuf_raw.log"

  {
    echo "══════════════════════════════════════════════════"
    echo "Port ${port}  →  ${BASE_URL}  ($(date '+%H:%M:%S'))"
    echo "══════════════════════════════════════════════════"
    echo "--- GET ---"
  } > "$PORT_LOG"

  ffuf -u "${BASE_URL}/FUZZ" -w "$WORDLIST" \
    -mc all -fc 404 -o "$GET_JSON" -of json \
    >>"$PORT_LOG" 2>&1 || true

  echo "--- POST ---" >> "$PORT_LOG"

  ffuf -u "${BASE_URL}/FUZZ" -w "$WORDLIST" \
    -X POST -H "Content-Type: application/json" -d '{}' \
    -mc all -fc 404,405 -o "$POST_JSON" -of json \
    >>"$PORT_LOG" 2>&1 || true

  touch "${PORT_DIR}/.done"
}

# ─── Dispatcher: runs in background, launches workers with concurrency cap ───
dispatcher() {
  local slots="$OUT_DIR/.slots"
  mkdir -p "$slots"

  for port in $(seq "$PORT_START" "$PORT_END"); do
    # Wait for a free slot
    while (( $(ls "$slots" | wc -l) >= THREADS )); do
      sleep 0.1
    done
    touch "${slots}/${port}"
    (
      scan_port "$port"
      rm -f "${slots}/${port}"
    ) &
  done
  wait
}

# ─── Main ────────────────────────────────────────────────────────────────────
banner "FFUF AI API Scan  |  Target: ${TARGET_IP}  |  Ports: ${PORT_START}-${PORT_END}  |  Threads: ${THREADS}"
info "Wordlist"   "$WORDLIST"
info "Output dir" "$OUT_DIR"
info "Started"    "$(date)"
echo

{
  echo "FFUF AI API Scan Summary"
  echo "========================"
  echo "Target  : $TARGET_IP"
  echo "Ports   : $PORT_START - $PORT_END"
  echo "Started : $(date)"
  echo "Wordlist: $WORDLIST"
  echo ""
} > "$SUMMARY_FILE"

TOTAL_PORTS=$(( PORT_END - PORT_START + 1 ))

# Start dispatcher in background — workers start immediately
dispatcher &
DISPATCHER_PID=$!

# ── Printer: walks ports in order, prints each one as soon as .done appears ──
CURRENT=0
for port in $(seq "$PORT_START" "$PORT_END"); do
  CURRENT=$(( CURRENT + 1 ))
  PORT_DIR="${OUT_DIR}/port_${port}"
  BASE_URL="http://${TARGET_IP}:${port}"

  # Block only on this specific port, not on any other
  while [[ ! -f "${PORT_DIR}/.done" ]]; do
    sleep 0.2
  done

  cat "${PORT_DIR}/ffuf_raw.log" >> "$FFUF_LOG"

  GET_JSON="${PORT_DIR}/get_results.json"
  POST_JSON="${PORT_DIR}/post_results.json"

  get_hits=$(python3 -c "
import json
try:  print(len(json.load(open('$GET_JSON')).get('results',[])))
except: print(0)" 2>/dev/null || echo 0)

  post_hits=$(python3 -c "
import json
try:  print(len(json.load(open('$POST_JSON')).get('results',[])))
except: print(0)" 2>/dev/null || echo 0)

  echo -e "\n${MAGENTA}${BOLD}[${CURRENT}/${TOTAL_PORTS}]${RESET} Port ${BOLD}${port}${RESET}  →  ${BASE_URL}  ${DIM}$(date '+%H:%M:%S')${RESET}"

  if [[ "$get_hits" -eq 0 && "$post_hits" -eq 0 ]]; then
    echo -e "  ${DIM}GET/POST — No hits found.${RESET}"
  else
    echo -e "  ${YELLOW}${BOLD}[GET]${RESET} Fuzzing endpoints..."
    parse_hits "$GET_JSON" "GET"
    echo -e "\n  ${YELLOW}${BOLD}[POST]${RESET} Fuzzing endpoints with JSON body..."
    parse_hits "$POST_JSON" "POST"
  fi

  {
    echo "Port $port ($BASE_URL)"
    echo "  GET results : $GET_JSON"
    echo "  POST results: $POST_JSON"
    echo ""
  } >> "$SUMMARY_FILE"
done

wait "$DISPATCHER_PID" 2>/dev/null || true

# ─── Final footer ─────────────────────────────────────────────────────────────
echo ""
banner "Scan Complete"
info "Finished"    "$(date)"
info "Results"     "$OUT_DIR/"
info "ffuf log"    "$FFUF_LOG"
info "Summary"     "$SUMMARY_FILE"
echo -e "\n  ${DIM}Raw JSON files saved per port inside: ${OUT_DIR}/${RESET}\n"

echo "Finished: $(date)" >> "$SUMMARY_FILE"