#!/usr/bin/env bash
# Build -> Test -> Publish -> Verify each server, tracked in docs/publish-tracking.csv.
# Resumable: a server already marked Published=Y is skipped.
#   Built     = docker build succeeded
#   Tested    = test.sh result (PASS / "N passed, M failed" / FAIL)
#   Published = docker push to hackerdogs succeeded
#   Verified  = Docker Hub confirms tag 'latest' exists AND README/overview is set
# Env: DOCKERHUB_PAT (+ DOCKERHUB_USER) enable the README + verify steps.
# Usage: scripts/build-test-publish.sh <server> [server...]
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT=/tmp/mcpbuild/publish; mkdir -p "$OUT"
CSV="$ROOT/docs/publish-tracking.csv"
[ -f "$CSV" ] || echo "server,built,tested,published,verified,updated" > "$CSV"

upsert() { # server,built,tested,published,verified
  local s="$1"
  grep -vE "^${s}," "$CSV" > "$CSV.tmp" 2>/dev/null || true
  mv "$CSV.tmp" "$CSV"
  echo "${s},${2},${3},${4},${5},$(date -u +%FT%TZ)" >> "$CSV"
}

verify() { # server -> Y/N  (tag latest present AND full_description set)
  python3 - "$1" <<'PY'
import sys, json, urllib.request
s=sys.argv[1]; ns="hackerdogs"
def get(u):
    with urllib.request.urlopen(u, timeout=25) as r: return r.status, json.load(r)
try:
    st,_=get(f"https://hub.docker.com/v2/repositories/{ns}/{s}/tags/latest/")
    _,d=get(f"https://hub.docker.com/v2/repositories/{ns}/{s}/")
    print("Y" if st==200 and (d.get("full_description") or "").strip() else "N")
except Exception:
    print("N")
PY
}

for s in "$@"; do
  if [ ! -d "$s" ]; then upsert "$s" "NO_DIR" "-" "N" "N"; continue; fi
  if [ "$(awk -F, -v s="$s" '$1==s{print $4}' "$CSV" | tail -1)" = "Y" ]; then
    echo ">>> [$s] already published, skipping"; continue
  fi
  img="hackerdogs/${s}:latest"
  blog="$OUT/${s}.build.log"; tlog="$OUT/${s}.test.log"; plog="$OUT/${s}.push.log"

  echo ">>> [$s] build..."
  if ! docker build -t "$img" "$s" >"$blog" 2>&1; then
    echo "    BUILD_FAIL"; upsert "$s" "N" "-" "N" "N"; continue
  fi
  docker tag "$img" "$s" 2>/dev/null || true   # test.sh image-name aliases vary

  echo ">>> [$s] test..."
  ( cd "$s" && bash test.sh >"$tlog" 2>&1 )
  tline=$(sed 's/\x1b\[[0-9;]*m//g' "$tlog" | grep -iE "Results:|Summary:|^Total:|Counters:" | grep -i passed | tail -1)
  pc=$(echo "$tline" | grep -oiE "[0-9]+ passed" | grep -oE "[0-9]+" | head -1)
  fc=$(echo "$tline" | grep -oiE "[0-9]+ failed" | grep -oE "[0-9]+" | head -1)
  if [ -n "$pc" ]; then tested="${pc}pass-${fc:-0}fail"; else tested="UNKNOWN"; fi  # CSV-safe token

  echo ">>> [$s] push..."
  if ! docker push "$img" >"$plog" 2>&1; then
    echo "    PUSH_FAIL"; upsert "$s" "Y" "$tested" "N" "N"; continue
  fi

  # README/overview (needs PAT)
  if [ -n "${DOCKERHUB_PAT:-}" ]; then
    python3 "$ROOT/scripts/set-dockerhub-readme.py" "$s" >"$OUT/${s}.readme.log" 2>&1 || true
  fi
  ver=$(verify "$s")
  upsert "$s" "Y" "$tested" "Y" "$ver"
  echo "    DONE built=Y tested=$tested published=Y verified=$ver"
done

echo "=== tracking CSV: $CSV ==="
echo "published: $(awk -F, 'NR>1 && $4=="Y"' "$CSV" | wc -l | tr -d ' ') / $(($(wc -l < "$CSV")-1))"
