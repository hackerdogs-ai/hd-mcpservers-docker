<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Wiremcp MCP Server

MCP server wrapper for [WireMCP](https://github.com/bstefanescu/wiremcp) — AI-assisted real-time network traffic analysis via Wireshark/tshark.

## What is Wiremcp?

WireMCP is a Model Context Protocol server that connects AI assistants to Wireshark (via the `tshark` command-line tool) for real-time network traffic capture and analysis. It enables AI-driven packet inspection, protocol analysis, traffic filtering, and network troubleshooting without leaving the chat interface. See [bstefanescu/wiremcp](https://github.com/bstefanescu/wiremcp) for full documentation. No API keys are required, but `tshark` must be accessible and the container may need elevated network privileges to capture live traffic.

## Tools Reference

| Tool | Description |
|------|-------------|
| `wiremcp_info` | Return status information for the WireMCP server |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use WireMCP to capture live traffic on interface eth0 for 30 seconds and summarize the protocols seen."
- "Filter HTTP traffic from the last capture using WireMCP and show me the request URIs."
- "Run a tshark capture via WireMCP targeting DNS queries to identify unusual domain lookups."
- "Use WireMCP to analyze a PCAP file and list all unique source/destination IP pairs."
- "Capture traffic on port 443 for 60 seconds using WireMCP and report any TLS handshake anomalies."
- "Use WireMCP to check the status of the Wireshark integration and confirm it is ready to capture."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/wiremcp-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8458:8458 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8458 \
  hackerdogs/wiremcp-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "wiremcp-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/wiremcp-mcp:latest"],
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
    "wiremcp-mcp": {
      "url": "http://localhost:8458/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8458` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/wiremcp-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name wiremcp-mcp-test -p 8458:8458 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/wiremcp-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8458/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8458/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8458/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_wiremcp","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop wiremcp-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Wiremcp CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint wiremcp hackerdogs/wiremcp-mcp:latest --help
```
