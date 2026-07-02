<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Sqlmap MCP Server

MCP server wrapper for [sqlmap](https://github.com/sqlmapproject/sqlmap) — automated detection and exploitation of SQL injection vulnerabilities.

## What is Sqlmap?

Sqlmap is an open-source penetration testing tool that automates the detection and exploitation of SQL injection flaws, supporting backends including MySQL, PostgreSQL, Oracle, MSSQL, SQLite, and more. It can enumerate databases, extract data, read/write files on the server, and in some cases execute OS commands via database out-of-band techniques. See [sqlmapproject/sqlmap](https://github.com/sqlmapproject/sqlmap) for full documentation.

**No API keys required** — sqlmap runs locally inside the Docker container.

**Summary.** MCP server wrapper for [sqlmap](https://github.com/sqlmapproject/sqlmap) — automated detection and exploitation of SQL injection vulnerabilities.

**Tools:**
- `run_sqlmap` — Run sqlmap with CLI arguments (e.g. example.com).

## Tools Reference

### `run_sqlmap`

Run sqlmap with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "sqlmap output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Test http://testphp.vulnweb.com/listproducts.php?cat=1 for SQL injection using sqlmap."
- "Run sqlmap against the login form at http://target.local/login.php and try to enumerate databases."
- "Use sqlmap with --dbs to list all databases on the target URL http://example.com/page?id=1."
- "Run sqlmap with --level=3 --risk=2 for a thorough SQL injection test on http://target.com/item?id=5."
- "Use sqlmap to dump the users table from the targetdb database on http://example.com/page?id=1."
- "Run sqlmap with --batch --forms to automatically test all forms on http://target.local/."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/sqlmap-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8394:8394 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8394 \
  hackerdogs/sqlmap-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "sqlmap-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/sqlmap-mcp:latest"],
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
    "sqlmap-mcp": {
      "url": "http://localhost:8394/mcp"
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
    "sqlmap-mcp": {
      "url": "http://localhost:8485/sqlmap-mcp/mcp",
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
| `MCP_PORT` | `8394` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/sqlmap-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name sqlmap-mcp-test -p 8394:8394 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/sqlmap-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8394/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8394/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8394/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_sqlmap","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop sqlmap-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Sqlmap CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint sqlmap hackerdogs/sqlmap-mcp:latest --help
```
