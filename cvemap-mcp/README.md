<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Cvemap MCP Server

MCP server wrapper for [Cvemap](https://github.com/projectdiscovery/cvemap) — CVE and vulnerability search, filtering, and analysis.

## What is Cvemap?

Cvemap is a CLI tool by ProjectDiscovery that provides a structured interface for browsing and exploring CVEs. It supports searching and filtering by product, vendor, severity, CVSS score, and more, making it easy to stay on top of vulnerability data.

## Prerequisites

Cvemap works without an API key but is **rate-limited** without one. A free ProjectDiscovery Cloud Platform (PDCP) API key is recommended.

Get your free key at: [cloud.projectdiscovery.io](https://cloud.projectdiscovery.io/?ref=api_key)

```bash
export PDCP_API_KEY=your_api_key_here
```

**Summary.** MCP server wrapper for [Cvemap](https://github.com/projectdiscovery/cvemap) — CVE and vulnerability search, filtering, and analysis.

**Tools:**
- `search_cves` — Search CVEs with filters (product, vendor, severity, CVSS score).
- `get_cve_details` — Get details for specific CVE(s).
- `list_filters` — List available CVE search filter fields. _No parameters._
- `analyze_cves` — Aggregate and analyze CVEs by a field (severity, vendor, product, year).


## Tools Reference

### `search_cves`

Search CVEs with filters (product, vendor, severity, CVSS score).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | — | Free-text search query |
| `product` | string | No | — | Filter by product name (e.g. `"chrome"`) |
| `vendor` | string | No | — | Filter by vendor (e.g. `"microsoft"`) |
| `severity` | string | No | — | Filter: `"low"`, `"medium"`, `"high"`, or `"critical"` |
| `cvss_score` | string | No | — | CVSS threshold (e.g. `">=7.0"`) |
| `limit` | integer | No | `25` | Max results to return |
| `detailed` | boolean | No | `false` | Include detailed CVE information |

<details>
<summary>Example response</summary>

```json
[{"cve_id": "CVE-2024-1234", "severity": "high", "cvss_score": 8.1, "product": "chrome", "vendor": "google"}]
```

</details>

### `get_cve_details`

Get details for specific CVE(s).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cve_ids` | string | Yes | — | Comma-separated CVE IDs (e.g. `"CVE-2024-1234,CVE-2024-5678"`) |

### `list_filters`

List available CVE search filter fields. _No parameters._

### `analyze_cves`

Aggregate and analyze CVEs by a field (severity, vendor, product, year).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `field` | string | Yes | — | Field to aggregate by (e.g. `"severity"`, `"vendor"`) |
| `query` | string | No | — | Optional search query to narrow the CVE set |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Find all critical CVEs affecting Apache HTTP Server."
- "Show me the details for CVE-2024-3094 (the xz backdoor vulnerability)."
- "Search for high and critical vulnerabilities in Microsoft Exchange with a CVSS score above 8.0."
- "What are the latest CVEs for Google Chrome?"
- "Analyze the severity distribution of CVEs for the vendor 'mozilla'."
- "List all CVEs for the product 'openssh' that have a CVSS score >= 7.0."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm -e PDCP_API_KEY=your_key hackerdogs/cvemap-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8106:8106 \
  -e PDCP_API_KEY=your_key \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8106 \
  hackerdogs/cvemap-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "cvemap-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "PDCP_API_KEY",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/cvemap-mcp:latest"
      ],
      "env": {
        "PDCP_API_KEY": "<your-projectdiscovery-api-key>",
        "MCP_TRANSPORT": "stdio"
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
    "cvemap-mcp": {
      "url": "http://localhost:8106/mcp"
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
| `MCP_PORT` | `8106` | Port for streamable-http transport |
| `CVEMAP_BIN` | `cvemap` | Path to cvemap binary |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use naabu to scan example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/cvemap-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name cvemap-test -p 8106:8106 \
  -e MCP_TRANSPORT=streamable-http \
  -e PDCP_API_KEY=your_key \
  hackerdogs/cvemap-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8106/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8106/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8106/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_cves","arguments":{"product":"chrome","severity":"critical","limit":5}}}'
```

**4. Clean up:**

```bash
docker stop cvemap-test
```
