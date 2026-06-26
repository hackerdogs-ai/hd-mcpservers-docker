<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Adguard Dns MCP Server

MCP server wrapper for AdGuard DNS — check if hostnames are blocked by AdGuard's public DNS filtering resolvers.

## What is AdGuard DNS?

AdGuard DNS is a public DNS-based filtering service that blocks ads, trackers, and malicious domains at the DNS level. This MCP server queries AdGuard's default resolver (94.140.14.14) and/or family-safe resolver (94.140.15.15) to determine if a hostname is blocked, detecting the characteristic blocked-response IP (94.140.14.35). It is useful for threat intelligence workflows, ad/tracker classification, and parental-control testing. No API keys are required; DNS queries are made directly to AdGuard's public resolvers.

**Tools:**
- `adguard_dns_check` — Check if a host is blocked by AdGuard DNS (default, family, or both modes).

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Check if the hostname ads.example.com is blocked by AdGuard DNS default mode."
- "Is tracker.analytics.io blocked by AdGuard's family-safe DNS resolver?"
- "Check malware-site.com against both AdGuard DNS default and family resolvers."
- "Use AdGuard DNS to determine whether doubleclick.net is treated as a tracker and blocked."
- "Check a list of suspicious hostnames from my threat intel feed against AdGuard DNS."
- "Is adservice.google.com blocked by AdGuard DNS? Show the raw resolver response."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/adguard-dns-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8509:8509 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8509 \
  hackerdogs/adguard-dns-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "adguard-dns-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/adguard-dns-mcp:latest"],
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
    "adguard-dns-mcp": {
      "url": "http://localhost:8509/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8509` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/adguard-dns-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name adguard-dns-mcp-test -p 8509:8509 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/adguard-dns-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8509/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8509/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8509/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_adguard_dns","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop adguard-dns-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Adguard Dns CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint adguard-dns hackerdogs/adguard-dns-mcp:latest --help
```
