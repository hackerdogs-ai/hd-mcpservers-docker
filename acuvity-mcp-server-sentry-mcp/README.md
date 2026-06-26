<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Acuvity Server Sentry MCP Server

MCP server wrapper for [Sentry](https://github.com/acuvity/mcp-servers) — retrieve and analyze application error issues from Sentry.io via the Acuvity MCP server.

## What is Acuvity Server Sentry?

The Acuvity Sentry MCP server connects AI models to the Sentry.io error monitoring platform, allowing retrieval and analysis of application issues, stack traces, and error trends. It exposes Sentry's issue tracking capabilities through the MCP protocol so you can query, triage, and analyze production errors without leaving your AI workflow. **A Sentry API token is required** — set it as an environment variable before starting the server.

**Tools:**
- `run_acuvity_server_sentry` — Run acuvity-server-sentry with the given arguments.

## Tools Reference


## Tools Reference

| Tool | Description |
|------|-------------|
| `acuvity_mcp_server_sentry_info` | Return basic info / status for Sentry MCP Server. |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List the top 10 unresolved Sentry issues for my project and summarize their root causes."
- "Fetch the stack trace for Sentry issue PROJ-1234 and explain what is causing the error."
- "Show me all Sentry issues that occurred in the last 24 hours with severity level 'fatal'."
- "Query Sentry for errors related to 'NullPointerException' in the backend service."
- "Retrieve Sentry issue details for event ID abc123 and suggest a fix."
- "List all Sentry issues assigned to me that are still unresolved."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-sentry-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8452:8452 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8452 \
  hackerdogs/acuvity-mcp-server-sentry-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "acuvity-mcp-server-sentry-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/acuvity-mcp-server-sentry-mcp:latest"],
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
    "acuvity-mcp-server-sentry-mcp": {
      "url": "http://localhost:8452/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8452` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/acuvity-mcp-server-sentry-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name acuvity-mcp-server-sentry-mcp-test -p 8452:8452 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/acuvity-mcp-server-sentry-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8452/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8452/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8452/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_acuvity_server_sentry","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop acuvity-mcp-server-sentry-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Acuvity Server Sentry CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint acuvity-server-sentry hackerdogs/acuvity-mcp-server-sentry-mcp:latest --help
```
