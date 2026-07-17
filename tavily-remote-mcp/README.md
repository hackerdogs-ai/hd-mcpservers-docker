<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Tavily Remote MCP Server

MCP server wrapper for [Tavily](https://tavily.com) — AI-optimized web search API designed for retrieval-augmented generation and research agents.

## What is Tavily Remote?

Tavily is a search API purpose-built for AI agents and LLM applications, returning clean, structured web search results optimized for RAG pipelines. This image is a local compliance stub that reports the production remote MCP endpoint (`https://mcp.tavily.com/mcp`) — for full search functionality, configure your MCP client to connect directly to `https://mcp.tavily.com/mcp` using a Tavily API key. See [Tavily documentation](https://docs.tavily.com) for full documentation.

**API key required** — sign up at [app.tavily.com](https://app.tavily.com) to get a `TAVILY_API_KEY`. This stub image does not perform live searches; point your MCP client at the hosted endpoint.

**Summary.** MCP server wrapper for [Tavily](https://tavily.com) — AI-optimized web search API; this image is a local stub pointing to the production endpoint at `https://mcp.tavily.com/mcp`.

**Tools:**
- `remote_endpoint_info` — Return the official remote MCP URL and usage notes for connecting to Tavily's hosted search service.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Show me the remote endpoint URL for the Tavily MCP service."
- "What is the production MCP URL I should configure in my client to use Tavily search?"
- "Confirm the Tavily remote MCP endpoint is reachable and return its connection details."
- "Use the Tavily stub to find out which hosted URL to point my AI agent at for web search."
- "Get the connection info for the Tavily search MCP server."
- "What API endpoint should I use to connect to Tavily's full MCP search tools?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/tavily-remote-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8513:8513 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8513 \
  hackerdogs/tavily-remote-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "tavily-remote-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/tavily-remote-mcp:latest"],
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
    "tavily-remote-mcp": {
      "url": "http://localhost:8513/mcp"
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
    "tavily-remote-mcp": {
      "url": "http://localhost:8485/tavily-remote-mcp/mcp",
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
| `MCP_PORT` | `8513` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/tavily-remote-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name tavily-remote-mcp-test -p 8513:8513 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/tavily-remote-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8513/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8513/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8513/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_tavily_remote","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop tavily-remote-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Tavily Remote CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint tavily-remote hackerdogs/tavily-remote-mcp:latest --help
```
