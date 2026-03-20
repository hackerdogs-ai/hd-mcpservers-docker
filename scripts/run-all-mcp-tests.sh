#!/usr/bin/env bash
#
# Run ./test.sh for every MCP server directory at repo root (*/test.sh).
# Writes per-server evidence:
#   - Servers using mcp-standard-six-test.sh or append_section (e.g. ai-infra-guard-mcp)
#     already write ./test-results.txt — we do not overwrite.
#   - All others: full stdout/stderr capture → <server>/test-results.txt
#
# Summary (repo root):
#   ALL_MCP_TESTS_SUMMARY.tsv   — directory, basename, exit_code, duration_sec, status
#   ALL_MCP_TESTS_RUN.log       — progress + each test’s console output
#
# Optional env:
#   RUN_MAX=N     — execute at most N servers (after RUN_START), for smoke tests
#   RUN_START=N   — 1-based index into the sorted list to start from (inclusive)
#
set -u
# Do not use set -e — continue the sweep after individual server failures
set +e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

SUMMARY="${ROOT}/ALL_MCP_TESTS_SUMMARY.tsv"
MASTER_LOG="${ROOT}/ALL_MCP_TESTS_RUN.log"
RUN_MAX="${RUN_MAX:-}"
RUN_START="${RUN_START:-1}"

writes_test_results_internally() {
  local f="$1"
  grep -qE 'mcp-standard-six-test\.sh' "$f" 2>/dev/null && return 0
  grep -qE 'append_section\(\)' "$f" 2>/dev/null && return 0
  return 1
}

STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
{
  echo "================================================================================="
  echo "MCP test sweep - all */test.sh under ${ROOT}"
  echo "Started (UTC): ${STAMP}"
  echo "RUN_MAX=${RUN_MAX:-unset (all)}  RUN_START=${RUN_START}"
  echo "================================================================================="
} | tee "$MASTER_LOG"

echo -e "directory\tbasename\texit_code\tduration_sec\tstatus" >"$SUMMARY"

LIST_TMP=$(mktemp)
find "$ROOT" -maxdepth 2 -type f -name test.sh | LC_ALL=C sort >"$LIST_TMP"
total=$(wc -l <"$LIST_TMP" | tr -d ' ')

count=0
exec_count=0
ok=0
fail=0

while IFS= read -r testsh; do
  [ -z "$testsh" ] && continue
  count=$((count + 1))
  if [ "$count" -lt "$RUN_START" ]; then
    continue
  fi
  if [ -n "$RUN_MAX" ] && [ "$exec_count" -ge "$RUN_MAX" ]; then
    break
  fi
  exec_count=$((exec_count + 1))

  dir=$(dirname "$testsh")
  name=$(basename "$dir")
  echo "" | tee -a "$MASTER_LOG"
  echo "[$exec_count executed / ~$total dirs] ($count index) $name" | tee -a "$MASTER_LOG"
  t0=$(date +%s)
  if writes_test_results_internally "$testsh"; then
    (cd "$dir" && bash ./test.sh) >>"$MASTER_LOG" 2>&1
    ec=$?
  else
    tmp=$(mktemp)
    (cd "$dir" && bash ./test.sh) >"$tmp" 2>&1
    ec=$?
    {
      echo "MCP test run - $name"
      echo "Generated (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "Exit code: $ec"
      echo "Note: Full stdout/stderr capture (this test.sh does not use the structured test-results writer)."
      echo "---------------------------------------------------------------------------------"
      cat "$tmp"
    } >"$dir/test-results.txt"
    rm -f "$tmp"
  fi
  t1=$(date +%s)
  dur=$((t1 - t0))
  if [ "$ec" -eq 0 ]; then
    st=PASS
    ok=$((ok + 1))
  else
    st=FAIL
    fail=$((fail + 1))
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$dir" "$name" "$ec" "$dur" "$st" >>"$SUMMARY"
done <"$LIST_TMP"

rm -f "$LIST_TMP"

{
  echo ""
  echo "================================================================================="
  echo "Sweep finished (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Servers in tree: $total  Executed this run: $exec_count  PASS: $ok  FAIL: $fail"
  echo "Summary TSV: $SUMMARY"
  echo "Full log:    $MASTER_LOG"
  echo "================================================================================="
} | tee -a "$MASTER_LOG"

if [ "$fail" -gt 0 ]; then
  exit 1
fi
exit 0
