#!/usr/bin/env python3
"""
Validate MCP tools/call output — exit 0 only if the call truly succeeded.

Reads the full captured blob (stdio docker output or HTTP/SSE body) from stdin.
argv[1] = expected JSON-RPC response id (e.g. 3 for stdio, 4 for HTTP).

Fails (exit 1) when:
  - Obvious transport/network errors appear anywhere (ENOTFOUND, fetch failed, …)
  - No JSON-RPC response for that id
  - Top-level JSON-RPC "error"
  - result.isError is True
  - result.content text clearly indicates failure (e.g. "Failed to retrieve")
"""
from __future__ import annotations

import json
import re
import sys

HARD_FAIL_PATTERNS = re.compile(
    r"ENOTFOUND|ECONNREFUSED|ETIMEDOUT|ENETUNREACH|"
    r"fetch failed|TypeError:\s*fetch|getaddrinfo|"
    r"certificate verify failed|SSL_ERROR",
    re.IGNORECASE,
)

# Line-start hints the tool reported failure (not "protocol OK but business error")
SOFT_FAIL_TEXT = re.compile(
    r"(?im)^\s*("
    r"failed to|unauthorized|forbidden|not found|"
    r"invalid api|rate limit exceeded|internal server error"
    r")\b",
    re.IGNORECASE,
)


def _id_matches(obj_id, target_id: int) -> bool:
    if obj_id == target_id:
        return True
    if isinstance(obj_id, str) and obj_id.isdigit() and int(obj_id) == target_id:
        return True
    return False


def iter_json_blobs(raw: str):
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        if not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: mcp-validate-tools-call-output.py <expected_id>", file=sys.stderr)
        return 2
    target_id = int(sys.argv[1])
    raw = sys.stdin.read()

    if HARD_FAIL_PATTERNS.search(raw):
        print(
            "VALIDATION_FAIL: network/DNS/transport error pattern found in output",
            file=sys.stderr,
        )
        return 1

    last = None
    for obj in iter_json_blobs(raw):
        if _id_matches(obj.get("id"), target_id) and ("result" in obj or "error" in obj):
            last = obj

    if last is None:
        print(
            f"VALIDATION_FAIL: no JSON-RPC response object with id={target_id}",
            file=sys.stderr,
        )
        return 1

    if last.get("error") is not None:
        print(f"VALIDATION_FAIL: JSON-RPC error: {last.get('error')}", file=sys.stderr)
        return 1

    res = last.get("result")
    if res is None:
        print("VALIDATION_FAIL: missing result", file=sys.stderr)
        return 1

    if res.get("isError") is True:
        print("VALIDATION_FAIL: result.isError is true", file=sys.stderr)
        return 1

    # Aggregate text content from MCP tool result
    texts: list[str] = []
    for block in res.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            t = block.get("text") or ""
            if isinstance(t, str):
                texts.append(t)
    combined = "\n".join(texts).strip()
    if combined and SOFT_FAIL_TEXT.search(combined):
        print(
            f"VALIDATION_FAIL: tool returned failure text: {combined[:200]!r}",
            file=sys.stderr,
        )
        return 1

    print("VALIDATION_OK: tools/call id=%s accepted" % target_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
