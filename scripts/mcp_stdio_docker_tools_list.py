#!/usr/bin/env python3
"""
Run MCP initialize + notifications/initialized + tools/list over Docker stdio with a HARD timeout.

Compliance tests used `docker run -i` with no timeout — a stuck server blocks forever.
Env: MCP_STDIO_DOCKER_TIMEOUT (seconds, default 45).
"""
from __future__ import annotations

import os
import subprocess
import sys

TIMEOUT = float(os.environ.get("MCP_STDIO_DOCKER_TIMEOUT", "45"))
# export MCP_COMPLIANCE_DUMP_IO=1 to print docker cmd, stdin, stdout, stderr on stderr (noisy).
DUMP_IO = os.environ.get("MCP_COMPLIANCE_DUMP_IO", "0") == "1"


def _log(msg: str) -> None:
    if DUMP_IO:
        print(msg, file=sys.stderr)

INIT_REQ = (
    '{"jsonrpc":"2.0","id":1,"method":"initialize",'
    '"params":{"protocolVersion":"2024-11-05","capabilities":{},'
    '"clientInfo":{"name":"test","version":"1.0"}}}'
)
INIT_NOTIF = '{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
INPUT_BYTES = (INIT_REQ + "\n" + INIT_NOTIF + "\n" + LIST_REQ + "\n").encode()


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) < 1:
        print(
            "usage: mcp_stdio_docker_tools_list.py [docker run extra args ...] <image>",
            file=sys.stderr,
        )
        return 2
    image = argv[-1]
    extra = argv[:-1]
    cmd = ["docker", "run", "-i", "--rm", "-e", "MCP_TRANSPORT=stdio", *extra, image]
    _log("--- mcp_stdio_docker_tools_list: docker command ---")
    _log(" ".join(cmd))
    _log("--- mcp_stdio_docker_tools_list: bytes sent on stdin (MCP lines) ---")
    _log(INPUT_BYTES.decode())
    try:
        proc = subprocess.run(
            cmd,
            input=INPUT_BYTES,
            capture_output=True,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
        if b'"tools"' in out:
            print(
                f"mcp_stdio_docker_tools_list: wall-clock {TIMEOUT}s hit (docker still running) "
                f"but tools/list JSON is present — increase MCP_STDIO_DOCKER_TIMEOUT if you want clean exit",
                file=sys.stderr,
            )
        else:
            print(
                f"mcp_stdio_docker_tools_list: TIMEOUT after {TIMEOUT}s (image={image}) — incomplete response",
                file=sys.stderr,
            )
        if out:
            sys.stdout.buffer.write(out)
        return 0

    if DUMP_IO:
        _log("--- mcp_stdio_docker_tools_list: docker stdout (raw) ---")
        _log(proc.stdout.decode(errors="replace"))
        _log("--- mcp_stdio_docker_tools_list: docker stderr (raw) ---")
        _log(proc.stderr.decode(errors="replace"))

    sys.stdout.buffer.write(proc.stdout)
    # If tools only appear on stderr, surface for grep (some noisy servers)
    if b'"tools"' not in proc.stdout and b'"tools"' in proc.stderr:
        sys.stdout.buffer.write(proc.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
