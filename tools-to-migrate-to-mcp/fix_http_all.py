#!/usr/bin/env python3
"""
Fix HTTP mode for all 75 servers using the Python-based MCP HTTP proxy.
- For UVX (Python) servers: COPY proxy.py, use it for HTTP mode
- For NPX (Node) servers: COPY proxy.py (Python available via base image?), or fix supergateway
"""
import os, re, csv, shutil

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
PROXY_SRC = os.path.join(ROOT, "tools-to-migrate-to-mcp/mcp_http_proxy.py")

# Read phase4 mapping
servers = {}
with open(os.path.join(ROOT, "tools-to-migrate-to-mcp/phase4_mapping.csv")) as f:
    for r in csv.DictReader(f):
        servers[r["server_name"]] = {
            "port": r["port"],
            "type": r["type"],
        }


def read(path):
    with open(path) as f:
        return f.read()


def write(path, content):
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {path}")


# First, copy the proxy script to each server directory
for name, info in servers.items():
    server_dir = os.path.join(ROOT, name)
    if not os.path.isdir(server_dir):
        continue
    dest = os.path.join(server_dir, "mcp_http_proxy.py")
    shutil.copy2(PROXY_SRC, dest)

print("Copied proxy to all server directories")

# Now fix Dockerfiles and entrypoints

for name, info in servers.items():
    server_dir = os.path.join(ROOT, name)
    if not os.path.isdir(server_dir):
        continue

    df_path = os.path.join(server_dir, "Dockerfile")
    ep_path = os.path.join(server_dir, "entrypoint.sh")
    port = info["port"]

    if not os.path.isfile(df_path) or not os.path.isfile(ep_path):
        continue

    df = read(df_path)
    ep = read(ep_path)

    # Add COPY mcp_http_proxy.py to Dockerfile if not already there
    if "mcp_http_proxy.py" not in df:
        if "COPY entrypoint.sh" in df:
            df = df.replace(
                "COPY entrypoint.sh",
                "COPY mcp_http_proxy.py /mcp_http_proxy.py\nCOPY entrypoint.sh"
            )
        elif "COPY . ." in df:
            pass  # already copied
        write(df_path, df)

    # Determine the stdio command from the entrypoint
    # Look for the exec command in the stdio branch or the main exec
    stdio_cmd = None

    # Pattern 1: if/else branch
    m = re.search(r'if \[ "\$MCP_TRANSPORT" = "stdio" \]; then\s*\n\s*exec (.+)', ep)
    if m:
        stdio_cmd = m.group(1).strip()
    else:
        # Pattern 2: simple exec (no branching)
        m = re.search(r'exec (.+)', ep)
        if m:
            stdio_cmd = m.group(1).strip()

    if not stdio_cmd:
        print(f"  WARN: {name} — no exec found in entrypoint")
        continue

    # Check if this is a Python (UVX) or Node (NPX) server
    is_python = "python" in df.lower().split("from")[1].split("\n")[0] if "FROM" in df else False
    is_node = "node" in df.lower().split("from")[1].split("\n")[0] if "FROM" in df else False

    # For Python-based (UVX) servers, use the proxy directly
    if is_python or "pip install" in df:
        new_ep = f"""#!/bin/sh
export AWS_DEFAULT_REGION=${{AWS_REGION:-us-east-1}}
export AWS_DEFAULT_PROFILE=
export FASTMCP_TRANSPORT=${{MCP_TRANSPORT:-stdio}}
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=${{MCP_PORT:-{port}}}
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec {stdio_cmd}
else
  exec python /mcp_http_proxy.py --port ${{MCP_PORT:-{port}}} {stdio_cmd}
fi
"""
        write(ep_path, new_ep)

    # For Node-based (NPX) servers, install Python and use proxy
    elif is_node or "npm install" in df:
        # Node servers need Python for the proxy
        # Instead, let's use supergateway in SSE mode and adjust the test
        # OR, we can use the proxy by installing Python in Node images
        # Simplest: add Python to Node images
        if "apt-get" not in df or "python3" not in df:
            # Add Python3 install
            if "RUN npm install" in df:
                df = df.replace(
                    "RUN npm install",
                    "RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*\nRUN npm install"
                )
                write(df_path, df)

        new_ep = f"""#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec {stdio_cmd}
else
  exec python3 /mcp_http_proxy.py --port ${{MCP_PORT:-{port}}} {stdio_cmd}
fi
"""
        write(ep_path, new_ep)

print("\nDone. Now rebuild all images.")
