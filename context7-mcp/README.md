<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Context7 MCP Server

MCP server wrapper for [Context7](https://github.com/upstash/context7-mcp) — fetch live library documentation and code examples to eliminate hallucinated API references.

## What is Context7?

Context7 is an Upstash service that injects accurate, version-specific library documentation and code examples directly into your AI assistant's context window. It resolves package names to their canonical docs, preventing outdated or fabricated API calls. See [upstash/context7-mcp](https://github.com/upstash/context7-mcp) for full documentation.

**No API keys required** — this server works out of the box.

## Tools Reference

| Tool | Description |
|------|-------------|
| `resolve-library-id` | Resolve Library Id |
| `query-docs` | Query Docs |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use Context7 to fetch the latest Next.js App Router documentation."
- "Look up the Prisma ORM `findMany` API and show me a working code example."
- "Retrieve the FastAPI dependency injection docs so I can write a correct endpoint."
- "Show me the current React `useEffect` hook signature and usage examples from the official docs."
- "Fetch the LangChain Python SDK docs for building a retrieval-augmented generation chain."
- "Use Context7 to get the Tailwind CSS v4 configuration reference."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/context7-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8634:8634 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8634 \
  hackerdogs/context7-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "context7-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/context7-mcp:latest"
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
    "context7-mcp": {
      "url": "http://localhost:8634/mcp"
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
    "context7-mcp": {
      "url": "http://localhost:8485/context7-mcp/mcp",
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
| `MCP_PORT` | `8634` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/context7-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name context7-mcp-test -p 8634:8634 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/context7-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8634/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8634/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8634/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop context7-mcp-test
```
