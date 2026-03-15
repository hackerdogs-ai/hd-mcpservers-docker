<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AlienVault OTX MCP Server

MCP server for [AlienVault OTX](https://otx.alienvault.com) — open threat intelligence platform with crowd-sourced threat data.

## What is AlienVault OTX?

AlienVault Open Threat Exchange (OTX) is the world's largest open threat intelligence community. It provides: **crowd-sourced threat data, IoC lookups, pulse-based threat sharing, and automated threat analysis.**

See [otx.alienvault.com](https://otx.alienvault.com) for full documentation.

**API key required** — Set the `OTX_API_KEY` environment variable. Get a free API key at [https://otx.alienvault.com](https://otx.alienvault.com) (sign up → Settings → API Key).

**Summary.** MCP server for [AlienVault OTX](https://otx.alienvault.com) — open threat intelligence platform with crowd-sourced threat data. Uses the OTXv2 Python SDK to query the OTX API directly.

**Tools:**
- `otx_file_report` — Query OTX for a file hash (MD5/SHA1/SHA256)
- `otx_url_report` — Query OTX for a URL
- `otx_domain_report` — Query OTX for a domain
- `otx_ip_report` — Query OTX for an IP address
- `otx_submit_url` — Submit a URL to OTX for analysis


## Tools Reference

### `otx_file_report`

Query AlienVault OTX for a file hash (MD5, SHA1, or SHA256). Returns threat intelligence data including pulse references, malware families, and analysis results.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_hash` | string | Yes | — | The file hash to look up (MD5, SHA1, or SHA256) |

<details>
<summary>Example response</summary>

```json
{
  "hash": "6c5360d41bd2b14b1565f5b18e5c203cf512e493",
  "hash_type": "sha1",
  "data": {
    "general": {
      "indicator": "6c5360d41bd2b14b1565f5b18e5c203cf512e493",
      "pulse_info": {
        "count": 5,
        "pulses": [
          {
            "name": "Malware Campaign Q1 2025",
            "description": "Tracking known malware hashes"
          }
        ]
      }
    },
    "analysis": {
      "malware_families": ["trojan"],
      "file_type": "PE32 executable"
    }
  }
}
```

</details>

### `otx_url_report`

Query AlienVault OTX for a URL. Returns threat intelligence data including pulse references, associated domains/IPs, and reputation data.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | The URL to look up |

<details>
<summary>Example response</summary>

```json
{
  "url": "http://malicious-example.com/payload",
  "data": {
    "general": {
      "url_list": {
        "url": "http://malicious-example.com/payload",
        "result": {
          "urlworker": {
            "ip": "203.0.113.50",
            "http_code": 200
          }
        }
      },
      "pulse_info": {
        "count": 3
      }
    }
  }
}
```

</details>

### `otx_domain_report`

Query AlienVault OTX for a domain. Returns threat intelligence including pulse references, DNS records, associated malware, WHOIS data, and reputation information.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain` | string | Yes | — | The domain name to look up (e.g. "example.com") |

<details>
<summary>Example response</summary>

```json
{
  "domain": "example.com",
  "data": {
    "general": {
      "indicator": "example.com",
      "pulse_info": {
        "count": 0,
        "pulses": []
      },
      "whois": "https://otx.alienvault.com/whois/example.com"
    },
    "geo": {
      "country_name": "United States",
      "city": "Los Angeles"
    },
    "passive_dns": [
      {
        "address": "93.184.216.34",
        "hostname": "example.com",
        "record_type": "A"
      }
    ]
  }
}
```

</details>

### `otx_ip_report`

Query AlienVault OTX for an IP address. Returns threat intelligence including pulse references, geolocation, passive DNS, associated malware, and reputation data.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ip_address` | string | Yes | — | The IP address to look up (IPv4 or IPv6) |

<details>
<summary>Example response</summary>

```json
{
  "ip_address": "8.8.8.8",
  "data": {
    "general": {
      "indicator": "8.8.8.8",
      "pulse_info": {
        "count": 12,
        "pulses": [
          {
            "name": "Known DNS Resolvers",
            "description": "Public DNS resolver IPs"
          }
        ]
      },
      "whois": "https://otx.alienvault.com/whois/8.8.8.8"
    },
    "geo": {
      "country_name": "United States",
      "asn": "AS15169 Google LLC"
    },
    "reputation": {
      "threat_score": 0
    }
  }
}
```

</details>

### `otx_submit_url`

Submit a URL to AlienVault OTX for analysis. Results may take time to process.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | The URL to submit for analysis |

<details>
<summary>Example response</summary>

```json
{
  "submitted_url": "http://suspicious-site.com/page",
  "result": {
    "status": "accepted",
    "message": "URL submitted for analysis"
  }
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use OTX to look up the domain evil-corp.com for any threat intelligence."
- "Check the IP address 203.0.113.50 against AlienVault OTX for known threats."
- "Look up this SHA256 hash in OTX: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
- "Query OTX for threat data on the URL http://suspicious-site.com/download"
- "Submit this suspicious URL to OTX for analysis: http://phishing-example.com/login"
- "What does AlienVault OTX know about the IP 1.2.3.4? Show me any associated pulses."

## Deploy

### Docker Compose (recommended)

```bash
OTX_API_KEY=your-key-here docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm -e MCP_TRANSPORT -e OTX_API_KEY hackerdogs/otx-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8368:8368 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8368 \
  -e OTX_API_KEY=your-key-here \
  hackerdogs/otx-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "otx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "OTX_API_KEY", "hackerdogs/otx-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "OTX_API_KEY": "your-otx-api-key-here"
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
    "otx-mcp": {
      "url": "http://localhost:8368/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8368` | HTTP port (only used with `streamable-http`) |
| `OTX_API_KEY` | — | AlienVault OTX API key (required — free at [otx.alienvault.com](https://otx.alienvault.com)) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use OTX to check the domain example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your OTX API key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/otx-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name otx-mcp-test -p 8368:8368 \
  -e MCP_TRANSPORT=streamable-http \
  -e OTX_API_KEY=your-key-here \
  hackerdogs/otx-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8368/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8368/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8368/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"otx_domain_report","arguments":{"domain":"example.com"}}}'
```

**4. Clean up:**

```bash
docker stop otx-mcp-test
```

## Running the tool directly (bypassing MCP)

This is an API-based MCP server that uses the OTXv2 Python SDK — there is no standalone CLI binary to run. All interaction with AlienVault OTX goes through the MCP tools. To query OTX directly without MCP, use the [OTXv2 Python SDK](https://github.com/AlienVault-OTX/OTX-Python-SDK) or the [OTX API](https://otx.alienvault.com/api) directly.
