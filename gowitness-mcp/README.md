<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Gowitness MCP Server

MCP server wrapper for [Gowitness](https://github.com/sensepost/gowitness) — headless Chrome screenshot tool for web reconnaissance.

## What is Gowitness?

Gowitness is a web screenshot utility that uses a headless Chromium browser to capture screenshots of web targets at scale, making it ideal for quickly surveying large numbers of URLs discovered during reconnaissance. It supports scanning single URLs, lists of URLs, Nmap XML output, and CIDR ranges, and stores results in a local database with a built-in web UI. See [sensepost/gowitness](https://github.com/sensepost/gowitness) for full documentation.

**No API keys required** — Gowitness runs locally inside the Docker container using the bundled Chromium browser.

**Tools:**
- `run_gowitness` — Run gowitness with CLI arguments (e.g. example.com).

## Tools Reference

### `run_gowitness`

Run gowitness with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "gowitness output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use gowitness to take a screenshot of https://example.com and save the result."
- "Run gowitness scan on a list of URLs from urls.txt and capture screenshots of each."
- "Screenshot all HTTP/HTTPS services discovered by nmap on 192.168.1.0/24 using gowitness."
- "Use gowitness to scan the CIDR range 10.0.0.0/24 for web services and take screenshots."
- "Run gowitness against example.com with a custom user-agent to bypass basic bot detection."
- "Use gowitness to take a screenshot of https://internal.corp and report what the page looks like."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/gowitness-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8397:8397 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8397 \
  hackerdogs/gowitness-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "gowitness-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/gowitness-mcp:latest"],
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
    "gowitness-mcp": {
      "url": "http://localhost:8397/mcp"
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
    "gowitness-mcp": {
      "url": "http://localhost:8485/gowitness-mcp/mcp",
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
| `MCP_PORT` | `8397` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/gowitness-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name gowitness-mcp-test -p 8397:8397 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/gowitness-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8397/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8397/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8397/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_gowitness","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop gowitness-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Gowitness CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint gowitness hackerdogs/gowitness-mcp:latest --help
```
