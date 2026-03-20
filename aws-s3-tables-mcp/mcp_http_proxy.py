#!/usr/bin/env python3
"""
Stateful MCP stdio-to-HTTP proxy.
Wraps any stdio MCP server with a streamable-http endpoint at /mcp.
Maintains a single long-lived stdio process with session support.

Usage: python mcp_http_proxy.py --port 8600 -- command arg1 arg2
"""
import argparse, json, subprocess, sys, threading, time, uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import StringIO

sessions = {}
lock = threading.Lock()


class StdioSession:
    def __init__(self, cmd):
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1
        )
        self.lock = threading.Lock()
        self.id = uuid.uuid4().hex

    def send(self, msg):
        with self.lock:
            try:
                self.proc.stdin.write(msg + "\n")
                self.proc.stdin.flush()
            except BrokenPipeError:
                return None

    def read_response(self, timeout=10):
        import select
        start = time.time()
        while time.time() - start < timeout:
            if select.select([self.proc.stdout], [], [], 0.1)[0]:
                line = self.proc.stdout.readline().strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    return line
                except (json.JSONDecodeError, ValueError):
                    continue
        return None

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=3)
        except:
            self.proc.kill()


class MCPHandler(BaseHTTPRequestHandler):
    cmd = None

    def log_message(self, format, *args):
        pass

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

        if method == "initialize":
            session = StdioSession(self.cmd)
            session.send(body)
            resp_line = session.read_response(timeout=30)
            if resp_line:
                with lock:
                    sessions[session.id] = session
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("mcp-session-id", session.id)
                self.end_headers()
                self.wfile.write(f"event: message\ndata: {resp_line}\n\n".encode())
            else:
                session.close()
                self.send_response(502)
                self.end_headers()
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
            resp_line = session.read_response(timeout=15)
            if resp_line:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("mcp-session-id", session_id)
                self.end_headers()
                self.wfile.write(f"event: message\ndata: {resp_line}\n\n".encode())
            else:
                self.send_response(504)
                self.end_headers()
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
        pre = argv[:argv.index("--")]
        cmd = argv[argv.index("--") + 1:]
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
        print("Usage: mcp_http_proxy.py [--port PORT] [--host HOST] -- command [args...]", file=sys.stderr)
        sys.exit(1)

    MCPHandler.cmd = cmd
    server = HTTPServer((host, port), MCPHandler)
    print(f"[mcp-proxy] Listening on {host}:{port}/mcp", flush=True)
    print(f"[mcp-proxy] Wrapping: {' '.join(cmd)}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
