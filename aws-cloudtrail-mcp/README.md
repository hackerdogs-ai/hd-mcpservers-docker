<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS CloudTrail MCP Server

MCP server wrapper for [AWS CloudTrail](https://github.com/awslabs/mcp/tree/main/src/cloudtrail-mcp-server) — query and analyze AWS account activity logs for security investigations, compliance auditing, and operational troubleshooting.

## What is AWS CloudTrail?

AWS CloudTrail records every API call made in your AWS account — who made it, what they did, and from where. This MCP server lets AI assistants search CloudTrail event history and data event logs to answer security questions such as "who changed this S3 bucket policy?", "what actions did this IAM role take last night?", or "which resources were accessed from this IP address?". See [awslabs/mcp](https://github.com/awslabs/mcp/tree/main/src/cloudtrail-mcp-server) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

**Summary.** MCP server wrapper for [AWS CloudTrail](https://github.com/awslabs/mcp/tree/main/src/cloudtrail-mcp-server) — search and analyze API activity logs across your AWS account for security and compliance investigations.

## Tools Reference

| Tool | Description |
|------|-------------|
| `lookup_events` | Lookup Events |
| `lake_query` | Lake Query |
| `get_query_status` | Get Query Status |
| `get_query_results` | Get Query Results |
| `list_event_data_stores` | List Event Data Stores |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Show me all CloudTrail events for the IAM user 'john.doe' in the last 24 hours."
- "Find all S3 DeleteObject events in us-east-1 from the past week."
- "Who created or modified security groups in my account yesterday?"
- "List all CloudTrail trails configured in my account and show which regions they cover."
- "Show me any root account login events from the past 30 days."
- "Find all API calls made from IP address 203.0.113.45 in the last 7 days."

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
  hackerdogs/aws-cloudtrail-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8606:8606 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8606 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-cloudtrail-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-cloudtrail-mcp": {
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
        "hackerdogs/aws-cloudtrail-mcp:latest"
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
    "aws-cloudtrail-mcp": {
      "url": "http://localhost:8606/mcp"
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
    "aws-cloudtrail-mcp": {
      "url": "http://localhost:8485/aws-cloudtrail-mcp/mcp",
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
| `MCP_PORT` | `8606` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-cloudtrail-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-cloudtrail-mcp-test -p 8606:8606 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-cloudtrail-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8606/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8606/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8606/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-cloudtrail-mcp-test
```
