<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# MISP MCP Server

MCP server for [MISP](https://www.misp-project.org/) — Malware Information Sharing Platform (threat intelligence, IOC search, event management).

## What is MISP?

MISP is an open-source threat intelligence sharing platform that provides: **IOC sharing, event correlation, and threat intelligence feeds.**

See [MISP Project](https://www.misp-project.org/) for full documentation.

**API key required** — You must set `MISP_API_KEY` and `MISP_URL` environment variables pointing to your MISP instance.

**Summary.** MCP server for [MISP](https://www.misp-project.org/) — threat intelligence sharing platform (IOC search, event management, attribute enrichment).

**Tools:**
- `misp_search_attributes` — Search MISP attributes (IOCs) by value
- `misp_search_events` — Search MISP events by keyword
- `misp_get_event` — Get a specific MISP event by ID
- `misp_add_attribute` — Add an attribute (IOC) to an existing MISP event


## Tools Reference

### `misp_search_attributes`

Search MISP attributes (IOCs) by value. Queries the MISP restSearch endpoint to find indicators of compromise matching the given value (IP, domain, hash, email, etc.).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `value` | string | Yes | — | The IOC value to search for (e.g. "8.8.8.8", "evil.com", a hash) |
| `type_attribute` | string | No | `""` | MISP attribute type filter (e.g. "ip-dst", "domain", "md5") |
| `limit` | integer | No | `25` | Maximum number of results to return |

<details>
<summary>Example response</summary>

```json
{
  "response": {
    "Attribute": [
      {
        "id": "12345",
        "type": "domain",
        "value": "evil.com",
        "event_id": "678",
        "category": "Network activity"
      }
    ]
  }
}
```

</details>

### `misp_search_events`

Search MISP events by keyword. Searches event info fields for the given query string.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | — | Search term to match against event info/descriptions |
| `limit` | integer | No | `25` | Maximum number of results to return |

<details>
<summary>Example response</summary>

```json
{
  "response": [
    {
      "Event": {
        "id": "678",
        "info": "Phishing campaign targeting financial sector",
        "date": "2025-01-15",
        "threat_level_id": "2"
      }
    }
  ]
}
```

</details>

### `misp_get_event`

Get a specific MISP event by ID. Retrieves full event details including all attributes and metadata.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `event_id` | string | Yes | — | The numeric MISP event ID (e.g. "1234") |

<details>
<summary>Example response</summary>

```json
{
  "Event": {
    "id": "678",
    "info": "Phishing campaign targeting financial sector",
    "Attribute": [
      {
        "id": "12345",
        "type": "domain",
        "value": "evil.com"
      }
    ]
  }
}
```

</details>

### `misp_add_attribute`

Add an attribute (IOC) to an existing MISP event. Use this to enrich events with additional indicators of compromise.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `event_id` | string | Yes | — | The numeric MISP event ID to add the attribute to |
| `type_attribute` | string | Yes | — | MISP attribute type (e.g. "ip-dst", "domain", "md5", "url") |
| `value` | string | Yes | — | The attribute value (e.g. "192.168.1.1", "evil.com") |
| `category` | string | No | `"Network activity"` | MISP category (e.g. "Network activity", "Payload delivery") |

<details>
<summary>Example response</summary>

```json
{
  "Attribute": {
    "id": "12346",
    "type": "ip-dst",
    "value": "192.168.1.1",
    "event_id": "678",
    "category": "Network activity"
  }
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search MISP for any attributes matching the domain evil.com."
- "Look up the IP 203.0.113.42 in MISP to see if it's a known IOC."
- "Search MISP events related to ransomware campaigns."
- "Get the full details for MISP event 1234."
- "Add the domain malware-c2.example.com as an IOC to MISP event 5678."
- "Search MISP for MD5 hash d41d8cd98f00b204e9800998ecf8427e."

## Deploy

### Docker Compose (recommended)

```bash
MISP_API_KEY=your-key MISP_URL=https://your-misp-instance docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e MISP_API_KEY=your-key \
  -e MISP_URL=https://your-misp-instance \
  hackerdogs/misp-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8371:8371 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8371 \
  -e MISP_API_KEY=your-key \
  -e MISP_URL=https://your-misp-instance \
  hackerdogs/misp-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "misp-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MISP_API_KEY", "-e", "MISP_URL", "hackerdogs/misp-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "MISP_API_KEY": "",
        "MISP_URL": ""
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
    "misp-mcp": {
      "url": "http://localhost:8371/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8371` | HTTP port (only used with `streamable-http`) |
| `MISP_API_KEY` | — | **Required.** Your MISP instance API key |
| `MISP_URL` | — | **Required.** Your MISP instance URL (e.g. `https://misp.example.com`) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use MISP to search for IOCs matching evil.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your `MISP_API_KEY` and `MISP_URL` in the config environment variable fields before clicking Install. Your keys will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/misp-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name misp-mcp-test -p 8371:8371 \
  -e MCP_TRANSPORT=streamable-http \
  -e MISP_API_KEY=your-key \
  -e MISP_URL=https://your-misp-instance \
  hackerdogs/misp-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8371/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8371/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8371/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"misp_search_attributes","arguments":{"value":"8.8.8.8"}}}'
```

**4. Clean up:**

```bash
docker stop misp-mcp-test
```


## Running the tool directly (bypassing MCP)

Since MISP MCP is an API-based server (not a CLI wrapper), you can test the MISP API connection directly:

**Test API connectivity:**

```bash
docker run --rm \
  -e MISP_API_KEY=your-key \
  -e MISP_URL=https://your-misp-instance \
  hackerdogs/misp-mcp:latest \
  python -c "import requests; r = requests.get('https://your-misp-instance/servers/getVersion', headers={'Authorization': 'your-key', 'Accept': 'application/json'}, verify=False); print(r.json())"
```
