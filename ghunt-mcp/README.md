<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# GHunt MCP Server

MCP server wrapper for [GHunt](https://github.com/mxrch/GHunt) — Google account OSINT (emails, Gaia IDs, documents).

## What is GHunt?

GHunt (ghunt) is a security tool that provides: **Google account OSINT — investigates emails, Gaia IDs, and Google Docs to extract account metadata, profile photos, connected services, and more.**

See [mxrch/GHunt](https://github.com/mxrch/GHunt) for full documentation.

**No API keys required** — GHunt runs locally inside the Docker container. Some advanced features may require Google authentication cookies.

**Summary.** MCP server wrapper for [GHunt](https://github.com/mxrch/GHunt) — Google account OSINT (emails, Gaia IDs, documents).

**Tools:**
- `run_ghunt` — Run ghunt with the given arguments. Returns structured JSON output.


## Tools Reference

### `run_ghunt`

Run ghunt with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"email user@gmail.com"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "ghunt output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use ghunt to investigate the Google account user@gmail.com."
- "Look up Google Gaia ID 123456789 using ghunt."
- "Run ghunt email lookup on target@gmail.com and summarize the profile."
- "Use ghunt to check what Google services are linked to this email."
- "Show me all available ghunt subcommands with --help."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/ghunt-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8218:8218 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8218 \
  hackerdogs/ghunt-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "ghunt-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/ghunt-mcp:latest"],
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
    "ghunt-mcp": {
      "url": "http://localhost:8218/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8218` | HTTP port (only used with `streamable-http`) |
| `GHUNT_BIN` | `ghunt` | Path or name of the GHunt binary |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use ghunt to investigate user@gmail.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/ghunt-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name ghunt-mcp-test -p 8218:8218 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/ghunt-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8218/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8218/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8218/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_ghunt","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop ghunt-mcp-test
```


## Running the tool directly (bypassing MCP)

You can run GHunt directly in the same container by overriding the entrypoint to investigate Google accounts without starting the MCP server.

**Show help:**

```bash
docker run --rm --entrypoint ghunt hackerdogs/ghunt-mcp:latest --help
```

**Investigate an email:**

```bash
docker run --rm --entrypoint ghunt hackerdogs/ghunt-mcp:latest email user@gmail.com
```
