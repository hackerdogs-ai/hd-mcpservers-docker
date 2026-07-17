#!/usr/bin/env bash
# Re-verify the previously-failing MCP servers against CURRENT source.
# Builds hackerdogs/<dir>:latest, runs the server's own test.sh, records the Results line.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT=/tmp/mcpbuild/retest
mkdir -p "$OUT"
SUMMARY="$OUT/SUMMARY.tsv"
: > "$SUMMARY"

SERVERS="$*"
for s in $SERVERS; do
  [ -d "$s" ] || { printf "%s\tNO_DIR\n" "$s" >>"$SUMMARY"; continue; }
  img="hackerdogs/${s}:latest"
  blog="$OUT/${s}.build.log"; tlog="$OUT/${s}.test.log"
  if docker build -t "$img" "$s" >"$blog" 2>&1; then
    # test.sh image-name conventions vary; tag the build under common aliases.
    docker tag "$img" "$s" 2>/dev/null || true            # -> <name>:latest
    docker tag "$img" "${s%-mcp}" 2>/dev/null || true     # some expect the bare tool name
    ( cd "$s" && bash test.sh >"$tlog" 2>&1 )
    res=$(sed 's/\x1b\[[0-9;]*m//g' "$tlog" | grep -i -E "Results:|Summary:|^Total:" | grep -i "passed" | tail -1 | xargs)
    [ -z "$res" ] && res="NO_RESULTS_LINE"
    printf "%s\tBUILT\t%s\n" "$s" "$res" >>"$SUMMARY"
  else
    err=$(grep -i -E "ERROR|did not complete" "$blog" | tail -1 | sed 's/\x1b\[[0-9;]*m//g' | cut -c1-80)
    printf "%s\tBUILD_FAIL\t%s\n" "$s" "$err" >>"$SUMMARY"
  fi
done
echo "DONE" >>"$SUMMARY"
