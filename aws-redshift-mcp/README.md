<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS Redshift MCP Server

MCP server wrapper for [Amazon Redshift](https://github.com/awslabs/mcp/tree/main/src/redshift-mcp-server) — discover clusters and serverless workgroups, browse schemas, and run analytical SQL queries against Amazon Redshift through natural language.

## What is Amazon Redshift?

Amazon Redshift is AWS's fully managed petabyte-scale cloud data warehouse, supporting both provisioned clusters and serverless compute. This MCP server, built from `awslabs.redshift-mcp-server`, connects to Redshift clusters or serverless endpoints, introspects schemas and table statistics, and executes SQL queries — letting you explore large datasets and run ad-hoc analytics without writing SQL manually. See [awslabs/mcp](https://github.com/awslabs/mcp) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`. A Redshift cluster identifier or serverless workgroup name must also be configured.

## Tools Reference

| Tool | Description |
|------|-------------|
| `list_clusters` | List Clusters |
| `list_databases` | List Databases |
| `list_schemas` | List Schemas |
| `list_tables` | List Tables |
| `list_columns` | List Columns |
| `execute_query` | Execute Query |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all Redshift clusters and serverless workgroups in my account."
- "Show me the schemas and tables available in my 'analytics' Redshift database."
- "How many rows are in the 'fact_sales' table and what is its sort key?"
- "Query total revenue by region for Q4 2024 from the sales data warehouse."
- "Show me the 10 longest-running queries currently executing in Redshift."
- "Describe the distribution style and sort keys for all tables in the 'public' schema."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-redshift-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8621:8621 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8621 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-redshift-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-redshift-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "AWS_REGION",
        "-e",
        "AWS_ACCESS_KEY_ID",
        "-e",
        "AWS_SECRET_ACCESS_KEY",
        "hackerdogs/aws-redshift-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "AWS_REGION": "",
        "AWS_ACCESS_KEY_ID": "",
        "AWS_SECRET_ACCESS_KEY": ""
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
    "aws-redshift-mcp": {
      "url": "http://localhost:8621/mcp"
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
    "aws-redshift-mcp": {
      "url": "http://localhost:8485/aws-redshift-mcp/mcp",
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
| `AWS_REGION` | — | AWS region (e.g. `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | — | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | — | AWS secret access key |
| `MCP_PORT` | `8621` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-redshift-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-redshift-mcp-test -p 8621:8621 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-redshift-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8621/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8621/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8621/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-redshift-mcp-test
```
