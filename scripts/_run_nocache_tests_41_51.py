"""Run docker build (optional --no-cache) then ./test.sh for simple-index idx 41-51."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tmp-test-41-51-nocache"
OUT.mkdir(exist_ok=True)
SUMMARY = ROOT / "tmp-test-41-51-nocache-summary.tsv"

def git_bash_cd_path(win: Path) -> str:
    """Windows path -> Git Bash style /c/Users/... (no cygpath required)."""
    p = str(win.resolve())
    if len(p) >= 2 and p[1] == ":":
        return "/" + p[0].lower() + p[2:].replace("\\", "/")
    return p.replace("\\", "/")


ALL_TARGETS = [
    (41, "amass-mcp"),
    (42, "anew-mcp"),
    (43, "angr-mcp"),
    (44, "apple-itunes-mcp"),
    (45, "aquatone-mcp"),
    (46, "archiveorg-mcp"),
    (47, "arin-mcp"),
    (48, "arjun-mcp"),
    (49, "arp-scan-mcp"),
    (50, "asnmap-mcp"),
    (51, "assetfinder-mcp"),
]


def image_from_test_sh(text: str) -> str | None:
    m = re.search(r'^IMAGE="([^"]+)"', text, re.MULTILINE)
    if m:
        return m.group(1)
    m = re.search(r'^MCP_IMAGE="([^"]+)"', text, re.MULTILINE)
    if m:
        return m.group(1)
    return None


def classify(log_lower: str, exit_code: int) -> tuple[str, str]:
    stdio_pass = any(
        x in log_lower
        for x in (
            "pass: stdio tools/list",
            "pass: stdio list",
            "stdio mode returned tools/list response",
        )
    )
    stdio_fail = "fail: stdio tools/list" in log_lower or "fail: stdio list" in log_lower
    http_pass = any(
        x in log_lower
        for x in (
            "pass: http tools/list",
            "pass: http list",
            "pass: http streamable mode responded",
            "http tools/list returned tools",
        )
    )
    http_fail = "fail: http tools/list" in log_lower or "fail: http list" in log_lower
    stdio = "PASS" if stdio_pass else ("FAIL" if stdio_fail else ("PASS" if exit_code == 0 else "FAIL"))
    http = "PASS" if http_pass else ("FAIL" if http_fail else ("PASS" if exit_code == 0 else "FAIL"))
    return stdio, http


def main() -> None:
    use_nocache = os.environ.get("MCP_NOCACHE", "1") != "0"
    if len(sys.argv) > 1:
        want = set(sys.argv[1:])
        targets = [(i, n) for i, n in ALL_TARGETS if str(i) in want]
    else:
        targets = list(ALL_TARGETS)

    rows: list[str] = []
    for idx, name in targets:
        d = ROOT / name
        ts = d / "test.sh"
        if not ts.is_file():
            rows.append(f"{idx}\t{name}\tFAIL\tFAIL\t-1\tmissing test.sh")
            SUMMARY.write_text("\n".join(rows) + "\n", encoding="utf-8")
            print(rows[-1], flush=True)
            continue
        text = ts.read_text(encoding="utf-8", errors="replace")
        image = image_from_test_sh(text)
        if use_nocache and image:
            build = f'docker build --no-cache -t "{image}" . && '
        elif image:
            build = f'docker build -t "{image}" . && '
        else:
            build = ""
        # Wait for Docker (reduces Windows Docker Desktop flakes during long batches).
        bash_script = f"""set -euo pipefail
i=0
while [ "$i" -lt 90 ]; do
  docker info >/dev/null 2>&1 && break
  i=$((i+1))
  sleep 2
done
docker info >/dev/null 2>&1 || {{ echo "docker unavailable"; exit 1; }}
mkdir -p /tmp/pyshim
ln -sf /usr/bin/python3 /tmp/pyshim/python
export PATH="/tmp/pyshim:$PATH"
cd "$MCP_RUN_UNIX"
{build}./test.sh
"""
        log_path = OUT / f"{idx}-{name}-nocache.log"
        env = os.environ.copy()
        env["MCP_RUN_UNIX"] = git_bash_cd_path(d)
        with open(log_path, "wb") as lf:
            p = subprocess.run(
                ["bash", "-lc", bash_script],
                cwd=str(d),
                stdout=lf,
                stderr=subprocess.STDOUT,
                timeout=7200,
                env=env,
            )
        body = log_path.read_bytes().decode("utf-8", errors="ignore").lower()
        s1, s2 = classify(body, p.returncode)
        note = ""
        if "0x8007274c" in body or "8007274c" in body:
            note = "docker desktop unreachable"
        elif "docker unavailable" in body:
            note = "docker not running"
        elif "error" in body and p.returncode != 0:
            note = "see log"
        rows.append(f"{idx}\t{name}\t{s1}\t{s2}\t{p.returncode}\t{note}".rstrip())
        SUMMARY.write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(rows[-1], flush=True)
        time.sleep(10)


if __name__ == "__main__":
    main()
