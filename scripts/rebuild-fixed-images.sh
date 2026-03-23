#!/usr/bin/env bash
#
# Rebuild all images that include fixes for:
#   - mcp_http_proxy.py (stderr drain + long timeouts), OR
#   - hd_fetch.py COPY (dirb, dirsearch, feroxbuster, gobuster)
#
# Tags: primary tag from test.sh IMAGE="..." when present; else
#       -t <dirname> -t hackerdogs/<dirname>:latest
#
# Usage (from repo root):
#   ./scripts/rebuild-fixed-images.sh
#   LOG=./rebuild-images.log ./scripts/rebuild-fixed-images.sh
#
# Output goes to the terminal AND to $LOG (default: ./rebuild-fixed-images.log).
#
# Optional:
#   START_AFTER=dirname   skip until this basename (sorted), then continue
#   MAX_BUILDS=N          stop after N build attempts
#
set -u
set +e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

LOG="${LOG:-${ROOT}/rebuild-fixed-images.log}"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Was: exec >>"$LOG" only → zero progress on the terminal. Tee = terminal + log file.
exec > >(tee "$LOG") 2>&1

echo "==================================================================================="
echo "rebuild-fixed-images.sh started (UTC) $STAMP"
echo "Repo: $ROOT"
echo "Log:  $LOG  (same output is printed here and saved to this file)"
echo "==================================================================================="

extract_image_tag() {
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

# Full paths to build, sorted unique
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
seen_start="${START_AFTER:-}"

ok=0
fail=0
skipped=0
attempt=0

while IFS= read -r dir; do
  [ -z "$dir" ] && continue
  [ -d "$dir" ] || continue
  base=$(basename "$dir")

  if [ "$started" = false ]; then
    if [ "$base" = "$seen_start" ]; then
      started=true
    else
      echo "[SKIP] (before START_AFTER=$seen_start) $base"
      skipped=$((skipped + 1))
      continue
    fi
  fi

  if [ -n "${MAX_BUILDS:-}" ] && [ "$attempt" -ge "$MAX_BUILDS" ]; then
    echo "[STOP] MAX_BUILDS=$MAX_BUILDS"
    break
  fi
  attempt=$((attempt + 1))

  tag=$(extract_image_tag "$dir")
  build_args=(docker build)
  if [ -n "$tag" ]; then
    build_args+=(-t "$tag")
    if [[ "$tag" == hackerdogs/* ]]; then
      short="${tag#hackerdogs/}"
      short="${short%:latest}"
      build_args+=(-t "$short")
    fi
  else
    build_args+=(-t "$base" -t "hackerdogs/${base}:latest")
  fi
  build_args+=("$dir")

  echo ""
  echo "--------------------------------------------------------------------------------"
  echo "[BUILD] $base  (${build_args[*]})"
  echo "--------------------------------------------------------------------------------"
  start=$(date +%s)
  if "${build_args[@]}"; then
    end=$(date +%s)
    echo "[OK] $base in $((end - start))s"
    ok=$((ok + 1))
  else
    echo "[FAIL] $base"
    fail=$((fail + 1))
  fi
done < <(list_build_dirs)

echo ""
echo "==================================================================================="
echo "Finished (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "OK: $ok  FAIL: $fail  skipped: $skipped"
echo "==================================================================================="

if [ "$fail" -gt 0 ]; then
  exit 1
fi
exit 0
