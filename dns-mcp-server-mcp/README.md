<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# DNS MCP Server

MCP server wrapper for [dns-mcp-server](https://github.com/cenemiljezweb/dns-mcp-server) — perform DNS record lookups (A, AAAA, MX, TXT, NS, CNAME, SOA) directly from your AI assistant.

## What is DNS MCP Server?

The DNS MCP Server provides structured DNS resolution capabilities to AI assistants, allowing them to query any record type for any domain using the system resolver. It is useful for reconnaissance, verifying mail configuration, debugging DNS propagation, and validating SPF/DKIM/DMARC records. See [cenemiljezweb/dns-mcp-server](https://github.com/cenemiljezweb/dns-mcp-server) for full documentation.

**No API keys required** — uses standard DNS resolution.

## Tools Reference

| Tool | Description |
|------|-------------|
| `dns_lookup` | Dns Lookup |
| `reverse_dns` | Reverse Dns |
| `batch_dns` | Batch Dns |
| `dns_trace` | Dns Trace |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Look up the MX records for gmail.com and list all mail servers in priority order."
- "Resolve the A and AAAA records for github.com."
- "Fetch the TXT records for example.com to check SPF and DMARC policy."
- "Query the NS records for a domain to identify its authoritative name servers."
- "Resolve the CNAME chain for a subdomain to trace where it ultimately points."
- "Check the SOA record for a domain to find the primary nameserver and serial number."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/dns-mcp-server-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8635:8635 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8635 \
  hackerdogs/dns-mcp-server-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "dns-mcp-server-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/dns-mcp-server-mcp:latest"
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
    "dns-mcp-server-mcp": {
      "url": "http://localhost:8635/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8635` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/dns-mcp-server-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name dns-mcp-server-mcp-test -p 8635:8635 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/dns-mcp-server-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8635/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8635/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8635/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop dns-mcp-server-mcp-test
```
