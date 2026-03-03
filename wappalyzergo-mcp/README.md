<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Wappalyzergo MCP Server

MCP server wrapper for [Wappalyzergo](https://github.com/projectdiscovery/wappalyzergo) — web technology detection tool by ProjectDiscovery.

## What is Wappalyzergo?

Wappalyzergo detects **web technologies** (frameworks, CMS, servers, JavaScript libraries, analytics tools, CDNs, databases, and more) from HTTP headers and HTML content. It fetches target URLs, analyzes responses, and matches against known technology fingerprints to identify the full technology stack.

**No API keys required** — Wappalyzergo connects directly to target URLs using standard HTTP requests.

## Tools Reference

### `detect_technologies`

Detect web technologies (frameworks, CMS, servers, libraries) on target URLs using HTTP headers and HTML fingerprinting.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | string | Yes | — | Comma-separated URLs (e.g. `"https://example.com,https://google.com"`) |
| `timeout` | integer | No | `10` | HTTP timeout per request in seconds |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [
    {"url": "https://example.com", "technologies": {"Nginx": {"categories": ["Web servers"]}}, "categories": {"Web servers": ["Nginx"]}}
  ]
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "What technologies is hackerdogs.ai built with?"
- "Detect the web stack on https://github.com — what server, framework, and CDN does it use?"
- "Compare the technology stacks of https://shopify.com and https://bigcommerce.com."
- "Check what CMS is being used on https://wordpress.org."
- "Identify the JavaScript frameworks and analytics tools on https://vercel.com."
- "Scan https://example.com and https://example.org to see if they use the same web server."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/wappalyzergo-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8114:8114 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8114 \
  hackerdogs/wappalyzergo-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "wappalyzergo-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/wappalyzergo-mcp:latest"],
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
    "wappalyzergo-mcp": {
      "url": "http://localhost:8114/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8114` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/wappalyzergo-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name wappalyzergo-test -p 8114:8114 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/wappalyzergo-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8114/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8114/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8114/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"detect_technologies","arguments":{"urls":"https://example.com"}}}'
```

**4. Clean up:**

```bash
docker stop wappalyzergo-test
```
