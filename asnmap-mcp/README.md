<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Asnmap MCP Server

MCP server wrapper for [Asnmap](https://github.com/projectdiscovery/asnmap) — maps organization network ranges from ASN, IP, domain, and organization lookups for network reconnaissance and asset discovery.

## What is Asnmap?

Asnmap is a network mapping tool by ProjectDiscovery that resolves ASN (Autonomous System Number) information from multiple input types. It maps ASN numbers to advertised IP ranges, resolves IPs and domains to their parent ASN and organization, and finds all ASNs associated with an organization name.

## Prerequisites

Asnmap requires a **ProjectDiscovery Cloud Platform (PDCP) API key**.

Get your free key at: [cloud.projectdiscovery.io](https://cloud.projectdiscovery.io/?ref=api_key)

```bash
export PDCP_API_KEY=your_api_key_here
```

## Tools Reference

### `lookup_asn`

Look up network ranges associated with an ASN number.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `asn` | string | Yes | — | ASN number (e.g. `"AS13335"` or `"13335"`) |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [{"first_ip": "1.0.0.0", "last_ip": "1.0.0.255", "asn": 13335, "org": "Cloudflare, Inc."}]
}
```

</details>

### `lookup_ip`

Look up ASN and network information for an IP address.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ip` | string | Yes | — | IP address (e.g. `"1.1.1.1"`) |

### `lookup_domain`

Look up ASN and network information for a domain.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `domain` | string | Yes | — | Domain name (e.g. `"example.com"`) |

### `lookup_org`

Look up ASN and network information for an organization.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `org` | string | Yes | — | Organization name (e.g. `"Google"`) |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "What IP ranges does Cloudflare own? Look up ASN AS13335."
- "Which ASN and organization owns the IP address 8.8.8.8?"
- "Look up the network information for the domain netflix.com."
- "Find all ASN numbers and IP ranges associated with the organization 'Google'."
- "Map the network ranges for AS16509 (Amazon) to understand their infrastructure footprint."
- "What ASN is responsible for the IP 104.16.132.229 and what organization owns it?"

## Deploy

### Docker Compose (recommended)

```bash
PDCP_API_KEY=your_key docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm -e PDCP_API_KEY=your_key hackerdogs/asnmap-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8110:8110 \
  -e PDCP_API_KEY=your_key \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8110 \
  hackerdogs/asnmap-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "asnmap-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "PDCP_API_KEY",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/asnmap-mcp:latest"
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
    "asnmap-mcp": {
      "url": "http://localhost:8110/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PDCP_API_KEY` | — | **Required.** ProjectDiscovery Cloud Platform API key |
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8110` | Port for streamable-http transport |

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
docker build -t hackerdogs/asnmap-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name asnmap-test -p 8110:8110 \
  -e MCP_TRANSPORT=streamable-http \
  -e PDCP_API_KEY=your_key \
  hackerdogs/asnmap-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8110/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8110/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8110/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"lookup_asn","arguments":{"asn":"AS13335"}}}'
```

**4. Clean up:**

```bash
docker stop asnmap-test
```
