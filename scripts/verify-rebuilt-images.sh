#!/usr/bin/env bash
# Run ./test.sh for every directory in rebuild-fixed-images.sh (79 dirs).
#
# Usage:
#   ./scripts/verify-rebuilt-images.sh
#   VERIFY_LOG=/path/to.log ./scripts/verify-rebuilt-images.sh
#
# Default VERIFY_LOG: <repo>/verify-rebuilt-79.log (full test output + summary lines)
# Optional: MAX_TESTS=N  START_AFTER=basename
#
set -u
set +e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

# Compliance: fail fast. Override per-run if needed (e.g. MCP_HTTP_LIST_MAX_WAIT=120).
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-10}"
export MCP_HTTP_LIST_MAX_WAIT="${MCP_HTTP_LIST_MAX_WAIT:-30}"
# Stdio docker run had NO timeout (could hang forever).
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-45}"
export MCP_STDIO_DOCKER_TIMEOUT_CALL="${MCP_STDIO_DOCKER_TIMEOUT_CALL:-90}"

extract_image_tag_from_test_sh() {
  local dir="$1"
  local ts="$dir/test.sh"
  [ -f "$ts" ] || { echo ""; return; }
  local line
  line=$(grep -E '^IMAGE=' "$ts" | head -1) || true
  [ -n "$line" ] || { echo ""; return; }
  line="${line#IMAGE=}"
  line="${line%\"}"
  line="${line#\"}"
  line="${line%\'}"
  line="${line#\'}"
  echo "$line"
}

VERIFY_LOG="${VERIFY_LOG:-${ROOT}/verify-rebuilt-79.log}"
: >"$VERIFY_LOG"

list_build_dirs() {
  local tmp
  tmp=$(mktemp)
  grep -rl 'COPY mcp_http_proxy' "$ROOT" --include=Dockerfile 2>/dev/null \
    | while IFS= read -r f; do dirname "$f"; done >>"$tmp"
  for b in dirb-mcp dirsearch-mcp feroxbuster-mcp gobuster-mcp; do
    echo "$ROOT/$b" >>"$tmp"
  done
  LC_ALL=C sort -u "$tmp"
  rm -f "$tmp"
}

if [ -z "${START_AFTER:-}" ]; then
  started=true
else
  started=false
fi
seen="${START_AFTER:-}"

ok=0
fail=0
skipped=0
n=0

{
  echo "==================================================================================="
  echo "verify-rebuilt-images.sh started (UTC) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Log: $VERIFY_LOG"
  echo "==================================================================================="

  while IFS= read -r dir; do
    [ -z "$dir" ] && continue
    [ -f "$dir/test.sh" ] || continue
    base=$(basename "$dir")

    if [ "$started" = false ]; then
      if [ "$base" = "$seen" ]; then
        started=true
      else
        echo "[SKIP] $base (before START_AFTER)"
        skipped=$((skipped + 1))
        continue
      fi
    fi

    if [ -n "${MAX_TESTS:-}" ] && [ "$n" -ge "$MAX_TESTS" ]; then
      echo "[STOP] MAX_TESTS=$MAX_TESTS"
      break
    fi
    n=$((n + 1))

    echo ""
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo "[$n] $base"
    echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    t0=$(date +%s)
    img_tag=$(extract_image_tag_from_test_sh "$dir")
    if [ "${VERIFY_BUILD_MISSING:-1}" != "0" ] && [ -n "$img_tag" ] && ! docker image inspect "$img_tag" >/dev/null 2>&1; then
      echo "[BUILD] missing image $img_tag — docker build -t $img_tag $dir"
      if ! docker build -t "$img_tag" "$dir" >>"$VERIFY_LOG" 2>&1; then
        t1=$(date +%s)
        echo "[FAIL] $base (docker build failed, $((t1 - t0))s)"
        fail=$((fail + 1))
        continue
      fi
    fi
    if (cd "$dir" && bash ./test.sh); then
      t1=$(date +%s)
      echo "[PASS] $base ($((t1 - t0))s)"
      ok=$((ok + 1))
    else
      t1=$(date +%s)
      echo "[FAIL] $base ($((t1 - t0))s)"
      fail=$((fail + 1))
    fi
  done < <(list_build_dirs)

  echo ""
  echo "==================================================================================="
  echo "Finished (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "PASS: $ok  FAIL: $fail  skipped: $skipped"
  echo "==================================================================================="
  exit $([ "$fail" -gt 0 ] && echo 1 || echo 0)
} 2>&1 | tee -a "$VERIFY_LOG"
exit "${PIPESTATUS[0]}"
