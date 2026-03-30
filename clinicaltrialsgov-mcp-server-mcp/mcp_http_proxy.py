#!/usr/bin/env python3
import json
import os
import select
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

sessions = {}
lock = threading.Lock()

_INIT_TIMEOUT = float(os.environ.get("MCP_PROXY_INIT_TIMEOUT", "360"))
_REQUEST_TIMEOUT = float(os.environ.get("MCP_PROXY_REQUEST_TIMEOUT", "600"))
_KEEPALIVE_INTERVAL = float(os.environ.get("MCP_PROXY_KEEPALIVE_INTERVAL", "10"))

def read_jsonrpc_line(proc, timeout, keepalive_wfile=None):
    buf = b""
    deadline = time.time() + timeout
    last_keepalive = time.time()
    try:
        out_buf = proc.stdout.buffer
    except AttributeError:
        out_buf = None
    if out_buf is None:
        return None

    while time.time() < deadline:
        remaining = max(0.0, deadline - time.time())
        if remaining <= 0:
            break
        sel_t = min(0.5, remaining)
        r, _, _ = select.select([out_buf], [], [], sel_t)
        now = time.time()
        if not r:
            if (
                keepalive_wfile is not None
                and _KEEPALIVE_INTERVAL > 0
                and (now - last_keepalive) >= _KEEPALIVE_INTERVAL
            ):
                keepalive_wfile.write(
                    b": mcp-proxy waiting for stdio child (large JSON-RPC line)\n\n"
                )
                keepalive_wfile.flush()
                last_keepalive = now
            continue

        chunk = out_buf.read1(65536)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line_b, _, buf = buf.partition(b"\n")
            line = line_b.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                json.loads(line)
                return line
            except (json.JSONDecodeError, ValueError):
                sys.stdout.write(f"[child-stdout-discarded] {line}\n")
                sys.stdout.flush()
                continue
    return None

class StdioSession:
    def __init__(self, cmd):
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.lock = threading.Lock()
        self.id = uuid.uuid4().hex
        threading.Thread(target=self._drain_stderr, daemon=True).start()

    def _drain_stderr(self):
        try:
            if self.proc.stderr is not None:
                for line in iter(self.proc.stderr.readline, ""):
                    sys.stdout.write(f"[child-stderr] {line}")
                    sys.stdout.flush()
        except Exception:
            pass

    def send(self, msg):
        with self.lock:
            try:
                self.proc.stdin.write(msg + "\n")
                self.proc.stdin.flush()
            except BrokenPipeError:
                return None

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=3)
        except Exception:
            self.proc.kill()

class MCPHandler(BaseHTTPRequestHandler):
    cmd = None

    def log_message(self, format, *args):
        pass

    def _jsonrpc_error_line(self, req_id, message):
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32000, "message": message},
        }
        return json.dumps(payload, separators=(",", ":"))

    def do_POST(self):
        if self.path != "/mcp":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        session_id = self.headers.get("mcp-session-id", "")

        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        method = msg.get("method", "")
        req_id = msg.get("id")

        if method == "initialize":
            session = StdioSession(self.cmd)
            session.send(body)
            with lock:
                sessions[session.id] = session
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("mcp-session-id", session.id)
                self.end_headers()
                self.wfile.flush()
                resp_line = read_jsonrpc_line(
                    session.proc, _INIT_TIMEOUT, self.wfile
                )
                if resp_line:
                    self.wfile.write(
                        f"event: message\ndata: {resp_line}\n\n".encode()
                    )
                    self.wfile.flush()
                else:
                    err = self._jsonrpc_error_line(
                        req_id,
                        "mcp proxy: timeout waiting for initialize response on stdio",
                    )
                    self.wfile.write(
                        f"event: message\ndata: {err}\n\n".encode()
                    )
                    self.wfile.flush()
                    with lock:
                        sessions.pop(session.id, None)
                    session.close()
            except BrokenPipeError:
                with lock:
                    sessions.pop(session.id, None)
                session.close()
            return

        if method == "notifications/initialized":
            if session_id and session_id in sessions:
                sessions[session_id].send(body)
            self.send_response(202)
            self.end_headers()
            return

        if session_id and session_id in sessions:
            session = sessions[session_id]
            session.send(body)
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("mcp-session-id", session_id)
                self.end_headers()
                self.wfile.flush()
                resp_line = read_jsonrpc_line(
                    session.proc, _REQUEST_TIMEOUT, self.wfile
                )
                if resp_line:
                    self.wfile.write(
                        f"event: message\ndata: {resp_line}\n\n".encode()
                    )
                    self.wfile.flush()
                else:
                    err = self._jsonrpc_error_line(
                        req_id,
                        "mcp proxy: timeout waiting for stdio response (e.g. tools/list too slow)",
                    )
                    self.wfile.write(
                        f"event: message\ndata: {err}\n\n".encode()
                    )
                    self.wfile.flush()
            except BrokenPipeError:
                pass
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing or invalid mcp-session-id")

    def do_DELETE(self):
        session_id = self.headers.get("mcp-session-id", "")
        if session_id and session_id in sessions:
            sessions[session_id].close()
            del sessions[session_id]
        self.send_response(200)
        self.end_headers()

def main():
    argv = sys.argv[1:]
    port = 8000
    host = "0.0.0.0"
    cmd_start = 0
    if "--" in argv:
        pre = argv[: argv.index("--")]
        cmd = argv[argv.index("--") + 1 :]
    else:
        pre = []
        cmd = argv
        for i, a in enumerate(argv):
            if a == "--port" and i + 1 < len(argv):
                port = int(argv[i + 1])
                cmd_start = i + 2
            elif a == "--host" and i + 1 < len(argv):
                host = argv[i + 1]
                cmd_start = i + 2
        cmd = argv[cmd_start:]

    for i, a in enumerate(pre):
        if a == "--port" and i + 1 < len(pre):
            port = int(pre[i + 1])
        elif a == "--host" and i + 1 < len(pre):
            host = pre[i + 1]

    if not cmd:
        print(
            "Usage: mcp_http_proxy.py [--port PORT] [--host HOST] -- command [args...]",
            file=sys.stderr,
        )
        sys.exit(1)

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    MCPHandler.cmd = cmd
    server = ThreadingHTTPServer((host, port), MCPHandler)
    print(f"[mcp-proxy] Listening on {host}:{port}/mcp", flush=True)
    print(f"[mcp-proxy] Wrapping: {' '.join(cmd)}", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    main()