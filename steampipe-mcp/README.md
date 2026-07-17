<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Steampipe MCP Server

MCP server wrapper for [Steampipe](https://github.com/turbot/steampipe-mcp) — query cloud infrastructure, SaaS APIs, and security data using SQL.

## What is Steampipe?

Steampipe is an open-source tool that lets you query cloud services (AWS, Azure, GCP, GitHub, Kubernetes, and 140+ others) using standard SQL. It exposes live API data as relational tables so you can join across providers — for example, correlating AWS IAM users with GitHub organization members. This MCP server surfaces Steampipe's SQL query capability to AI assistants for cloud security auditing and compliance checks. See [turbot/steampipe-mcp](https://github.com/turbot/steampipe-mcp) for full documentation.

**Cloud credentials required** — configure provider credentials (e.g. AWS keys, Azure tokens) inside the container for the plugins you wish to query.

**Summary.** MCP server wrapper for [Steampipe](https://github.com/turbot/steampipe-mcp) — query cloud infrastructure, SaaS APIs, and security data using SQL.

## Tools Reference

| Tool | Description |
|------|-------------|
| `list_all_tables` | List All Tables |
| `list_tables_in_schema` | List Tables In Schema |
| `get_table_schema` | Get Table Schema |
| `query` | Query |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Query Steampipe for all publicly accessible S3 buckets in my AWS account."
- "Use Steampipe SQL to list all IAM users that have never logged in."
- "Find all AWS security groups that allow unrestricted inbound access on port 22."
- "Query Steampipe for all GCP service accounts with admin-level permissions."
- "Show me all EC2 instances without CloudWatch monitoring enabled using Steampipe."
- "Use Steampipe to list all GitHub repositories in my organization that have public visibility."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/steampipe-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8668:8668 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8668 \
  hackerdogs/steampipe-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "steampipe-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/steampipe-mcp:latest"
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
    "steampipe-mcp": {
      "url": "http://localhost:8668/mcp"
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
    "steampipe-mcp": {
      "url": "http://localhost:8485/steampipe-mcp/mcp",
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
| `MCP_PORT` | `8668` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/steampipe-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name steampipe-mcp-test -p 8668:8668 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/steampipe-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8668/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8668/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8668/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop steampipe-mcp-test
```
