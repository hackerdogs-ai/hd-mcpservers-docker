<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# TestDisk MCP Server

MCP server wrapper for [Testdisk](https://github.com/cgsecurity/testdisk) — Disk partition recovery and file carving.

## What is Testdisk?

Testdisk (testdisk) is a security tool that provides: **Disk partition recovery and file carving.**

See [cgsecurity/testdisk](https://github.com/cgsecurity/testdisk) for full documentation.

**No API keys required** — Testdisk runs locally inside the Docker container.

## Tools Reference

### `run_testdisk`

Run testdisk with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "testdisk output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run testdisk with --help to see all available options."
- "Use testdisk to scan the target 192.168.1.1."
- "What options does testdisk support? Show me its help output."
- "Run testdisk against example.com with default settings."
- "Execute testdisk with verbose output enabled."
- "Use the testdisk tool to analyze the target and report findings."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/testdisk-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8283:8283 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8283 \
  hackerdogs/testdisk-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "testdisk-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/testdisk-mcp:latest"],
      "env": {}
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "testdisk-mcp": {
      "url": "http://localhost:8283/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8283` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/testdisk-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name testdisk-mcp-test -p 8283:8283 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/testdisk-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8283/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8283/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8283/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_testdisk","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop testdisk-mcp-test
```
