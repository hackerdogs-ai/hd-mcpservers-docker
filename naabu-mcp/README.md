<p align="center">
  <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="200"/>
</p>

# Naabu MCP Server

MCP server wrapper for [Naabu](https://github.com/projectdiscovery/naabu) — fast port scanner by ProjectDiscovery.

## What is Naabu?

Naabu is a fast port scanner written in Go that performs **SYN, CONNECT, or UDP scanning** to reliably enumerate open ports on target hosts. It supports configurable rate limiting, threading, and multiple scan types for flexible network reconnaissance.

**No API keys required** — Naabu sends network probes directly to target hosts.

## Tools Reference

### `scan_ports`

Scan ports on target hosts. Returns discovered open ports in JSON format.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `hosts` | string | Yes | — | Target host(s) — IP, CIDR, or comma-separated list |
| `ports` | string | No | — | Specific ports or ranges (e.g. `"80,443"`, `"1-1024"`) |
| `top_ports` | integer | No | `100` | Number of top ports to scan (ignored if `ports` is set) |
| `scan_type` | string | No | — | `"s"` for SYN (requires root) or `"c"` for CONNECT |
| `passive` | boolean | No | `false` | Use passive port enumeration (no active scanning) |
| `rate` | integer | No | `1000` | Packets per second rate limit |
| `threads` | integer | No | `25` | Number of concurrent threads |
| `exclude_hosts` | string | No | — | Hosts to exclude (comma-separated) |
| `exclude_ports` | string | No | — | Ports to exclude (comma-separated) |

<details>
<summary>Example response</summary>

```json
[
  {
    "ip": "192.168.4.174",
    "port": 11434,
    "protocol": "tcp",
    "tls": false
  }
]
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Scan the top 1000 ports on 192.168.1.1 and tell me which ones are open."
- "Do a quick port scan of scanme.nmap.org on ports 22, 80, 443, and 8080."
- "Scan the entire 10.0.0.0/24 subnet for open web ports (80, 443, 8080, 8443)."
- "Find all open ports on my server at 192.168.4.174 using a CONNECT scan."
- "Scan 203.0.113.50 but exclude ports 25 and 587 from the results."
- "Run a passive port enumeration on example.com without sending any probes."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/naabu-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8105:8105 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8105 \
  hackerdogs/naabu-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "naabu-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/naabu-mcp:latest"],
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
    "naabu-mcp": {
      "url": "http://localhost:8105/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8105` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/naabu-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name naabu-test -p 8105:8105 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/naabu-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8105/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8105/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8105/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"scan_ports","arguments":{"hosts":"scanme.nmap.org","top_ports":100}}}'
```

**4. Clean up:**

```bash
docker stop naabu-test
```

> **Note:** The container runs as a non-root user, so naabu defaults to CONNECT scanning (`-s c`). For SYN scanning, run with `--cap-add=NET_RAW` and pass `scan_type: "s"`.
