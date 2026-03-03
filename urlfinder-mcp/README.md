<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# URLFinder MCP Server

MCP server wrapper for [URLFinder](https://github.com/projectdiscovery/urlfinder) — passive URL discovery tool by ProjectDiscovery.

## What is URLFinder?

URLFinder passively discovers URLs for target domains using sources like **Wayback Machine, Common Crawl, URLScan, VirusTotal, AlienVault OTX**, and more. It aggregates results from multiple passive sources without directly contacting the target.

**No API keys required** — URLFinder queries public passive data sources to find known URLs for a domain.

## Tools Reference

### `find_urls`

Passively discover URLs for target domains using Wayback Machine, Common Crawl, URLScan, and more.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domains` | string | Yes | — | Comma-separated target domains (e.g. `"example.com,google.com"`) |
| `sources` | string | No | — | Comma-separated sources (e.g. `"waybackarchive,commoncrawl"`) |
| `exclude_sources` | string | No | — | Sources to exclude |
| `use_all_sources` | boolean | No | `false` | Use all available sources |
| `match_pattern` | string | No | — | Regex to match/include (e.g. `".*\\.js$"`) |
| `filter_pattern` | string | No | — | Regex to filter/exclude (e.g. `".*\\.png$"`) |
| `timeout` | integer | No | `30` | Timeout per source in seconds |
| `max_time` | integer | No | `10` | Max total execution time in minutes |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": ["https://example.com/api/v1/users", "https://example.com/static/app.js"]
}
```

</details>

### `list_sources`

List all available URL discovery sources. _No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Find all known URLs for example.com from passive sources like Wayback Machine."
- "Discover all JavaScript file URLs historically associated with hackerdogs.ai."
- "Find URLs for tesla.com but filter out image files (png, jpg, gif, svg)."
- "What API endpoints have been historically observed for api.github.com?"
- "List all the passive URL discovery sources that URLFinder supports."
- "Find all URLs for example.com using all available sources, and only show URLs matching *.js."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/urlfinder-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8112:8112 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8112 \
  hackerdogs/urlfinder-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "urlfinder-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/urlfinder-mcp:latest"],
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
    "urlfinder-mcp": {
      "url": "http://localhost:8112/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8112` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/urlfinder-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name urlfinder-test -p 8112:8112 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/urlfinder-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8112/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8112/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8112/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"find_urls","arguments":{"domains":"example.com"}}}'
```

**4. Clean up:**

```bash
docker stop urlfinder-test
```
