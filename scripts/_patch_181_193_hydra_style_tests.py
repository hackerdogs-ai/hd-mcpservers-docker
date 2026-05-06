"""Patch hydra-style test.sh (Test 3-6) for Idx 181-193 long-form MCP tests."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PATCHES = [
    ("gospider-mcp", "run_gospider", "-h"),
    ("graphql-voyager-mcp", "run_graphql_voyager", "--help"),
    ("grype-mcp", "run_grype", "--help"),
    ("hakrawler-mcp", "run_hakrawler", "--help"),
    ("hashcat-mcp", "run_hashcat", "--help"),
    ("hashid-mcp", "run_hashid", "--help"),
    ("hashpump-mcp", "run_hashpump", "--help"),
    ("holehe-mcp", "run_holehe", "--help"),
    ("horusec-mcp", "run_horusec", "--help"),
]

HEADER_INSERT = '''# shellcheck source=/dev/null
. "$PROJECT_DIR/../scripts/mcp_compliance_python.sh"
MCP_HDR_FILE="${TMPDIR:-/tmp}/mcp_http_${CONTAINER_NAME}.$$"
'''


def hydra_tail_template() -> str:
    hydra = (ROOT / "hydra-mcp" / "test.sh").read_text(encoding="utf-8")
    start = hydra.index("INIT_REQ=")
    return hydra[start:]


def call_req_line(tool: str, arg: str) -> str:
    obj = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": tool, "arguments": {"arguments": arg}},
    }
    return "CALL_REQ='" + json.dumps(obj, separators=(",", ":")) + "'"


def patch_tail(tail: str, tool: str, arg: str) -> str:
    tail = tail.replace("run_hydra", tool)
    tail = re.sub(
        r"CALL_REQ='\{[^']+\}'",
        call_req_line(tool, arg),
        tail,
        count=1,
    )
    tail = tail.replace(
        'info "[Test 6] MCP HTTP — tools/call (run_hydra)"',
        f'info "[Test 6] MCP HTTP — tools/call ({tool})"',
    )
    return tail


def patch_file(subdir: str, tool: str, arg: str) -> None:
    path = ROOT / subdir / "test.sh"
    text = path.read_text(encoding="utf-8")
    if "MCP_HDR_FILE" in text and "Mcp-Session-Id" in text:
        print("skip (already patched):", subdir)
        return
    if "cleanup() {" not in text or "# Test 3:" not in text:
        print("skip (unexpected layout):", subdir)
        return
    old_anchor = 'PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n\npass()'
    if old_anchor not in text:
        raise SystemExit(f"no PROJECT_DIR anchor: {subdir}")
    text = text.replace(
        old_anchor,
        'PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        + HEADER_INSERT
        + "\npass()",
        1,
    )
    text = text.replace(
        "cleanup() {\n    docker stop",
        "cleanup() {\n    rm -f \"$MCP_HDR_FILE\" 2>/dev/null || true\n    docker stop",
        1,
    )
    tail = patch_tail(hydra_tail_template(), tool, arg)
    pat = re.compile(
        r"# Test 3: MCP stdio mode[^\000]*\[ \$FAIL -gt 0 \] && exit 1 \|\| exit 0\n",
        re.DOTALL,
    )
    new_text, n = pat.subn(tail, text, count=1)
    if n != 1:
        raise SystemExit(f"replace count {n} for {subdir}")
    path.write_text(new_text, encoding="utf-8", newline="\n")
    print("patched:", subdir)


def main() -> None:
    for sub, tool, arg in PATCHES:
        patch_file(sub, tool, arg)


if __name__ == "__main__":
    main()
