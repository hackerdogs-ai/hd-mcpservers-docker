<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Vulnx MCP Server

MCP server wrapper for [Vulnx](https://github.com/projectdiscovery/vulnx) — next-generation vulnerability search and analysis (successor to cvemap).

## What is Vulnx?

Vulnx is the successor to [cvemap](https://github.com/projectdiscovery/cvemap) from ProjectDiscovery, providing enhanced vulnerability search capabilities with subcommands for searching, filtering, and analyzing vulnerability data by product, vendor, severity, CVSS score, and more.

## Prerequisites

Vulnx works without an API key but is **rate-limited to 10 requests/min** without one. A free ProjectDiscovery Cloud Platform (PDCP) API key is recommended.

Get your free key at: [cloud.projectdiscovery.io](https://cloud.projectdiscovery.io/?ref=api_key)

```bash
export PDCP_API_KEY=your_api_key_here
```

## Tools Reference

### `search_vulnerabilities`

Search vulnerabilities with filters (product, vendor, severity, CVSS score).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | — | Search query (e.g. `"apache && severity:high"`) |
| `product` | string | No | — | Filter by product name |
| `vendor` | string | No | — | Filter by vendor name |
| `severity` | string | No | — | `"low"`, `"medium"`, `"high"`, or `"critical"` |
| `cvss_score` | string | No | — | CVSS threshold (e.g. `">=7.0"`) |
| `limit` | integer | No | `25` | Max results |
| `detailed` | boolean | No | `false` | Include detailed information |

<details>
<summary>Example response</summary>

```json
[{"cve_id": "CVE-2024-1234", "severity": "critical", "cvss_score": 9.8, "product": "apache http server"}]
```

</details>

### `get_vulnerability_details`

Get details for specific CVE(s).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cve_ids` | string | Yes | — | Comma-separated CVE IDs (e.g. `"CVE-2024-1234"`) |

### `list_search_filters`

List available search filter fields. _No parameters._

### `analyze_vulnerabilities`

Aggregate vulnerabilities by a field.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `field` | string | Yes | — | Field to aggregate by (e.g. `"severity"`, `"vendor"`) |
| `query` | string | No | — | Optional search query to narrow results |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search for all critical vulnerabilities in Apache Log4j."
- "Get the full details for CVE-2023-44228 including affected products and remediation."
- "Find high-severity vulnerabilities affecting 'wordpress' with CVSS >= 8.0."
- "What are the most recent critical vulnerabilities across all vendors?"
- "Analyze the severity breakdown of vulnerabilities for the vendor 'microsoft'."
- "Search for vulnerabilities related to 'remote code execution' in nginx."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm -e PDCP_API_KEY=your_key hackerdogs/vulnx-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8116:8116 \
  -e PDCP_API_KEY=your_key \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8116 \
  hackerdogs/vulnx-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "vulnx-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "PDCP_API_KEY",
        "hackerdogs/vulnx-mcp:latest"
      ],
      "env": {
        "PDCP_API_KEY": "<your-projectdiscovery-api-key>"
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above) — API keys are passed as environment variables at container start time. Then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "vulnx-mcp": {
      "url": "http://localhost:8116/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PDCP_API_KEY` | — | ProjectDiscovery API key (optional but recommended — rate-limited without it) |
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8116` | Port for streamable-http transport |
| `VULNX_BIN` | `vulnx` | Path to vulnx binary |

## Build

```bash
docker build -t hackerdogs/vulnx-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name vulnx-test -p 8116:8116 \
  -e MCP_TRANSPORT=streamable-http \
  -e PDCP_API_KEY=your_key \
  hackerdogs/vulnx-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8116/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8116/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8116/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_vulnerabilities","arguments":{"product":"apache","severity":"critical","limit":5}}}'
```

**4. Clean up:**

```bash
docker stop vulnx-test
```
