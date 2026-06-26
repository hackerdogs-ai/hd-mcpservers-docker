<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# DuckDuckGo MCP Server

MCP server wrapper for [DuckDuckGo](https://duckduckgo.com) — privacy-preserving web search that returns organic results without tracking or requiring an API key.

## What is DuckDuckGo MCP Server?

The DuckDuckGo MCP server provides AI assistants with real-time web search capabilities using DuckDuckGo's search engine. Unlike Google or Bing, DuckDuckGo does not track users or require an API key, making it a straightforward drop-in for anonymous web search in automated workflows.

**No API keys required** — uses DuckDuckGo's public search interface.

**Tools:**
- `duckduckgo_info` — Return status information for the connected DuckDuckGo MCP server.

## Tools Reference

### `duckduckgo_info`

Return basic status for the DuckDuckGo MCP server.

_No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search DuckDuckGo for recent news about the Log4Shell vulnerability."
- "Use DuckDuckGo to find the official documentation page for the Rust programming language."
- "Search for public proof-of-concept exploits for CVE-2024-3094 using DuckDuckGo."
- "Find recent DuckDuckGo results about open-source threat intelligence platforms."
- "Use DuckDuckGo to search for tutorials on setting up a home lab for penetration testing."
- "Search DuckDuckGo for security advisories published this week by CISA."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/duckduckgo-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8413:8413 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8413 \
  hackerdogs/duckduckgo-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "duckduckgo-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/duckduckgo-mcp:latest"],
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
    "duckduckgo-mcp": {
      "url": "http://localhost:8413/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8413` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/duckduckgo-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name duckduckgo-mcp-test -p 8413:8413 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/duckduckgo-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8413/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8413/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8413/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_duckduckgo","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop duckduckgo-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Duckduckgo CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint duckduckgo hackerdogs/duckduckgo-mcp:latest --help
```
