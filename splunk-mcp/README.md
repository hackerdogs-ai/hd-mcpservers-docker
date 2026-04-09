<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Splunk MCP Server

MCP server wrapper for [Splunk](https://github.com/splunk/splunk-mcp) — upstream package `splunk-mcp`.

## What is Splunk?

MCP server for [Splunk](https://www.splunk.com/). Run SPL searches, query indexes, manage saved searches, and access dashboards. Investigate security events and operational data through AI assistants.

**Splunk credentials required** — set `SPLUNK_URL` and `SPLUNK_TOKEN`.

**Summary.** Splunk MCP Server — Dockerized from upstream `splunk-mcp` package.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search Splunk for failed SSH logins in the last 24 hours."
- "Show me the top 10 source IPs in the firewall index."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e SPLUNK_URL \
  -e SPLUNK_TOKEN \
  hackerdogs/splunk-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8667:8667 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8667 \
  -e SPLUNK_URL \
  -e SPLUNK_TOKEN \
  hackerdogs/splunk-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "splunk-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "SPLUNK_URL",
        "-e",
        "SPLUNK_TOKEN",
        "hackerdogs/splunk-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "SPLUNK_URL": "",
        "SPLUNK_TOKEN": ""
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
    "splunk-mcp": {
      "url": "http://localhost:8667/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8667` | HTTP port (only used with `streamable-http`) |
| `SPLUNK_URL` | — | Splunk instance URL (e.g. `https://splunk.example.com:8089`) |
| `SPLUNK_TOKEN` | — | Splunk bearer token or session key |

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
docker build -t hackerdogs/splunk-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name splunk-mcp-test -p 8667:8667 \
  -e MCP_TRANSPORT=streamable-http \
  -e SPLUNK_URL \
  -e SPLUNK_TOKEN \
  hackerdogs/splunk-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8667/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8667/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8667/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop splunk-mcp-test
```
