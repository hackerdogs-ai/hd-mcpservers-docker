<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Trivy Neutr0n MCP Server

MCP server wrapper for [Trivy Neutr0n](https://github.com/Mr-Neutr0n/trivy-mcp-server) — Trivy-based container and filesystem vulnerability scanning.

## What is Trivy Neutr0n?

Trivy Neutr0n (trivy-mcp) is a security tool that provides: **Trivy-based container and filesystem vulnerability scanning.**

See [Mr-Neutr0n/trivy-mcp-server](https://github.com/Mr-Neutr0n/trivy-mcp-server) for full documentation.

**No API keys required** — Trivy Neutr0n runs locally inside the Docker container.

## Tools Reference

### `run_trivy_mcp`

Run trivy-mcp with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "trivy-mcp output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run trivy-mcp with --help to see all available options."
- "Use trivy-mcp to scan the target 192.168.1.1."
- "What options does trivy-mcp support? Show me its help output."
- "Run trivy-mcp against example.com with default settings."
- "Execute trivy-mcp with verbose output enabled."
- "Use the trivy-mcp tool to analyze the target and report findings."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/trivy-neutr0n-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8356:8356 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8356 \
  hackerdogs/trivy-neutr0n-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "trivy-neutr0n-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/trivy-neutr0n-mcp:latest"],
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
    "trivy-neutr0n-mcp": {
      "url": "http://localhost:8356/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8356` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/trivy-neutr0n-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name trivy-neutr0n-mcp-test -p 8356:8356 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/trivy-neutr0n-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8356/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8356/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8356/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_trivy_mcp","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop trivy-neutr0n-mcp-test
```
