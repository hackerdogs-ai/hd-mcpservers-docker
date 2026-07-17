<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Chrome DevTools MCP Server

MCP server wrapper for [Chrome DevTools Protocol](https://github.com/hangxingliu/mcp-chrome-devtools) — upstream package `@mcp-b/chrome-devtools-mcp`.

## What is Chrome DevTools?

The `@mcp-b/chrome-devtools-mcp` package exposes the Chrome DevTools Protocol (CDP) as MCP tools, allowing AI assistants to interact with a running Chrome instance. With it you can navigate pages, execute JavaScript in the browser context, inspect and modify the DOM, intercept and analyze network requests, and capture screenshots — enabling full browser automation and web app debugging workflows. See [github.com/hangxingliu/mcp-chrome-devtools](https://github.com/hangxingliu/mcp-chrome-devtools) for full documentation.

**No API keys required** — connects to a Chrome instance with remote debugging enabled (pass the CDP WebSocket URL or use a local Chrome).

## Tools Reference

| Tool | Description |
|------|-------------|
| `click` | Click |
| `close_page` | Close Page |
| `drag` | Drag |
| `emulate` | Emulate |
| `evaluate_script` | Evaluate Script |
| `fill` | Fill |
| `fill_form` | Fill Form |
| `get_console_message` | Get Console Message |
| `get_network_request` | Get Network Request |
| `handle_dialog` | Handle Dialog |
| `hover` | Hover |
| `lighthouse_audit` | Lighthouse Audit |
| `list_console_messages` | List Console Messages |
| `list_network_requests` | List Network Requests |
| `list_pages` | List Pages |
| `navigate_page` | Navigate Page |
| `new_page` | New Page |
| `performance_analyze_insight` | Performance Analyze Insight |
| `performance_start_trace` | Performance Start Trace |
| `performance_stop_trace` | Performance Stop Trace |
| `press_key` | Press Key |
| `resize_page` | Resize Page |
| `select_page` | Select Page |
| `take_heapsnapshot` | Take Heapsnapshot |
| `take_screenshot` | Take Screenshot |
| `take_snapshot` | Take Snapshot |
| `type_text` | Type Text |
| `upload_file` | Upload File |
| `wait_for` | Wait For |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Navigate to https://example.com and take a screenshot of the full page."
- "Execute JavaScript on the active tab to extract all anchor tags and their hrefs."
- "Intercept network requests on the current page and show me any XHR calls to /api/."
- "Inspect the DOM of the login form at https://staging.myapp.com and return the input field names."
- "Run a performance audit on https://example.com by checking network timing via Chrome DevTools."
- "Use Chrome DevTools to set a breakpoint-style event listener and capture all console.log output on the page."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/chrome-devtools-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8631:8631 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8631 \
  hackerdogs/chrome-devtools-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "chrome-devtools-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/chrome-devtools-mcp:latest"
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
    "chrome-devtools-mcp": {
      "url": "http://localhost:8631/mcp"
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
    "chrome-devtools-mcp": {
      "url": "http://localhost:8485/chrome-devtools-mcp/mcp",
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
| `MCP_PORT` | `8631` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/chrome-devtools-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name chrome-devtools-mcp-test -p 8631:8631 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/chrome-devtools-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8631/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8631/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8631/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop chrome-devtools-mcp-test
```
