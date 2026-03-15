<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Maigret MCP Server

MCP server wrapper for [Maigret](https://github.com/soxoj/maigret) — Username OSINT across 3000+ sites with false-positive detection.

## What is Maigret?

Maigret (maigret) is a security tool that provides: **Username OSINT across 3000+ sites with false-positive detection.**

See [soxoj/maigret](https://github.com/soxoj/maigret) for full documentation.

**No API keys required** — Maigret runs locally inside the Docker container.

**Summary.** MCP server wrapper for [Maigret](https://github.com/soxoj/maigret) — Username OSINT across 3000+ sites with false-positive detection.

**Tools:**
- `run_maigret` — Run maigret with the given arguments. Returns structured JSON output.

## Tools Reference

### `run_maigret`

Run maigret with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"johndoe"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "maigret output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search for username 'johndoe' across all sites using maigret."
- "Use maigret to find all accounts for username 'target_user' with JSON output."
- "Run maigret on 'suspicious_user' with a 30 second timeout."
- "Generate a detailed OSINT report for username 'analyst01' using maigret."
- "Show me all available maigret options with --help."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/maigret-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8221:8221 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8221 \
  hackerdogs/maigret-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "maigret-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/maigret-mcp:latest"],
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
    "maigret-mcp": {
      "url": "http://localhost:8221/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8221` | HTTP port (only used with `streamable-http`) |
| `MAIGRET_BIN` | `maigret` | Path or name of the Maigret binary |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use maigret to search for username 'johndoe'"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/maigret-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name maigret-mcp-test -p 8221:8221 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/maigret-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8221/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8221/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8221/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_maigret","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop maigret-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run Maigret directly in the same container by overriding the entrypoint to run username OSINT without starting the MCP server.

**Show help:**

```bash
docker run --rm --entrypoint maigret hackerdogs/maigret-mcp:latest --help
```

**Search for username:**

```bash
docker run --rm --entrypoint maigret hackerdogs/maigret-mcp:latest johndoe
```

**Search with timeout:**

```bash
docker run --rm --entrypoint maigret hackerdogs/maigret-mcp:latest johndoe --timeout 30
```
