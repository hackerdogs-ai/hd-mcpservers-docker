<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Acuvity Server Hyperbrowser MCP Server

MCP server wrapper for [Hyperbrowser](https://github.com/hyperbrowserai/mcp) — cloud browser automation and web scraping with built-in anti-detection and session management.

## What is Acuvity Server Hyperbrowser?

Hyperbrowser MCP Server provides cloud-hosted browser sessions that AI assistants can use to scrape web pages, interact with JavaScript-rendered content, navigate multi-step flows, and extract structured data at scale. Hyperbrowser handles proxy rotation, CAPTCHA solving, and browser fingerprinting so agents can access pages that block standard HTTP clients. See [hyperbrowserai/mcp](https://github.com/hyperbrowserai/mcp) for full documentation.

**API key required** — set `HYPERBROWSER_API_KEY` to your Hyperbrowser API key from [hyperbrowser.ai](https://hyperbrowser.ai).

**Tools:**
- `acuvity_mcp_server_hyperbrowser_info` — Return basic info / status for Hyperbrowser MCP Server.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use Hyperbrowser to scrape the product listing from https://example.com/shop and extract names and prices."
- "Open https://app.example.com/login with Hyperbrowser, fill in the credentials, and take a screenshot after login."
- "Use Hyperbrowser to navigate the multi-step checkout flow at https://store.example.com and record each step."
- "Scrape all customer reviews from https://example.com/product/123 including the hidden 'load more' pages."
- "Use Hyperbrowser to extract the table data from https://finance.example.com/reports/q4 as JSON."
- "Run a Hyperbrowser session against https://spa.example.com and return the fully-rendered page HTML."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8427:8427 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8427 \
  hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "acuvity-mcp-server-hyperbrowser-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest"],
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
    "acuvity-mcp-server-hyperbrowser-mcp": {
      "url": "http://localhost:8427/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8427` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name acuvity-mcp-server-hyperbrowser-mcp-test -p 8427:8427 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8427/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8427/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8427/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_acuvity_server_hyperbrowser","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop acuvity-mcp-server-hyperbrowser-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Acuvity Server Hyperbrowser CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint acuvity-server-hyperbrowser hackerdogs/acuvity-mcp-server-hyperbrowser-mcp:latest --help
```
