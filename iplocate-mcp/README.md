<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# IP Locate MCP Server

MCP server wrapper for [IPLocate](https://www.iplocate.io) — IP geolocation and organization lookup via the IPLocate API.

## What is IP Locate?

IPLocate is an IP address intelligence service that returns geographic location data (country, region, city, latitude/longitude), ISP and organization name, ASN, and whether an IP belongs to a hosting provider, VPN, Tor exit node, or proxy. It is commonly used during incident response and reconnaissance to quickly contextualize IP addresses from logs, alerts, or scan results. See [@iplocate/mcp-server](https://www.npmjs.com/package/@iplocate/mcp-server) for full documentation.

**No API keys required** — the server uses IPLocate's free-tier public API out of the box.

## Tools Reference

| Tool | Description |
|------|-------------|
| `lookup_ip_address_details` | Lookup Ip Address Details |
| `lookup_ip_address_location` | Lookup Ip Address Location |
| `lookup_ip_address_privacy` | Lookup Ip Address Privacy |
| `lookup_ip_address_network` | Lookup Ip Address Network |
| `lookup_ip_address_company` | Lookup Ip Address Company |
| `lookup_ip_address_abuse_contacts` | Lookup Ip Address Abuse Contacts |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Look up the geographic location and ISP for IP address 8.8.8.8."
- "Is the IP 185.220.101.34 a Tor exit node or known VPN according to IPLocate?"
- "Geolocate the IP 103.21.244.0 and tell me which country and ASN it belongs to."
- "Check whether IP 104.26.10.78 is a cloud hosting provider IP according to IPLocate."
- "I have ten suspicious IPs from our firewall logs — use IPLocate to geolocate each one."
- "Look up the organization and ASN registered to IP 1.1.1.1 using IPLocate."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/iplocate-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8648:8648 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8648 \
  hackerdogs/iplocate-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "iplocate-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/iplocate-mcp:latest"
      ],
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
    "iplocate-mcp": {
      "url": "http://localhost:8648/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.


## Securely Accessing MCP

When running through the [Hackerdogs MCP Farm](https://hackerdogs.ai), servers are accessed through the authenticated gateway instead of direct container ports:

```json
{
  "mcpServers": {
    "iplocate-mcp": {
      "url": "http://localhost:8485/iplocate-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

> **Farm access:** The MCP Farm gateway handles authentication, rate limiting, and routing. Replace `localhost:8485` with your farm's host address and use your API key from the farm admin panel. See [Hackerdogs](https://hackerdogs.ai) for details.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8648` | HTTP port (only used with `streamable-http`) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/iplocate-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name iplocate-mcp-test -p 8648:8648 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/iplocate-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8648/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8648/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8648/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop iplocate-mcp-test
```
