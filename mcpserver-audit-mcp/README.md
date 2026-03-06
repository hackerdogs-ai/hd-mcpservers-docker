<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# MCPServer Audit MCP Server

MCP server wrapper for [MCPServer Audit](https://github.com/ModelContextProtocol-Security/mcpserver-audit) — Security auditing tool for MCP servers.

## What is MCPServer Audit?

MCPServer Audit (mcpserver-audit) is a security tool that provides: **Security auditing tool for MCP servers.**

See [ModelContextProtocol-Security/mcpserver-audit](https://github.com/ModelContextProtocol-Security/mcpserver-audit) for full documentation.

**No API keys required** — MCPServer Audit runs locally inside the Docker container.

**Summary.** MCP server wrapper for [MCPServer Audit](https://github.com/ModelContextProtocol-Security/mcpserver-audit) — Security auditing tool for MCP servers.

**Tools:**
- `run_mcpserver_audit` — Run mcpserver-audit with the given arguments. Returns structured JSON output.


## Tools Reference

### `run_mcpserver_audit`

Run mcpserver-audit with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "mcpserver-audit output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run mcpserver-audit with --help to see all available options."
- "Use mcpserver-audit to scan the target 192.168.1.1."
- "What options does mcpserver-audit support? Show me its help output."
- "Run mcpserver-audit against example.com with default settings."
- "Execute mcpserver-audit with verbose output enabled."
- "Use the mcpserver-audit tool to analyze the target and report findings."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/mcpserver-audit-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8340:8340 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8340 \
  hackerdogs/mcpserver-audit-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "mcpserver-audit-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/mcpserver-audit-mcp:latest"
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
    "mcpserver-audit-mcp": {
      "url": "http://localhost:8340/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8340` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/mcpserver-audit-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name mcpserver-audit-mcp-test -p 8340:8340 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/mcpserver-audit-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8340/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8340/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8340/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_mcpserver_audit","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop mcpserver-audit-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run the mcpserver-audit CLI in the same container by overriding the entrypoint to audit MCP server configurations without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint mcpserver-audit hackerdogs/mcpserver-audit-mcp:latest --help
```