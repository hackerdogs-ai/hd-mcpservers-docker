<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Cloudflare MCP Server

MCP server wrapper for [Cloudflare](https://github.com/cloudflare/mcp-server-cloudflare) — manage Workers, DNS, KV, R2, D1, and Pages through the Cloudflare API.

## What is Cloudflare?

The official `@cloudflare/mcp-server-cloudflare` package exposes Cloudflare's management API as MCP tools. You can manage Workers (deploy, list, delete scripts), KV namespaces (read/write keys), R2 buckets (list/upload/delete objects), D1 databases (run SQL queries), DNS zones and records, and Cloudflare Pages projects — all from an AI assistant. See [github.com/cloudflare/mcp-server-cloudflare](https://github.com/cloudflare/mcp-server-cloudflare) for full documentation.

**API token required** — create a token at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) with the appropriate scopes, and set `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all Cloudflare Workers in my account and show their route bindings."
- "Show all DNS records for the zone example.com in Cloudflare."
- "Deploy a new Cloudflare Worker script that returns 'Hello World' on all requests."
- "List the contents of my R2 bucket named 'assets-prod'."
- "Run a SQL query against my D1 database 'app-db' to count all users."
- "Add an A record pointing www.example.com to 203.0.113.10 in Cloudflare DNS."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e CLOUDFLARE_API_TOKEN \
  -e CLOUDFLARE_ACCOUNT_ID \
  hackerdogs/cloudflare-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8633:8633 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8633 \
  -e CLOUDFLARE_API_TOKEN \
  -e CLOUDFLARE_ACCOUNT_ID \
  hackerdogs/cloudflare-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "cloudflare-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "CLOUDFLARE_API_TOKEN",
        "-e",
        "CLOUDFLARE_ACCOUNT_ID",
        "hackerdogs/cloudflare-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "CLOUDFLARE_API_TOKEN": "",
        "CLOUDFLARE_ACCOUNT_ID": ""
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
    "cloudflare-mcp": {
      "url": "http://localhost:8633/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8633` | HTTP port (only used with `streamable-http`) |
| `CLOUDFLARE_API_TOKEN` | — | Cloudflare API token with appropriate permissions |
| `CLOUDFLARE_ACCOUNT_ID` | — | Cloudflare account ID |

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
docker build -t hackerdogs/cloudflare-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name cloudflare-mcp-test -p 8633:8633 \
  -e MCP_TRANSPORT=streamable-http \
  -e CLOUDFLARE_API_TOKEN \
  -e CLOUDFLARE_ACCOUNT_ID \
  hackerdogs/cloudflare-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8633/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8633/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8633/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop cloudflare-mcp-test
```
