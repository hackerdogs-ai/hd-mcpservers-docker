#!/usr/bin/env python3
"""
Run MCP initialize + notifications/initialized + tools/list over Docker stdio with a HARD timeout.

Uses Popen + incremental reads: MCP servers are long-lived — ``subprocess.run`` would block
until the container exits, which never happens on some hosts (notably Docker Desktop on
Windows). We stop as soon as ``"tools"`` appears in stdout/stderr, then terminate ``docker run``.
Env: MCP_STDIO_DOCKER_TIMEOUT (seconds, default 120; Docker Desktop cold starts can exceed 60s).

Use ``--check`` in shell tests instead of ``$(...)`` + grep: some upstream ``tools/list``
responses are megabytes; bash command substitution can truncate the capture and grep
then fails even when the server responded correctly.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

TIMEOUT = float(os.environ.get("MCP_STDIO_DOCKER_TIMEOUT", "120"))
DUMP_IO = os.environ.get("MCP_COMPLIANCE_DUMP_IO", "0") == "1"
# Some Node MCP servers buffer stdin until EOF; a short delay then close stdin
# unblocks tools/list without waiting for the full idle timeout.
_STDIN_EOF_MS = int(os.environ.get("MCP_STDIO_STDIN_EOF_DELAY_MS", "0"))


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


def _drain_pipe(pipe, chunks: list[bytes]) -> None:
    try:
        while True:
            block = pipe.read(4096)
            if not block:
                break
            chunks.append(block)
    except Exception:
        pass


def main() -> int:
    argv = sys.argv[1:]
    check_only = False
    if argv and argv[0] == "--check":
        check_only = True
        argv = argv[1:]
    if len(argv) < 1:
        print(
            "usage: mcp_stdio_docker_tools_list.py [--check] [docker run extra args ...] <image>",
            file=sys.stderr,
        )
        return 2
    image = argv[-1]
    extra = argv[:-1]
    cmd = ["docker", "run", "-i", "--rm", "-e", "MCP_TRANSPORT=stdio", *extra, image]
    _log("--- mcp_stdio_docker_tools_list: docker command ---")
    _log(" ".join(cmd))
    _log("--- stdin (MCP lines) ---")
    _log(INPUT_BYTES.decode())

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None
    proc.stdin.write(INPUT_BYTES)
    proc.stdin.flush()
    if _STDIN_EOF_MS > 0:
        time.sleep(_STDIN_EOF_MS / 1000.0)
        try:
            proc.stdin.close()
        except (BrokenPipeError, OSError, ValueError):
            pass
    # Do not close stdin yet: Docker Desktop / some MCP stacks only process the
    # request batch after stdin EOF; others need stdin open while responses flush.
    # Closing immediately races with delivery (stdio tools/call tests keep stdin open).

    out_chunks: list[bytes] = []
    err_chunks: list[bytes] = []
    assert proc.stdout is not None and proc.stderr is not None
    t_out = threading.Thread(target=_drain_pipe, args=(proc.stdout, out_chunks), daemon=True)
    t_err = threading.Thread(target=_drain_pipe, args=(proc.stderr, err_chunks), daemon=True)
    t_out.start()
    t_err.start()

    deadline = time.monotonic() + TIMEOUT
    tools_marker = b'"tools"'

    def _combined() -> bytes:
        return b"".join(out_chunks) + b"".join(err_chunks)

    while time.monotonic() < deadline:
        if tools_marker in _combined():
            break
        if proc.poll() is not None:
            # Process exited; drain threads may still be flushing piped stdout.
            for _ in range(40):
                if tools_marker in _combined():
                    break
                time.sleep(0.05)
            break
        time.sleep(0.05)

    try:
        proc.stdin.close()
    except (BrokenPipeError, OSError, ValueError):
        pass

    # Stop docker run so the test can finish (server may not exit on stdin EOF).
    try:
        proc.terminate()
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)

    t_out.join(timeout=15)
    t_err.join(timeout=15)

    stdout = b"".join(out_chunks)
    stderr = b"".join(err_chunks)
    full = stdout + stderr

    if tools_marker not in full:
        print(
            f"mcp_stdio_docker_tools_list: TIMEOUT after {TIMEOUT}s (image={image}) — incomplete response",
            file=sys.stderr,
        )

    if DUMP_IO:
        _log("--- stdout ---")
        _log(stdout.decode(errors="replace"))
        _log("--- stderr ---")
        _log(stderr.decode(errors="replace"))

    ok = tools_marker in full
    if check_only:
        return 0 if ok else 1

    sys.stdout.buffer.write(stdout)
    if tools_marker not in stdout and tools_marker in stderr:
        sys.stdout.buffer.write(stderr)
    # Non-zero when tools/list never appeared (callers may use --check to avoid
    # bash capturing multi‑MB JSON, which truncates on some hosts and breaks grep).
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
