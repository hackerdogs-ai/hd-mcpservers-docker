<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Xpoz Server MCP Server

MCP server wrapper for [XPoz](https://xpoz.io) — local compliance stub that points to the hosted production MCP endpoint at https://mcp.xpoz.io/mcp.

## What is XPoz?

XPoz is a social intelligence platform for OSINT investigations, providing tools to discover and aggregate public social media profiles, digital footprints, and open-source data across the web. This Docker image is a local compliance stub — the single `remote_endpoint_info` tool returns the official production MCP URL (`https://mcp.xpoz.io/mcp`) where the full XPoz toolset is available. Connect your MCP client directly to the production endpoint for social intelligence queries. No API keys are required to query the stub; the production endpoint may require credentials from [xpoz.io](https://xpoz.io).

## Tools Reference

| Tool | Description |
|------|-------------|
| `remote_endpoint_info` | Returns the production MCP URL and connection notes for the XPoz social intelligence service |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "What is the production MCP endpoint URL for XPoz?"
- "Get the XPoz remote MCP connection details so I can configure my client for social intelligence lookups."
- "Return the remote endpoint info for the XPoz integration."
- "I want to use XPoz to search for public profiles — what MCP URL should I connect to?"
- "Show me how to connect to the XPoz production MCP server."
- "What tools are available through the XPoz MCP production endpoint at xpoz.io?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/xpoz-mcp-server-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8510:8510 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8510 \
  hackerdogs/xpoz-mcp-server-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "xpoz-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/xpoz-mcp-server-mcp:latest"],
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
    "xpoz-mcp-server-mcp": {
      "url": "http://localhost:8510/mcp"
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
    "xpoz-mcp-server-mcp": {
      "url": "http://localhost:8485/xpoz-mcp-server-mcp/mcp",
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
| `MCP_PORT` | `8510` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/xpoz-mcp-server-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name xpoz-mcp-server-mcp-test -p 8510:8510 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/xpoz-mcp-server-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8510/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8510/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8510/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_xpoz_server","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop xpoz-mcp-server-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Xpoz Server CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint xpoz-server hackerdogs/xpoz-mcp-server-mcp:latest --help
```
