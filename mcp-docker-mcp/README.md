<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Docker MCP Gateway Server

MCP server wrapper for [Docker MCP Toolkit](https://mcp.docker.com) — local compliance stub and gateway reference for the Docker MCP cloud endpoint.

## What is Docker MCP?

Docker MCP Toolkit is Docker's official MCP gateway that provides a curated catalog of containerized MCP servers, allowing AI agents to securely run tools inside isolated Docker containers. The production service runs at `https://mcp.docker.com/mcp` and provides access to hundreds of pre-built MCP tool servers. This Hackerdogs image is a local compliance stub that surfaces the gateway's remote endpoint URL and is useful for CI/CD pipelines and configuration verification. See [mcp.docker.com](https://mcp.docker.com) for full documentation.

**No API keys required** — this is a local stub. For the full production tool catalog, point your MCP client at `https://mcp.docker.com/mcp`.

**Tools:**
- `remote_endpoint_info` — Return the official Docker MCP remote URL and integration notes.

## Tools Reference

### `remote_endpoint_info`

Return the official remote MCP URL and notes for the Docker MCP Gateway integration.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| (none) | — | — | — | No parameters required |

<details>
<summary>Example response</summary>

```json
{
  "remote_mcp_url": "https://mcp.docker.com/mcp",
  "notes": "Use the remote URL in your MCP client for production tools."
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "What is the Docker MCP Gateway remote endpoint URL?"
- "Check the Docker MCP Gateway stub and return the production endpoint information."
- "Verify that the Docker MCP Gateway integration is correctly configured and return the remote URL."
- "What tools are available through the Docker MCP Toolkit production endpoint?"
- "Return the remote MCP URL from the Docker MCP Gateway server for use in client configuration."
- "Get the Docker MCP remote endpoint info so I can configure my MCP client to point at the production gateway."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/mcp-docker-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8517:8517 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8517 \
  hackerdogs/mcp-docker-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "mcp-docker-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/mcp-docker-mcp:latest"],
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
    "mcp-docker-mcp": {
      "url": "http://localhost:8517/mcp"
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
    "mcp-docker-mcp": {
      "url": "http://localhost:8485/mcp-docker-mcp/mcp",
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
| `MCP_PORT` | `8517` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/mcp-docker-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name mcp-docker-mcp-test -p 8517:8517 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/mcp-docker-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8517/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8517/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8517/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_mcp_docker","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop mcp-docker-mcp-test
```

## Running the tool directly (bypassing MCP)

This server is a Python-based stub with no separate CLI binary. To inspect the server behavior directly, run the Python script:

```bash
docker run -i --rm hackerdogs/mcp-docker-mcp:latest python /app/mcp_server.py
```

For the full Docker MCP Toolkit experience, use the production gateway at `https://mcp.docker.com/mcp`.
