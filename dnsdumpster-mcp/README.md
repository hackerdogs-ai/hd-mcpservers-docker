<p align="center">
  <img src="https://hackerdogs.ai/favicon.ico" width="60" alt="Hackerdogs logo" />
</p>

<h1 align="center">dnsdumpster-mcp</h1>

<p align="center">
  <strong>DNSDumpster MCP Server</strong> — Passive DNS reconnaissance with subdomain enumeration, DNS records, ASN, and geolocation
</p>

---

## What is DNSDumpster?

[DNSDumpster](https://github.com/nmmapper/dnsdumpster) is a passive DNS reconnaissance tool that discovers subdomains, DNS records (A, MX, NS, TXT), ASN information, geolocation data, and server types by querying multiple passive data sources:

- **DNSDumpster.com** — subdomain enumeration
- **Netcraft** — subdomain and server fingerprinting
- **VirusTotal** — passive DNS data
- **crt.sh** — SSL Certificate Transparency logs

This is **passive reconnaissance** — no direct queries are sent to the target domain, making it safe for initial reconnaissance and OSINT gathering.

## MCP Server

This MCP server wraps the `dnsdumpster` CLI tool inside a Docker container and exposes it through the Model Context Protocol. It provides **two tools**:

| Tool | Description |
|------|-------------|
| `dnsdumpster_search` | Structured passive DNS reconnaissance — takes a domain name and returns normalized JSON with subdomains, MX/NS/TXT records, ASN info, and server types |
| `run_dnsdumpster` | Generic CLI passthrough — run `dnsdumpster` with any arguments |

No API keys required.

---

## Tools Reference

### `dnsdumpster_search`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain` | string | Yes | — | Target domain (e.g. `example.com`). Protocols stripped automatically. |
| `timeout_seconds` | int | No | 300 | Max execution time in seconds |

### `run_dnsdumpster`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `-d example.com`) |
| `timeout_seconds` | int | No | 300 | Max execution time in seconds |

---

## Example Prompts

```
Perform passive DNS reconnaissance on hackerdogs.ai

Enumerate all subdomains for tesla.com and show their IPs and ASN info

Find all MX and NS records for github.com

What subdomains does cloudflare.com have? Include geolocation and server types.

Run a full DNS dump of example.com and summarize the infrastructure
```

---

## Deploy

### Docker Compose (HTTP Streamable)

```bash
docker compose up -d
```

Server available at `http://localhost:8216/mcp`

### Docker Run (stdio mode — for MCP clients)

```bash
docker run -i --rm -e MCP_TRANSPORT=stdio hackerdogs/dnsdumpster-mcp:latest
```

### Docker Run (HTTP mode)

```bash
docker run -d -p 8216:8216 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8216 \
  hackerdogs/dnsdumpster-mcp:latest
```

---

## MCP Client Configuration

### stdio mode (recommended for Claude Desktop, Cursor)

Add to your MCP client config:

```json
{
  "mcpServers": {
    "dnsdumpster-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/dnsdumpster-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### HTTP streamable mode

```json
{
  "mcpServers": {
    "dnsdumpster-mcp": {
      "url": "http://localhost:8216/mcp"
    }
  }
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8216` | HTTP port (only used in streamable-http mode) |
| `DNSDUMPSTER_BIN` | `dnsdumpster` | Path to the dnsdumpster binary |

---

## Installing in Hackerdogs

In the Hackerdogs dashboard, add a new MCP server with:

- **Transport**: stdio
- **Command**: `docker`
- **Args**: `run -i --rm -e MCP_TRANSPORT hackerdogs/dnsdumpster-mcp:latest`
- **Env**: `MCP_TRANSPORT=stdio`

---

## Build

```bash
docker build -t hackerdogs/dnsdumpster-mcp:latest .
```

Multi-arch build and publish:

```bash
./publish_to_hackerdogs.sh --build --publish
```

---

## Testing

### Automated test suite

```bash
chmod +x test.sh
./test.sh
```

### Manual — stdio mode

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
  docker run -i --rm -e MCP_TRANSPORT=stdio hackerdogs/dnsdumpster-mcp:latest
```

### Manual — HTTP mode

```bash
# Start server
docker run -d --name dnsdumpster-test -p 8216:8216 \
  -e MCP_TRANSPORT=streamable-http hackerdogs/dnsdumpster-mcp:latest

# Initialize
curl -s -X POST http://localhost:8216/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}'

# List tools
curl -s -X POST http://localhost:8216/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

# Cleanup
docker rm -f dnsdumpster-test
```

---

## Running the tool directly (bypassing MCP)

```bash
# Show help
docker run --rm hackerdogs/dnsdumpster-mcp:latest dnsdumpster --help

# DNS reconnaissance on a domain
docker run --rm hackerdogs/dnsdumpster-mcp:latest dnsdumpster -d example.com
```
