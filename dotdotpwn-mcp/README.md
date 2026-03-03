<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# DotDotPwn MCP Server

MCP server wrapper for [Dotdotpwn](https://github.com/wireghoul/dotdotpwn) — Directory traversal testing.

## What is Dotdotpwn?

Dotdotpwn (dotdotpwn) is a security tool that provides: **Directory traversal testing.**

See [wireghoul/dotdotpwn](https://github.com/wireghoul/dotdotpwn) for full documentation.

**No API keys required** — Dotdotpwn runs locally inside the Docker container.

## Tools Reference

### `run_dotdotpwn`

Run dotdotpwn with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "dotdotpwn output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run dotdotpwn with --help to see all available options."
- "Use dotdotpwn to scan the target 192.168.1.1."
- "What options does dotdotpwn support? Show me its help output."
- "Run dotdotpwn against example.com with default settings."
- "Execute dotdotpwn with verbose output enabled."
- "Use the dotdotpwn tool to analyze the target and report findings."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/dotdotpwn-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8223:8223 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8223 \
  hackerdogs/dotdotpwn-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "dotdotpwn-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/dotdotpwn-mcp:latest"],
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
    "dotdotpwn-mcp": {
      "url": "http://localhost:8223/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8223` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/dotdotpwn-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name dotdotpwn-mcp-test -p 8223:8223 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/dotdotpwn-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8223/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8223/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8223/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_dotdotpwn","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop dotdotpwn-mcp-test
```
