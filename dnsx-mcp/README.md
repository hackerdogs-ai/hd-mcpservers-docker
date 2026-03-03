<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# DNSx MCP Server

MCP server wrapper for [DNSx](https://github.com/projectdiscovery/dnsx) — multi-purpose DNS toolkit by ProjectDiscovery.

## What is DNSx?

DNSx is a multi-purpose DNS toolkit for running queries across **A, AAAA, CNAME, MX, TXT, NS, SOA, and PTR** record types. It supports wildcard handling, subdomain brute-forcing with wordlists, CDN detection, ASN lookup, and response filtering.

**No API keys required** — DNSx queries DNS servers directly using standard DNS protocol.

## Tools Reference

### `resolve_domains`

Resolve DNS records for one or more domains. Supports A, AAAA, CNAME, NS, MX, TXT, PTR, SOA record types.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domains` | string | Yes | — | Domains to resolve, comma-separated (e.g. `"example.com,google.com"`) |
| `record_types` | list[string] | No | `["a"]` | Record types to query: `a`, `aaaa`, `cname`, `ns`, `mx`, `txt`, `ptr`, `soa` |
| `show_response` | boolean | No | `true` | Display DNS response values |
| `response_only` | boolean | No | `false` | Show only response values without domain names |
| `check_cdn` | boolean | No | `false` | Detect CDN usage for domains |
| `check_asn` | boolean | No | `false` | Display ASN information |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [
    {"host": "google.com", "a": ["142.251.214.142"], "mx": ["smtp.google.com"], "status_code": "NOERROR"}
  ]
}
```

</details>

### `bruteforce_subdomains`

Bruteforce subdomains using a wordlist.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain` | string | Yes | — | Target domain (e.g. `"example.com"`) |
| `wordlist_content` | string | Yes | — | Newline-separated subdomain words (e.g. `"www\nmail\napi"`) |
| `record_type` | string | No | `"a"` | DNS record type to query |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Resolve the A and MX records for hackerdogs.ai."
- "Look up all DNS record types (A, AAAA, CNAME, NS, MX, TXT) for example.com."
- "Bruteforce subdomains on example.com using the words www, mail, api, dev, staging, admin, and app."
- "Check if cloudflare.com is using a CDN and show me the ASN information."
- "What are the nameservers and SOA record for github.com?"
- "Resolve the PTR record for 8.8.8.8 to find its reverse DNS hostname."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/dnsx-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8108:8108 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8108 \
  hackerdogs/dnsx-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "dnsx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/dnsx-mcp:latest"],
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
    "dnsx-mcp": {
      "url": "http://localhost:8108/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8108` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/dnsx-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name dnsx-test -p 8108:8108 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/dnsx-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8108/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8108/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8108/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"resolve_domains","arguments":{"domains":"google.com","record_types":["A","MX"]}}}'
```

**4. Clean up:**

```bash
docker stop dnsx-test
```
