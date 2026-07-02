<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS CloudWatch MCP Server

MCP server wrapper for [AWS CloudWatch](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server) — query metrics, search logs with Insights, inspect alarms, and retrieve dashboards for AI-powered cloud observability.

## What is AWS CloudWatch?

AWS CloudWatch is the primary observability service for AWS, collecting metrics from hundreds of services, storing structured log data queryable with CloudWatch Logs Insights, and evaluating alarm conditions across your infrastructure. This MCP server enables AI assistants to pull metric statistics, run Logs Insights queries, describe alarms and their state history, and read dashboard widgets to diagnose outages and performance anomalies. See [awslabs/mcp](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

**Summary.** MCP server wrapper for [AWS CloudWatch](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server) — query CloudWatch metrics, run Logs Insights queries, and inspect alarms and dashboards to troubleshoot AWS infrastructure.

## Tools Reference

| Tool | Description |
|------|-------------|
| `describe_log_groups` | Describe Log Groups |
| `analyze_log_group` | Analyze Log Group |
| `execute_log_insights_query` | Execute Log Insights Query |
| `get_logs_insight_query_results` | Get Logs Insight Query Results |
| `cancel_logs_insight_query` | Cancel Logs Insight Query |
| `execute_cwl_insights_batch` | Execute Cwl Insights Batch |
| `recommend_indexes_loggroup` | Recommend Indexes Loggroup |
| `recommend_indexes_account` | Recommend Indexes Account |
| `get_metric_data` | Get Metric Data |
| `get_metric_metadata` | Get Metric Metadata |
| `analyze_metric` | Analyze Metric |
| `get_recommended_metric_alarms` | Get Recommended Metric Alarms |
| `execute_promql_query` | Execute Promql Query |
| `execute_promql_range_query` | Execute Promql Range Query |
| `get_promql_label_values` | Get Promql Label Values |
| `get_promql_series` | Get Promql Series |
| `get_promql_labels` | Get Promql Labels |
| `get_active_alarms` | Get Active Alarms |
| `get_alarm_history` | Get Alarm History |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Show me the CPUUtilization metric for my EC2 instance i-0abc123 over the last 3 hours."
- "Search my Lambda function logs for ERROR messages in the past 30 minutes."
- "List all CloudWatch alarms that are currently in ALARM state."
- "Run a CloudWatch Logs Insights query to count HTTP 5xx errors by endpoint for the past hour."
- "Show me the p99 latency metric for my ALB target group over the past 24 hours."
- "List all metric alarms for my RDS cluster and show which have triggered in the last week."

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
  hackerdogs/aws-cloudwatch-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8608:8608 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8608 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-cloudwatch-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-cloudwatch-mcp": {
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
        "hackerdogs/aws-cloudwatch-mcp:latest"
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
    "aws-cloudwatch-mcp": {
      "url": "http://localhost:8608/mcp"
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
    "aws-cloudwatch-mcp": {
      "url": "http://localhost:8485/aws-cloudwatch-mcp/mcp",
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
| `MCP_PORT` | `8608` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-cloudwatch-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-cloudwatch-mcp-test -p 8608:8608 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-cloudwatch-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8608/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8608/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8608/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-cloudwatch-mcp-test
```
