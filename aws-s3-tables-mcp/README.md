<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS S3 Tables MCP Server

MCP server wrapper for [AWS S3 Tables](https://github.com/awslabs/mcp/tree/main/src/s3-tables-mcp-server) — create, query, and manage Apache Iceberg tables stored natively in Amazon S3 using the S3 Tables service.

## What is AWS S3 Tables?

Amazon S3 Tables is a managed table storage service that brings native Apache Iceberg support to S3, offering built-in compaction, snapshot management, and optimized query performance for analytics workloads. This MCP server, built from `awslabs.s3-tables-mcp-server`, lets you list table buckets, browse namespaces and tables, inspect table metadata and schemas, and run queries against Iceberg tables — all through natural language. See [awslabs/mcp](https://github.com/awslabs/mcp) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `list_table_buckets` | List Table Buckets |
| `list_namespaces` | List Namespaces |
| `list_tables` | List Tables |
| `create_table_bucket` | Create Table Bucket |
| `create_namespace` | Create Namespace |
| `create_table` | Create Table |
| `get_table_maintenance_config` | Get Table Maintenance Config |
| `get_maintenance_job_status` | Get Maintenance Job Status |
| `get_table_metadata_location` | Get Table Metadata Location |
| `rename_table` | Rename Table |
| `update_table_metadata_location` | Update Table Metadata Location |
| `query_database` | Query Database |
| `import_csv_to_table` | Import Csv To Table |
| `import_parquet_to_table` | Import Parquet To Table |
| `get_bucket_metadata_config` | Get Bucket Metadata Config |
| `append_rows_to_table` | Append Rows To Table |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all S3 table buckets in my account and their creation dates."
- "Show me the namespaces and tables in my 'analytics-bucket' S3 table bucket."
- "Describe the schema for the 'events' Iceberg table including partition spec."
- "What are the current snapshots and data files for the 'orders' table?"
- "Query the 'clickstream' table to count events by type for the last 7 days."
- "Show the compaction and maintenance settings for all tables in my S3 table bucket."

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
  hackerdogs/aws-s3-tables-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8622:8622 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8622 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-s3-tables-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-s3-tables-mcp": {
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
        "hackerdogs/aws-s3-tables-mcp:latest"
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
    "aws-s3-tables-mcp": {
      "url": "http://localhost:8622/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `AWS_REGION` | — | AWS region (e.g. `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | — | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | — | AWS secret access key |
| `MCP_PORT` | `8622` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-s3-tables-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-s3-tables-mcp-test -p 8622:8622 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-s3-tables-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8622/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8622/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8622/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-s3-tables-mcp-test
```
