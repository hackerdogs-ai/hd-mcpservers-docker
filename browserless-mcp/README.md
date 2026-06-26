<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Browserless MCP Server

MCP server wrapper for [Browserless](https://browserless.io) — headless Chrome automation for content rendering, screenshots, PDFs, and scraping.

## What is Browserless?

Browserless is a headless Chrome-as-a-service platform that runs a managed Chrome instance accessible over HTTP. This MCP server connects to a Browserless endpoint (cloud or self-hosted) to render JavaScript-heavy pages, capture full-page screenshots, generate PDFs, and scrape specific DOM elements via CSS selectors — ideal for testing web apps or extracting data from pages that require a real browser. See [browserless.io](https://browserless.io) for full documentation.

**API key optional** — works with a self-hosted Browserless instance at `BROWSERLESS_URL` without a key, or set `BROWSERLESS_API_KEY` for the cloud service.

**Tools:**
- `browserless_content` — Render a URL in Chrome and return the full HTML content.
- `browserless_screenshot` — Capture a PNG screenshot of a URL (supports full-page).
- `browserless_pdf` — Generate a PDF from a URL.
- `browserless_scrape` — Extract specific DOM elements from a URL using a CSS selector.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Take a full-page screenshot of https://example.com using Browserless."
- "Render https://app.example.com and return the fully loaded HTML."
- "Generate a PDF of https://example.com/report and save it."
- "Scrape the table with selector '.pricing-table' from https://example.com/pricing."
- "Capture a screenshot of the login page at https://staging.myapp.com to check the UI."
- "Use Browserless to extract all text within '#main-content' from a JavaScript-rendered page."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/browserless-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8518:8518 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8518 \
  hackerdogs/browserless-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "browserless-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/browserless-mcp:latest"],
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
    "browserless-mcp": {
      "url": "http://localhost:8518/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8518` | HTTP port (only used with `streamable-http`) |
| `BROWSERLESS_API_KEY` | `` | Browserless api key |

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
docker build -t hackerdogs/browserless-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name browserless-mcp-test -p 8518:8518 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/browserless-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8518/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8518/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8518/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_browserless","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop browserless-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Browserless CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint browserless hackerdogs/browserless-mcp:latest --help
```
