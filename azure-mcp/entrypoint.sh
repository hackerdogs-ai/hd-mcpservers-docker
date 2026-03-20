#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec python3 -u -c "
import subprocess, sys, time, threading, os, signal

proc = subprocess.Popen(
    ['azmcp', 'server', 'start', '--transport', 'stdio'],
    stdin=subprocess.PIPE, stdout=sys.stdout.buffer, stderr=sys.stderr
)

def forward_stdin():
    try:
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                time.sleep(5)
                break
            proc.stdin.write(line)
            proc.stdin.flush()
    except:
        pass
    finally:
        try:
            proc.stdin.close()
        except:
            pass

t = threading.Thread(target=forward_stdin, daemon=True)
t.start()
proc.wait()
sys.exit(proc.returncode)
"
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8627} -- azmcp server start --transport stdio
fi
