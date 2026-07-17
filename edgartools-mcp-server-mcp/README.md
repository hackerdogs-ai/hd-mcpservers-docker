<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Edgartools MCP Server

MCP server wrapper for [edgartools](https://github.com/dgunning/edgartools) — retrieve and parse SEC EDGAR filings including 10-K annual reports, 10-Q quarterly reports, 8-K current reports, and proxy statements.

## What is Edgartools?

EdgarTools is a Python library that provides a clean programmatic interface for the SEC EDGAR document store. It supports all major SEC form types (10-K, 10-Q, 8-K, DEF 14A, S-1, and more), automatically parses XBRL financial data, and surfaces company facts, financial statements, and filing metadata. See [dgunning/edgartools](https://github.com/dgunning/edgartools) for full documentation.

**No API keys required** — uses the public SEC EDGAR REST API.

**Tools:**
- `edgartools_mcp_server_info` — Return status information for the connected EdgarTools MCP server.

## Tools Reference

### `edgartools_mcp_server_info`

Return basic status for the EdgarTools MCP server.

_No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Fetch Apple's most recent 10-K annual report from SEC EDGAR and summarize the risk factors section."
- "Retrieve Tesla's last four 10-Q filings and compare revenue quarter over quarter."
- "Pull the latest 8-K current report filed by Microsoft and summarize the disclosed event."
- "Get the DEF 14A proxy statement for Amazon and extract executive compensation tables."
- "Search SEC EDGAR for all S-1 IPO filings in the cybersecurity sector from the last 12 months."
- "Use edgartools to extract the balance sheet and income statement from a company's 10-K XBRL data."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/edgartools-mcp-server-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8415:8415 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8415 \
  hackerdogs/edgartools-mcp-server-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "edgartools-mcp-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/edgartools-mcp-server-mcp:latest"],
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
    "edgartools-mcp-server-mcp": {
      "url": "http://localhost:8415/mcp"
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
    "edgartools-mcp-server-mcp": {
      "url": "http://localhost:8485/edgartools-mcp-server-mcp/mcp",
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
| `MCP_PORT` | `8415` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/edgartools-mcp-server-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name edgartools-mcp-server-mcp-test -p 8415:8415 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/edgartools-mcp-server-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8415/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8415/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8415/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_edgartools_server","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop edgartools-mcp-server-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Edgartools Server CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint edgartools-server hackerdogs/edgartools-mcp-server-mcp:latest --help
```
