<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Nerva MCP Server

MCP server wrapper for [Nerva](https://github.com/praetorian-inc/nerva) — network service fingerprinting tool by Praetorian.

## What is Nerva?

Nerva identifies **120+ network services** on open ports and extracts version and configuration metadata. It probes target host:port pairs and matches responses against known service signatures to determine what software is running.

**No API keys required** — Nerva connects directly to target services using standard network probes.

## Tools Reference

### `fingerprint_services`

Identify network services on open ports and extract version/config metadata. Detects 120+ service types.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `targets` | string | Yes | — | Comma-separated `host:port` pairs (e.g. `"10.0.0.1:80,10.0.0.1:443"`) |
| `output_format` | string | No | `"json"` | Output format: `"json"` or `"csv"` |
| `fast_mode` | boolean | No | `false` | Use fast mode (quicker, less thorough) |
| `udp` | boolean | No | `false` | Also probe UDP ports |
| `timeout` | integer | No | `2000` | Connection timeout in milliseconds |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": {"ip": "192.168.4.174", "port": 11434, "protocol": "http", "tls": false, "metadata": {"statusCode": 200}}
}
```

</details>

### `list_capabilities`

List all 120+ supported service detection plugins. _No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Identify what services are running on 192.168.1.1 ports 22, 80, 443, and 3306."
- "Fingerprint the service on 10.0.0.5:8080 and tell me the software version."
- "Scan 192.168.4.174:11434 and check if it's running an HTTP service or something else."
- "What network services are exposed on scanme.nmap.org:22 and scanme.nmap.org:80?"
- "List all the service detection plugins that Nerva supports."
- "Do a fast fingerprint of 10.0.0.1:443 and 10.0.0.1:8443 to see if they're both HTTPS."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/nerva-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8104:8104 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8104 \
  hackerdogs/nerva-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "nerva-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/nerva-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "nerva-mcp": {
      "url": "http://localhost:8104/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8104` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/nerva-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name nerva-test -p 8104:8104 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/nerva-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8104/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8104/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8104/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"fingerprint_services","arguments":{"targets":"scanme.nmap.org:22,scanme.nmap.org:80"}}}'
```

**4. Clean up:**

```bash
docker stop nerva-test
```
