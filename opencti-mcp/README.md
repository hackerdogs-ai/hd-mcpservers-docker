<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# OpenCTI MCP Server

MCP server for [OpenCTI](https://github.com/OpenCTI-Platform/opencti) — threat intelligence platform queries via the pycti Python client.

## What is OpenCTI?

OpenCTI is an open-source threat intelligence platform that allows organizations to manage their cyber threat intelligence knowledge and observables. It integrates with STIX2 standards and the MITRE ATT&CK framework.

See [OpenCTI-Platform/opencti](https://github.com/OpenCTI-Platform/opencti) for full documentation.

**API keys required** — Both `OPENCTI_API_KEY` and `OPENCTI_URL` must be set to connect to your OpenCTI instance.

**Summary.** MCP server for [OpenCTI](https://github.com/OpenCTI-Platform/opencti) — query indicators, malware, threat actors, reports, and MITRE ATT&CK techniques via the pycti API client.

**Tools:**
- `opencti_search_indicators` — Search for indicators of compromise (IOCs)
- `opencti_search_malware` — Search for malware entries
- `opencti_search_threat_actors` — Search for threat actors (groups)
- `opencti_get_report` — Get a specific report by ID or search reports
- `opencti_list_attack_patterns` — List MITRE ATT&CK techniques


## Tools Reference

### `opencti_search_indicators`

Search for indicators of compromise (IOCs) in OpenCTI. Returns matching indicators such as IP addresses, domains, hashes, URLs, etc.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | Search query (e.g. an IP, domain, hash, or keyword) |
| `limit` | integer | No | `10` | Maximum number of results to return |

<details>
<summary>Example response</summary>

```json
{
  "tool": "opencti_search_indicators",
  "query": "192.168.1.1",
  "count": 2,
  "results": [
    {
      "id": "indicator--abc123",
      "pattern": "[ipv4-addr:value = '192.168.1.1']",
      "name": "192.168.1.1"
    }
  ]
}
```

</details>

### `opencti_search_malware`

Search for malware entries in OpenCTI. Returns matching malware families, strains, and related intelligence.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | Search query (e.g. malware name or keyword) |
| `limit` | integer | No | `10` | Maximum number of results to return |

<details>
<summary>Example response</summary>

```json
{
  "tool": "opencti_search_malware",
  "query": "emotet",
  "count": 1,
  "results": [
    {
      "id": "malware--def456",
      "name": "Emotet",
      "description": "Banking trojan turned botnet loader"
    }
  ]
}
```

</details>

### `opencti_search_threat_actors`

Search for threat actors (groups) in OpenCTI. Returns matching threat actor profiles and related intelligence.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | Search query (e.g. threat actor name or keyword) |
| `limit` | integer | No | `10` | Maximum number of results to return |

<details>
<summary>Example response</summary>

```json
{
  "tool": "opencti_search_threat_actors",
  "query": "APT28",
  "count": 1,
  "results": [
    {
      "id": "threat-actor--ghi789",
      "name": "APT28",
      "description": "Russian state-sponsored threat group"
    }
  ]
}
```

</details>

### `opencti_get_report`

Get a specific report by ID or search reports in OpenCTI. Provide `report_id` to fetch a single report, or `query` to search.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `report_id` | string | No | `""` | OpenCTI report ID to fetch directly |
| `query` | string | No | `""` | Search query string for reports |
| `limit` | integer | No | `10` | Maximum number of results when searching |

<details>
<summary>Example response</summary>

```json
{
  "tool": "opencti_get_report",
  "query": "ransomware",
  "count": 3,
  "results": [
    {
      "id": "report--jkl012",
      "name": "Ransomware Trends Q1 2025",
      "published": "2025-04-01T00:00:00Z"
    }
  ]
}
```

</details>

### `opencti_list_attack_patterns`

List MITRE ATT&CK techniques (attack patterns) from OpenCTI. Returns matching ATT&CK techniques with IDs, names, and descriptions.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | No | `""` | Optional search query to filter attack patterns |
| `limit` | integer | No | `20` | Maximum number of results to return |

<details>
<summary>Example response</summary>

```json
{
  "tool": "opencti_list_attack_patterns",
  "query": "phishing",
  "count": 5,
  "results": [
    {
      "id": "attack-pattern--mno345",
      "name": "Phishing",
      "x_mitre_id": "T1566"
    }
  ]
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search OpenCTI for indicators related to the IP address 8.8.8.8."
- "Look up the threat actor APT29 in OpenCTI."
- "Find all malware entries matching 'cobalt strike' in OpenCTI."
- "Get the latest reports about ransomware from OpenCTI."
- "List all MITRE ATT&CK techniques related to credential access."
- "Search OpenCTI for IOCs containing the hash sha256:abc123def456."

## Deploy

### Docker Compose (recommended)

```bash
OPENCTI_API_KEY=your-key OPENCTI_URL=https://your-opencti-instance docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e OPENCTI_API_KEY=your-key \
  -e OPENCTI_URL=https://your-opencti-instance \
  hackerdogs/opencti-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8370:8370 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8370 \
  -e OPENCTI_API_KEY=your-key \
  -e OPENCTI_URL=https://your-opencti-instance \
  hackerdogs/opencti-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "opencti-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "OPENCTI_API_KEY", "-e", "OPENCTI_URL", "hackerdogs/opencti-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "OPENCTI_API_KEY": "",
        "OPENCTI_URL": ""
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
    "opencti-mcp": {
      "url": "http://localhost:8370/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8370` | HTTP port (only used with `streamable-http`) |
| `OPENCTI_API_KEY` | `""` | **Required.** API key for your OpenCTI instance |
| `OPENCTI_URL` | `""` | **Required.** Base URL of your OpenCTI instance (e.g. `https://opencti.example.com`) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use OpenCTI to search for indicators related to APT28"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/opencti-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name opencti-mcp-test -p 8370:8370 \
  -e MCP_TRANSPORT=streamable-http \
  -e OPENCTI_API_KEY=your-key \
  -e OPENCTI_URL=https://your-opencti-instance \
  hackerdogs/opencti-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8370/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8370/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8370/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"opencti_search_indicators","arguments":{"query":"test"}}}'
```

**4. Clean up:**

```bash
docker stop opencti-mcp-test
```


## Running the tool directly (bypassing MCP)

You can use the pycti client directly in the same container by overriding the entrypoint:

**Test connection:**

```bash
docker run --rm \
  -e OPENCTI_API_KEY=your-key \
  -e OPENCTI_URL=https://your-opencti-instance \
  --entrypoint python hackerdogs/opencti-mcp:latest \
  -c "from pycti import OpenCTIApiClient; c = OpenCTIApiClient('$OPENCTI_URL', '$OPENCTI_API_KEY'); print(c.health_check())"
```

**List indicators:**

```bash
docker run --rm \
  -e OPENCTI_API_KEY=your-key \
  -e OPENCTI_URL=https://your-opencti-instance \
  --entrypoint python hackerdogs/opencti-mcp:latest \
  -c "from pycti import OpenCTIApiClient; import json; c = OpenCTIApiClient('$OPENCTI_URL', '$OPENCTI_API_KEY'); print(json.dumps(c.indicator.list(first=5), indent=2, default=str))"
```
