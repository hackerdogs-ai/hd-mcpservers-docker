<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# VirusTotal MCP Server

MCP server for [VirusTotal](https://www.virustotal.com) — file, URL, domain & IP threat intelligence via the VT API v3.

## What is VirusTotal?

VirusTotal is a service that analyzes files, URLs, domains, and IP addresses for malware and other threats using **70+ antivirus engines and URL/domain blocklisting services.**

See [VirusTotal API v3 documentation](https://docs.virustotal.com/reference/overview) for full details.

**API key required** — Set the `VT_API_KEY` environment variable with your VirusTotal API key. Get one free at [virustotal.com](https://www.virustotal.com).

**Summary.** MCP server for [VirusTotal](https://www.virustotal.com) — file, URL, domain & IP threat intelligence via the VT API v3.

**Tools:**
- `vt_file_report` — Get analysis report for a file by hash (MD5/SHA-1/SHA-256)
- `vt_url_report` — Get analysis report for a URL
- `vt_domain_report` — Get analysis report for a domain
- `vt_ip_report` — Get analysis report for an IP address
- `vt_scan_url` — Submit a URL for scanning
- `vt_get_analysis` — Get status/results of a pending analysis


## Tools Reference

### `vt_file_report`

Get the VirusTotal analysis report for a file by its hash (MD5, SHA-1, or SHA-256).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_hash` | string | Yes | — | MD5, SHA-1, or SHA-256 hash of the file |

<details>
<summary>Example response</summary>

```json
{
  "hash": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
  "sha256": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
  "file_name": "eicar.com",
  "file_type": "EICAR test file",
  "size": 68,
  "verdict": "malicious",
  "stats": {
    "malicious": 62,
    "suspicious": 0,
    "undetected": 6,
    "harmless": 0
  },
  "reputation": -892,
  "tags": ["eicar"],
  "first_seen": 1178279769,
  "last_analysis_date": 1710000000
}
```

</details>

### `vt_url_report`

Get the VirusTotal analysis report for a URL.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | The URL to look up (e.g. `https://example.com/path`) |

<details>
<summary>Example response</summary>

```json
{
  "url": "https://example.com",
  "final_url": "https://example.com/",
  "verdict": "clean",
  "stats": {
    "malicious": 0,
    "suspicious": 0,
    "undetected": 5,
    "harmless": 85
  },
  "reputation": 100,
  "categories": {"Forcepoint ThreatSeeker": "information technology"},
  "title": "Example Domain",
  "last_analysis_date": 1710000000
}
```

</details>

### `vt_domain_report`

Get the VirusTotal analysis report for a domain.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain` | string | Yes | — | Domain name to look up (e.g. `example.com`) |

<details>
<summary>Example response</summary>

```json
{
  "domain": "example.com",
  "verdict": "clean",
  "stats": {
    "malicious": 0,
    "suspicious": 0,
    "undetected": 3,
    "harmless": 87
  },
  "reputation": 100,
  "registrar": "RESERVED-Internet Assigned Numbers Authority",
  "creation_date": 694224000,
  "categories": {"Forcepoint ThreatSeeker": "information technology"},
  "whois": "...",
  "last_analysis_date": 1710000000,
  "tags": []
}
```

</details>

### `vt_ip_report`

Get the VirusTotal analysis report for an IP address.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ip_address` | string | Yes | — | IPv4 or IPv6 address to look up |

<details>
<summary>Example response</summary>

```json
{
  "ip_address": "8.8.8.8",
  "verdict": "clean",
  "stats": {
    "malicious": 0,
    "suspicious": 0,
    "undetected": 5,
    "harmless": 85
  },
  "reputation": 100,
  "as_owner": "GOOGLE",
  "asn": 15169,
  "country": "US",
  "network": "8.8.8.0/24",
  "last_analysis_date": 1710000000,
  "tags": []
}
```

</details>

### `vt_scan_url`

Submit a URL to VirusTotal for scanning. Returns an analysis ID to check with `vt_get_analysis`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | The URL to submit for scanning |

<details>
<summary>Example response</summary>

```json
{
  "url": "https://suspicious-site.com",
  "analysis_id": "u-xxxx-1710000000",
  "type": "analysis",
  "message": "URL submitted for scanning. Use vt_get_analysis with the analysis_id to check results."
}
```

</details>

### `vt_get_analysis`

Get the status and results of a VirusTotal analysis by its ID.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `analysis_id` | string | Yes | — | The analysis ID returned by `vt_scan_url` |

<details>
<summary>Example response</summary>

```json
{
  "analysis_id": "u-xxxx-1710000000",
  "status": "completed",
  "verdict": "malicious",
  "stats": {
    "malicious": 12,
    "suspicious": 2,
    "undetected": 50,
    "harmless": 26
  },
  "date": 1710000000
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Check if this file hash is malicious: 275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
- "Is the URL https://suspicious-site.com safe? Check it on VirusTotal."
- "Look up the domain evil.com on VirusTotal — is it flagged?"
- "Get the VirusTotal report for IP address 185.220.101.1."
- "Scan this URL on VirusTotal: https://example.com/download.exe"
- "Check the status of VirusTotal analysis u-xxxx-1710000000."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm -e VT_API_KEY="your-key-here" hackerdogs/virustotal-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8369:8369 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8369 \
  -e VT_API_KEY="your-key-here" \
  hackerdogs/virustotal-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "virustotal-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "VT_API_KEY", "hackerdogs/virustotal-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "VT_API_KEY": ""
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
    "virustotal-mcp": {
      "url": "http://localhost:8369/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8369` | HTTP port (only used with `streamable-http`) |
| `VT_API_KEY` | — | VirusTotal API key (required — get at [virustotal.com](https://www.virustotal.com)) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use VirusTotal to check if this hash is malicious"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/virustotal-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name virustotal-mcp-test -p 8369:8369 \
  -e MCP_TRANSPORT=streamable-http \
  -e VT_API_KEY="your-key-here" \
  hackerdogs/virustotal-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8369/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8369/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8369/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"vt_domain_report","arguments":{"domain":"example.com"}}}'
```

**4. Clean up:**

```bash
docker stop virustotal-mcp-test
```

## Running the tool directly (bypassing MCP)

Since this is an API-based server (no CLI binary), you can test the API connection directly:

**Check API key validity:**

```bash
docker run --rm -e VT_API_KEY="your-key-here" hackerdogs/virustotal-mcp:latest \
  python -c "import requests; r=requests.get('https://www.virustotal.com/api/v3/domains/example.com', headers={'x-apikey':'your-key-here'}); print(r.status_code)"
```

**Quick domain check:**

```bash
docker run --rm -e VT_API_KEY="your-key-here" hackerdogs/virustotal-mcp:latest \
  python -c "
import requests, json
r = requests.get('https://www.virustotal.com/api/v3/domains/example.com',
  headers={'x-apikey':'your-key-here', 'Accept':'application/json'})
print(json.dumps(r.json().get('data',{}).get('attributes',{}).get('last_analysis_stats',{}), indent=2))
"
```
