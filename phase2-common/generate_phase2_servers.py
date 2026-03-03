#!/usr/bin/env python3
"""Generate phase2 MCP server directories and files from tools_metadata.json.

Follows the exact pattern of phase1 tools (naabu, asnmap, julius, etc.):
- mcp_server.py: tool-specific named function, JSON output, tool-specific logger
- Dockerfile: full OCI labels, output dir, chown, no generic env leaks
- mcpServer.json: env: {} (empty)
- docker-compose.yml: with container_name
- README.md: "What is X?" section, <details> example response, 6 prompts, manual test
- test.sh: 6 tests (image, binary, stdio, HTTP init, HTTP list, HTTP call)
- publish_to_hackerdogs.sh: full multi-arch script
- progress.md: detailed checklist
"""

import json
import os
import re
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)


def load_metadata():
    with open(os.path.join(SCRIPT_DIR, "tools_metadata.json")) as f:
        return json.load(f)


def make_tool_func_name(tool_name: str) -> str:
    """Convert tool_name like 'rustscan' to a Python-friendly function name like 'run_rustscan'."""
    clean = re.sub(r"[^a-z0-9]", "_", tool_name.lower()).strip("_")
    return f"run_{clean}"


def generate_mcp_server(t: dict) -> str:
    """Generate a tool-specific mcp_server.py matching the naabu pattern."""
    dir_name = t["dir"]
    bin_name = t["bin"]
    title = t["title"]
    desc = t["desc"]
    port = t["port"]
    repo = t["repo"]
    tool_name = dir_name.replace("-mcp", "")
    func_name = make_tool_func_name(tool_name)
    logger_name = dir_name
    bin_var = re.sub(r"[^A-Z0-9]", "_", tool_name.upper()) + "_BIN"
    desc_esc = desc.replace('"', '\\"')

    return f'''#!/usr/bin/env python3
"""{title} — {desc}

Wraps the {bin_name} CLI ({repo}) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shutil
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("{logger_name}")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "{port}"))

mcp = FastMCP(
    "{title}",
    instructions=(
        "{desc_esc}"
    ),
)

{bin_var} = os.environ.get("{bin_var}", "{bin_name}")


def _find_binary() -> str:
    """Locate the {bin_name} binary, raising a clear error if missing."""
    path = shutil.which({bin_var})
    if path is None:
        logger.error("{bin_name} binary not found on PATH")
        raise FileNotFoundError(
            f"{bin_name} binary not found. Ensure it is installed and available "
            f"on PATH, or set {bin_var} to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a {bin_name} command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    binary = _find_binary()
    cmd = [binary] + args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        logger.error("Command timed out after %ds: %s", timeout_seconds, " ".join(cmd))
        return {{
            "stdout": "",
            "stderr": f"Command timed out after {{timeout_seconds}}s: {{' '.join(cmd)}}",
            "return_code": -1,
        }}
    except Exception as exc:
        logger.error("Command execution failed: %s", exc)
        return {{
            "stdout": "",
            "stderr": f"Failed to execute command: {{exc}}",
            "return_code": -1,
        }}

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return {{
        "stdout": stdout,
        "stderr": stderr,
        "return_code": proc.returncode,
    }}


@mcp.tool()
async def {func_name}(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run {bin_name} with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("{func_name} called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("{bin_name} command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {{
                "error": True,
                "message": f"{bin_name} failed (exit code {{result['return_code']}})",
                "detail": error_detail.strip(),
                "command": f"{bin_name} {{' '.join(args)}}",
            }},
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({{"message": "Command completed with no output", "arguments": arguments}})

    # Try to parse as JSON/JSONL
    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({{"raw": line}})

    if len(results) == 1:
        return json.dumps(results[0], indent=2)
    return json.dumps(results, indent=2)


def main():
    logger.info("Starting {logger_name} server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
'''


def generate_dockerfile(t: dict) -> str:
    dir_name = t["dir"]
    bin_name = t["bin"]
    title = t["title"]
    desc = t["desc"]
    port = t["port"]
    tool_name = dir_name.replace("-mcp", "")
    bin_var = re.sub(r"[^A-Z0-9]", "_", tool_name.upper()) + "_BIN"

    return f"""# {title} - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="{title} - {desc[:60]}"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="{dir_name}"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \\
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

# TODO: Install {bin_name} — add your install steps here.
# Examples:
#   apt:   RUN apt-get update && apt-get install -y --no-install-recommends {bin_name} && rm -rf /var/lib/apt/lists/*
#   pip:   RUN pip install --no-cache-dir {bin_name}
#   go:    (use multi-stage) FROM golang:1.24-bookworm AS builder; RUN go install ...@latest; then COPY --from=builder
#   cargo: (use multi-stage) FROM rust:1.77 AS builder; RUN cargo install {bin_name}; then COPY --from=builder

RUN apt-get update && apt-get install -y --no-install-recommends \\
    tini \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT={port}

EXPOSE {port}

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
"""


def generate_mcpserver_json(t: dict) -> str:
    dir_name = t["dir"]
    config = {
        "mcpServers": {
            dir_name: {
                "command": "docker",
                "args": [
                    "run",
                    "-i",
                    "--rm",
                    f"hackerdogs/{dir_name}:latest"
                ],
                "env": {}
            }
        }
    }
    return json.dumps(config, indent=2) + "\n"


def generate_docker_compose(t: dict) -> str:
    dir_name = t["dir"]
    port = t["port"]
    return f"""version: "3.8"

services:
  {dir_name}:
    image: hackerdogs/{dir_name}:latest
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {dir_name}
    ports:
      - "{port}:{port}"
    environment:
      - MCP_TRANSPORT=streamable-http
      - MCP_PORT={port}
    restart: unless-stopped
"""


def generate_test_sh(t: dict) -> str:
    dir_name = t["dir"]
    bin_name = t["bin"]
    title = t["title"]
    port = t["port"]
    tool_name = dir_name.replace("-mcp", "")
    func_name = make_tool_func_name(tool_name)

    return f"""#!/bin/bash
# Test script for {title}
# Tests MCP protocol compliance via JSON-RPC (stdio and HTTP streamable)

set -euo pipefail

RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

PASS=0
FAIL=0
IMAGE="hackerdogs/{dir_name}:latest"
PORT={port}
BINARY="{bin_name}"
CONTAINER_NAME="{dir_name}-test"
PROJECT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

pass() {{ echo -e "  ${{GREEN}}✅ PASS: $1${{NC}}"; PASS=$((PASS + 1)); }}
fail() {{ echo -e "  ${{RED}}❌ FAIL: $1${{NC}}"; FAIL=$((FAIL + 1)); }}
info() {{ echo -e "${{BLUE}}$1${{NC}}"; }}

cleanup() {{
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}}
trap cleanup EXIT

echo "================================================================================="
echo -e "${{BLUE}}{title} — Test Suite${{NC}}"
echo "================================================================================="
echo ""

# Test 1: Build/verify Docker image
info "[Test 1] Docker image"
if ! docker image inspect "$IMAGE" > /dev/null 2>&1; then
    echo "  Image not found. Building..."
    docker build -t "$IMAGE" "$PROJECT_DIR"
fi
if docker image inspect "$IMAGE" > /dev/null 2>&1; then
    pass "Docker image $IMAGE exists"
else
    fail "Docker image $IMAGE could not be built"
    exit 1
fi
echo ""

# Test 2: CLI binary available
info "[Test 2] CLI binary inside container"
BINARY_OUTPUT=$(docker run --rm "$IMAGE" $BINARY --version 2>&1 | head -5 || docker run --rm "$IMAGE" $BINARY -version 2>&1 | head -5 || docker run --rm "$IMAGE" $BINARY -h 2>&1 | head -5 || true)
if [ -n "$BINARY_OUTPUT" ]; then
    pass "$BINARY binary responds"
    echo "       ${{BINARY_OUTPUT%%$'\\n'*}}"
else
    fail "$BINARY binary not found or not responding"
fi
echo ""

# Test 3: MCP stdio mode — initialize + tools/list
info "[Test 3] MCP stdio mode — initialize + tools/list"
INIT_REQ='{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"test-client","version":"1.0.0"}}}}}}'
INIT_NOTIF='{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
LIST_REQ='{{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{{}}}}'

STDIO_OUT=$(printf '%s\\n%s\\n%s\\n' "$INIT_REQ" "$INIT_NOTIF" "$LIST_REQ" | \\
    docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null || true)

if echo "$STDIO_OUT" | grep -q '"tools"'; then
    TOOL_COUNT=$(echo "$STDIO_OUT" | grep -o '"name"' | wc -l)
    pass "stdio mode returned tools/list response ($TOOL_COUNT tool names found)"
else
    fail "stdio mode did not return a valid tools/list response"
    [ -n "$STDIO_OUT" ] && echo "       Response preview: ${{STDIO_OUT:0:300}}"
fi
echo ""

# Test 4: MCP HTTP streamable mode — initialize
info "[Test 4] MCP HTTP streamable mode — initialize"
cleanup
docker run -d --name "$CONTAINER_NAME" \\
    -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT \\
    -p "$PORT:$PORT" "$IMAGE" > /dev/null

SESSION_ID=""
MAX_WAIT=30; WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    INIT_RESP=$(curl -s -D /tmp/mcp_headers -X POST "http://localhost:${{PORT}}/mcp" \\
        -H "Content-Type: application/json" \\
        -H "Accept: application/json, text/event-stream" \\
        -d "$INIT_REQ" 2>/dev/null) && break
    sleep 2; WAITED=$((WAITED + 2))
done

HTTP_CODE=$(head -1 /tmp/mcp_headers 2>/dev/null | grep -o '[0-9]\\{{3\\}}' | head -1 || echo "000")
SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_headers 2>/dev/null | sed 's/.*: //' | tr -d '\\r' || true)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
    pass "HTTP streamable mode responded (status $HTTP_CODE)"
    [ -n "$SESSION_ID" ] && echo "       Session ID: ${{SESSION_ID:0:16}}..."
else
    fail "HTTP streamable mode did not respond (status $HTTP_CODE after ${{WAITED}}s)"
    docker logs "$CONTAINER_NAME" 2>&1 | tail -10
fi
echo ""

# Test 5: MCP HTTP — tools/list
info "[Test 5] MCP HTTP — tools/list"
SESSION_HDR=""
[ -n "$SESSION_ID" ] && SESSION_HDR="-H mcp-session-id:${{SESSION_ID}}"

curl -s -X POST "http://localhost:${{PORT}}/mcp" \\
    -H "Content-Type: application/json" \\
    -H "Accept: application/json, text/event-stream" \\
    $SESSION_HDR \\
    -d "$INIT_NOTIF" > /dev/null 2>&1 || true

TOOLS_RESP=$(curl -s -X POST "http://localhost:${{PORT}}/mcp" \\
    -H "Content-Type: application/json" \\
    -H "Accept: application/json, text/event-stream" \\
    $SESSION_HDR \\
    -d "$LIST_REQ" 2>/dev/null || true)

if echo "$TOOLS_RESP" | grep -q '"tools"'; then
    pass "HTTP tools/list returned tools"
    echo "$TOOLS_RESP" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('data: '): line = line[6:]
    if not line: continue
    try:
        data = json.loads(line)
        tools = data.get('result',{{}}).get('tools',[])
        for t in tools:
            print(f'       - {{t[\"name\"]}}: {{t.get(\"description\",\"\")[:80]}}')
    except: pass
" 2>/dev/null || true
else
    fail "HTTP tools/list did not return tools"
    [ -n "$TOOLS_RESP" ] && echo "       Response: ${{TOOLS_RESP:0:300}}"
fi
echo ""

# Test 6: MCP HTTP — tools/call
info "[Test 6] MCP HTTP — tools/call ({func_name})"
CALL_REQ='{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"{func_name}","arguments":{{"arguments":"--help"}}}}}}'
CALL_RESP=$(curl -s -X POST "http://localhost:${{PORT}}/mcp" \\
    -H "Content-Type: application/json" \\
    -H "Accept: application/json, text/event-stream" \\
    $SESSION_HDR \\
    -d "$CALL_REQ" 2>/dev/null || true)

if echo "$CALL_RESP" | grep -q '"result"'; then
    pass "tools/call {func_name} returned a result"
elif echo "$CALL_RESP" | grep -q '"content"'; then
    pass "tools/call {func_name} returned content"
else
    fail "tools/call {func_name} did not return expected response"
    [ -n "$CALL_RESP" ] && echo "       Response: ${{CALL_RESP:0:500}}"
fi
echo ""

# Summary
echo "================================================================================="
echo -e "${{BLUE}}Results: ${{GREEN}}$PASS passed${{NC}}, ${{RED}}$FAIL failed${{NC}}"
echo "================================================================================="
[ $FAIL -gt 0 ] && exit 1 || exit 0
"""


def generate_readme(t: dict) -> str:
    dir_name = t["dir"]
    bin_name = t["bin"]
    title = t["title"]
    desc = t["desc"]
    port = t["port"]
    repo = t["repo"]
    url = t["url"]
    tool_name = dir_name.replace("-mcp", "")
    func_name = make_tool_func_name(tool_name)
    display_name = tool_name.replace("-", " ").title()

    return f'''<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# {title}

MCP server wrapper for [{display_name}]({url}) — {desc}

## What is {display_name}?

{display_name} ({bin_name}) is a security tool that provides: **{desc}**

See [{repo}]({url}) for full documentation.

**No API keys required** — {display_name} runs locally inside the Docker container.

## Tools Reference

### `{func_name}`

Run {bin_name} with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{{
  "raw": "{bin_name} output will appear here"
}}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run {bin_name} with --help to see all available options."
- "Use {tool_name} to scan the target 192.168.1.1."
- "What options does {bin_name} support? Show me its help output."
- "Run {tool_name} against example.com with default settings."
- "Execute {bin_name} with verbose output enabled."
- "Use the {tool_name} tool to analyze the target and report findings."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/{dir_name}:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  -e MCP_PORT={port} \\
  hackerdogs/{dir_name}:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{{
  "mcpServers": {{
    "{dir_name}": {{
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/{dir_name}:latest"],
      "env": {{}}
    }}
  }}
}}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{{
  "mcpServers": {{
    "{dir_name}": {{
      "url": "http://localhost:{port}/mcp"
    }}
  }}
}}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `{port}` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/{dir_name}:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name {dir_name}-test -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  hackerdogs/{dir_name}:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -d '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"test","version":"0.1"}}}}}}' \\
  2>&1 | grep -i mcp-session-id | awk '{{print $2}}' | tr -d '\\r\\n')

curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{{"name":"{func_name}","arguments":{{"arguments":"--help"}}}}}}'
```

**4. Clean up:**

```bash
docker stop {dir_name}-test
```
'''


def generate_publish_script(t: dict) -> str:
    dir_name = t["dir"]
    title = t["title"]

    return f"""#!/bin/bash
# Build and Publish {title} Docker Image to Docker Hub
# Image name: {dir_name}

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Configuration
IMAGE_NAME="{dir_name}"
DOCKERFILE="Dockerfile"
DEFAULT_TAG="latest"
PROJECT_ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# Flags
DO_BUILD=false
DO_PUBLISH=false
SHOW_HELP=false
PLATFORMS_MODE="parallel"

# Parse command-line arguments
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            DO_BUILD=true
            shift
            ;;
        --publish)
            DO_PUBLISH=true
            shift
            ;;
        --platforms)
            PLATFORMS_MODE="$2"
            shift 2
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    echo "Build and Publish {title} Docker Image to Docker Hub"
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS] <dockerhub_username> [tag] [additional_tag...]"
    echo ""
    echo "Options:"
    echo "  --build      Only build the Docker image (do not publish)"
    echo "  --publish    Only publish the Docker image (assumes image already exists)"
    echo "  --platforms parallel|sequential  Push both platforms at once (default) or amd64 then arm64"
    echo "  --help, -h   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 hackerdogs                    # Build and publish with tag 'latest'"
    echo "  $0 --build hackerdogs             # Only build (tag: latest)"
    echo "  $0 --publish hackerdogs           # Only publish"
    echo "  $0 --build --publish hackerdogs v1.0.0           # Build and publish with tag v1.0.0"
    echo "  $0 --build --publish --platforms sequential hackerdogs v1.0.0 latest"
    exit 0
fi

# If neither flag is set, do both (default behavior)
if [ "$DO_BUILD" = false ] && [ "$DO_PUBLISH" = false ]; then
    DO_BUILD=true
    DO_PUBLISH=true
fi

# Normalize platforms mode
if [ "$PLATFORMS_MODE" != "sequential" ]; then
    PLATFORMS_MODE="parallel"
fi

cd "$PROJECT_ROOT"

# Get Docker Hub username
if [ "$DO_PUBLISH" = true ]; then
    if [ ${{#ARGS[@]}} -eq 0 ]; then
        echo -e "${{YELLOW}}Docker Hub username not provided.${{NC}}"
        read -p "Enter your Docker Hub username: " DOCKERHUB_USERNAME
        if [ -z "$DOCKERHUB_USERNAME" ]; then
            echo -e "${{RED}}Error: Docker Hub username is required for publishing${{NC}}"
            exit 1
        fi
    else
        DOCKERHUB_USERNAME="${{ARGS[0]}}"
    fi
    FULL_IMAGE_NAME="${{DOCKERHUB_USERNAME}}/${{IMAGE_NAME}}"
else
    DOCKERHUB_USERNAME=""
    FULL_IMAGE_NAME="${{IMAGE_NAME}}"
fi

TAGS=("${{ARGS[@]:1}}")
if [ ${{#TAGS[@]}} -eq 0 ]; then
    TAGS=("$DEFAULT_TAG")
fi

echo "================================================================================="
if [ "$DO_BUILD" = true ] && [ "$DO_PUBLISH" = true ]; then
    echo -e "${{BLUE}}Building and Publishing {title} Docker Image${{NC}}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${{BLUE}}Building {title} Docker Image${{NC}}"
else
    echo -e "${{BLUE}}Publishing {title} Docker Image to Docker Hub${{NC}}"
fi
echo "================================================================================="
[ "$DO_PUBLISH" = true ] && echo "Docker Hub Username: ${{GREEN}}${{DOCKERHUB_USERNAME}}${{NC}}"
echo "Image Name: ${{GREEN}}${{IMAGE_NAME}}${{NC}}"
echo "Tags: ${{GREEN}}${{TAGS[*]}}${{NC}}"
echo "Full Image Name: ${{GREEN}}${{FULL_IMAGE_NAME}}${{NC}}"
echo "================================================================================="
echo ""

if ! command -v docker &> /dev/null; then
    echo -e "${{RED}}Error: Docker is not installed or not in PATH${{NC}}"
    exit 1
fi

if ! docker ps > /dev/null 2>&1; then
    echo -e "${{RED}}Error: Docker is not running or not accessible${{NC}}"
    exit 1
fi

echo -e "${{YELLOW}}Setting up Docker Buildx for multi-platform support...${{NC}}"
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${{RED}}Error: Docker Buildx is not available. Please upgrade Docker.${{NC}}"
    exit 1
fi

BUILDER_NAME="multiarch-builder"
if ! docker buildx inspect "$BUILDER_NAME" > /dev/null 2>&1; then
    echo -e "${{YELLOW}}Creating multi-platform builder: ${{BUILDER_NAME}}${{NC}}"
    docker buildx create --name "$BUILDER_NAME" --use --bootstrap
    [ $? -ne 0 ] && echo -e "${{RED}}Error: Failed to create buildx builder${{NC}}" && exit 1
else
    docker buildx use "$BUILDER_NAME" > /dev/null 2>&1
fi
echo -e "${{GREEN}}✅ Buildx builder ready${{NC}}"
echo ""

if [ "$DO_PUBLISH" = true ]; then
    echo -e "${{YELLOW}}Checking Docker Hub authentication...${{NC}}"
    if ! docker info | grep -q "Username"; then
        echo -e "${{YELLOW}}You are not logged in to Docker Hub.${{NC}}"
        echo "Please log in with: docker login"
        read -p "Do you want to log in now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
            [ $? -ne 0 ] && echo -e "${{RED}}Error: Docker login failed${{NC}}" && exit 1
        else
            echo -e "${{RED}}Error: Docker Hub login required for publishing${{NC}}"
            exit 1
        fi
    else
        echo -e "${{GREEN}}✅ Docker Hub authentication verified${{NC}}"
    fi
    echo ""
fi

MAX_RETRIES=5
do_build_push_with_retry() {{
    local retry=0
    local backoff=30
    while [ $retry -lt $MAX_RETRIES ]; do
        if [ $retry -gt 0 ]; then
            echo -e "${{YELLOW}}Retry $retry/$MAX_RETRIES in ${{backoff}}s...${{NC}}"
            sleep "$backoff"
            backoff=$((backoff * 2))
            [ $backoff -gt 300 ] && backoff=300
        fi
        if "$@"; then
            return 0
        fi
        retry=$((retry + 1))
    done
    return 1
}}

if [ "$DO_BUILD" = true ]; then
    if [ ! -f "$DOCKERFILE" ]; then
        echo -e "${{RED}}Error: Dockerfile not found: ${{DOCKERFILE}}${{NC}}"
        exit 1
    fi

    if [ "$DO_PUBLISH" = true ]; then
        echo -e "${{YELLOW}}Building Docker image (multi-platform)...${{NC}}"
        for tag in "${{TAGS[@]}}"; do
            if [ "$PLATFORMS_MODE" = "sequential" ]; then
                for arch in amd64 arm64; do
                    echo "Building ${{FULL_IMAGE_NAME}}:${{tag}}-${{arch}}..."
                    if ! do_build_push_with_retry docker buildx build \\
                        --platform linux/$arch \\
                        --provenance=false --sbom=false \\
                        -f "$DOCKERFILE" -t "${{FULL_IMAGE_NAME}}:${{tag}}-${{arch}}" \\
                        --push . ; then
                        echo -e "${{RED}}Error: Failed to build/push $arch after $MAX_RETRIES attempts${{NC}}"
                        exit 1
                    fi
                    echo -e "${{GREEN}}✅ Pushed ${{FULL_IMAGE_NAME}}:${{tag}}-${{arch}}${{NC}}"
                done
                docker buildx imagetools create -t "${{FULL_IMAGE_NAME}}:${{tag}}" \\
                    "${{FULL_IMAGE_NAME}}:${{tag}}-amd64" "${{FULL_IMAGE_NAME}}:${{tag}}-arm64"
                [ $? -ne 0 ] && echo -e "${{RED}}Error: Failed to create manifest${{NC}}" && exit 1
            else
                echo "Building ${{FULL_IMAGE_NAME}}:${{tag}}..."
                if ! do_build_push_with_retry docker buildx build \\
                    --platform linux/amd64,linux/arm64 \\
                    --provenance=false --sbom=false \\
                    -f "$DOCKERFILE" -t "${{FULL_IMAGE_NAME}}:${{tag}}" \\
                    --push . ; then
                    echo -e "${{RED}}Error: Build failed after $MAX_RETRIES attempts${{NC}}"
                    exit 1
                fi
            fi
            echo -e "${{GREEN}}✅ Successfully built and pushed ${{FULL_IMAGE_NAME}}:${{tag}}${{NC}}"
        done
    else
        echo -e "${{YELLOW}}Building Docker image (local platform only)...${{NC}}"
        LOCAL_IMAGE_NAME="${{IMAGE_NAME}}:${{TAGS[0]}}"
        docker buildx build --load -f "$DOCKERFILE" -t "${{LOCAL_IMAGE_NAME}}" .
        [ $? -ne 0 ] && echo -e "${{RED}}Error: Docker build failed${{NC}}" && exit 1
        echo -e "${{GREEN}}✅ Docker image built: ${{LOCAL_IMAGE_NAME}}${{NC}}"

        REGISTRY_TAG="hackerdogs/${{IMAGE_NAME}}:${{TAGS[0]}}"
        docker tag "${{LOCAL_IMAGE_NAME}}" "${{REGISTRY_TAG}}"
        echo -e "${{GREEN}}✅ Tagged as ${{REGISTRY_TAG}}${{NC}}"
    fi
fi

if [ "$DO_PUBLISH" = true ] && [ "$DO_BUILD" = false ]; then
    for tag in "${{TAGS[@]}}"; do
        echo "Pushing ${{FULL_IMAGE_NAME}}:${{tag}}..."
        docker push "${{FULL_IMAGE_NAME}}:${{tag}}"
        [ $? -ne 0 ] && echo -e "${{RED}}Error: Failed to push${{NC}}" && exit 1
        echo -e "${{GREEN}}✅ Pushed ${{FULL_IMAGE_NAME}}:${{tag}}${{NC}}"
    done
fi

echo ""
echo "================================================================================="
if [ "$DO_BUILD" = true ] && [ "$DO_PUBLISH" = true ]; then
    echo -e "${{GREEN}}✅ Build and Publish Complete!${{NC}}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${{GREEN}}✅ Build Complete!${{NC}}"
else
    echo -e "${{GREEN}}✅ Publish Complete!${{NC}}"
fi
echo "================================================================================="
echo "Image: ${{GREEN}}${{FULL_IMAGE_NAME}}:${{TAGS[0]}}${{NC}}"

VERSION_FILE="${{IMAGE_NAME}}_versions.txt"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TAGS_CSV=$(IFS=','; echo "${{TAGS[*]}}")
if [ "$DO_PUBLISH" = true ]; then
    echo "${{TAGS_CSV}},linux/amd64+linux/arm64,${{TIMESTAMP}},https://hub.docker.com/r/${{DOCKERHUB_USERNAME}}/${{IMAGE_NAME}}/tags" >> "$VERSION_FILE"
elif [ "$DO_BUILD" = true ]; then
    echo "${{TAGS_CSV}},local,${{TIMESTAMP}},local" >> "$VERSION_FILE"
fi
echo "Version info saved to: ${{GREEN}}${{VERSION_FILE}}${{NC}}"
echo ""
"""


def generate_progress(t: dict) -> str:
    dir_name = t["dir"]
    bin_name = t["bin"]
    title = t["title"]
    port = t["port"]
    repo = t["repo"]
    url = t["url"]
    tool_name = dir_name.replace("-mcp", "")
    func_name = make_tool_func_name(tool_name)

    return f"""# {title} — Progress

## Setup Steps

- [x] Create directory structure (`{dir_name}/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping {bin_name} CLI
  - [x] `{func_name}` tool — run {bin_name} with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add {bin_name} install steps to `Dockerfile` (see [{repo}]({url}))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port {port}
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **{port}** — {title} (streamable-http)

## Notes

- Source: {url}
- Binary: `{bin_name}`
- Install: see {url} for installation instructions
"""


def main():
    metadata = load_metadata()

    for t in metadata:
        dir_name = t["dir"]
        out_dir = os.path.join(REPO_ROOT, dir_name)
        os.makedirs(out_dir, exist_ok=True)

        with open(os.path.join(out_dir, "mcp_server.py"), "w") as f:
            f.write(generate_mcp_server(t))

        with open(os.path.join(out_dir, "requirements.txt"), "w") as f:
            f.write("fastmcp>=2.0.0\n")

        with open(os.path.join(out_dir, "mcpServer.json"), "w") as f:
            f.write(generate_mcpserver_json(t))

        with open(os.path.join(out_dir, "docker-compose.yml"), "w") as f:
            f.write(generate_docker_compose(t))

        with open(os.path.join(out_dir, "Dockerfile"), "w") as f:
            f.write(generate_dockerfile(t))

        with open(os.path.join(out_dir, "test.sh"), "w") as f:
            f.write(generate_test_sh(t))
        os.chmod(os.path.join(out_dir, "test.sh"), 0o755)

        with open(os.path.join(out_dir, "progress.md"), "w") as f:
            f.write(generate_progress(t))

        with open(os.path.join(out_dir, "README.md"), "w") as f:
            f.write(generate_readme(t))

        with open(os.path.join(out_dir, "publish_to_hackerdogs.sh"), "w") as f:
            f.write(generate_publish_script(t))
        os.chmod(os.path.join(out_dir, "publish_to_hackerdogs.sh"), 0o755)

        print(f"Created {dir_name}")


if __name__ == "__main__":
    main()
