<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Evil-WinRM MCP Server

MCP server wrapper for [Evil Winrm](https://github.com/Hackplayers/evil-winrm) — Windows Remote Management shell.

## What is Evil Winrm?

Evil Winrm (evil-winrm) is a security tool that provides: **Windows Remote Management shell.**

See [Hackplayers/evil-winrm](https://github.com/Hackplayers/evil-winrm) for full documentation.

**No API keys required** — Evil Winrm runs locally inside the Docker container.

## Tools Reference

### `run_evil_winrm`

Run evil-winrm with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "evil-winrm output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run evil-winrm with --help to see all available options."
- "Use evil-winrm to scan the target 192.168.1.1."
- "What options does evil-winrm support? Show me its help output."
- "Run evil-winrm against example.com with default settings."
- "Execute evil-winrm with verbose output enabled."
- "Use the evil-winrm tool to analyze the target and report findings."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/evil-winrm-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8263:8263 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8263 \
  hackerdogs/evil-winrm-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "evil-winrm-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/evil-winrm-mcp:latest"],
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
    "evil-winrm-mcp": {
      "url": "http://localhost:8263/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8263` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/evil-winrm-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name evil-winrm-mcp-test -p 8263:8263 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/evil-winrm-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8263/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8263/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8263/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_evil_winrm","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop evil-winrm-mcp-test
```
