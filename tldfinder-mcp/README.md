<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# TLDFinder MCP Server

MCP server wrapper for [TLDFinder](https://github.com/projectdiscovery/tldfinder) — TLD and subdomain discovery tool by ProjectDiscovery.

## What is TLDFinder?

TLDFinder discovers **private TLDs and subdomains** using passive and active DNS enumeration. It supports multiple discovery modes, source filtering, and IP inclusion for comprehensive domain reconnaissance.

**No API keys required** — TLDFinder uses passive data sources and standard DNS queries.

## Tools Reference

### `find_tlds`

Discover TLDs and subdomains for domains using passive and active DNS.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domains` | string | Yes | — | Comma-separated target domains |
| `discovery_mode` | string | No | — | Mode: `"dns"`, `"tld"`, or `"domain"` |
| `sources` | string | No | — | Comma-separated sources to use |
| `exclude_sources` | string | No | — | Sources to exclude |
| `use_all_sources` | boolean | No | `false` | Use all available sources |
| `active_only` | boolean | No | `false` | Use only active DNS discovery |
| `include_ips` | boolean | No | `false` | Include IP addresses in output |
| `match_pattern` | string | No | — | Match pattern to filter results |
| `filter_pattern` | string | No | — | Filter pattern to exclude results |
| `timeout` | integer | No | `30` | Timeout per domain in seconds |
| `max_time` | integer | No | `10` | Max total runtime in minutes |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": ["example.com", "mail.example.com", "api.example.com"]
}
```

</details>

### `list_sources`

List all available TLD/subdomain discovery sources. _No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Find all subdomains and TLD variations for example.com."
- "Discover subdomains of hackerdogs.ai and include their IP addresses."
- "Use only active DNS discovery to enumerate subdomains for tesla.com."
- "Find all TLD variants of google.com (google.co.uk, google.de, etc.)."
- "List all the discovery sources that TLDFinder supports."
- "Enumerate subdomains for github.com using all available sources and show their IPs."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/tldfinder-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8113:8113 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8113 \
  hackerdogs/tldfinder-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "tldfinder-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/tldfinder-mcp:latest"],
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
    "tldfinder-mcp": {
      "url": "http://localhost:8113/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8113` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/tldfinder-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name tldfinder-test -p 8113:8113 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/tldfinder-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8113/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8113/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8113/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"find_tlds","arguments":{"domains":"example.com"}}}'
```

**4. Clean up:**

```bash
docker stop tldfinder-test
```
