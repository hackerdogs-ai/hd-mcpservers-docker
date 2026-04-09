#!/usr/bin/env python3
"""Pipe stdin to `docker run -i` MCP stdio with hard timeout (for tools/call etc.)."""
from __future__ import annotations

import os
import subprocess
import sys

TIMEOUT = float(os.environ.get("MCP_STDIO_DOCKER_TIMEOUT", "45"))


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) < 1:
        print("usage: mcp_stdio_docker_pipe.py [docker args ...] <image>", file=sys.stderr)
        return 2
    image = argv[-1]
    extra = argv[:-1]
    cmd = ["docker", "run", "-i", "--rm", "-e", "MCP_TRANSPORT=stdio", *extra, image]
    data = sys.stdin.buffer.read()
    try:
        proc = subprocess.run(cmd, input=data, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        print(f"mcp_stdio_docker_pipe: TIMEOUT after {TIMEOUT}s ({image})", file=sys.stderr)
        if exc.stdout:
            sys.stdout.buffer.write(exc.stdout)
        if exc.stderr:
            sys.stdout.buffer.write(exc.stderr)
        return 0
    sys.stdout.buffer.write(proc.stdout)
    sys.stdout.buffer.write(proc.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
