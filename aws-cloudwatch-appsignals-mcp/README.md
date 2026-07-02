<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS CloudWatch App Signals MCP Server

MCP server wrapper for [CloudWatch Application Signals](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-appsignals-mcp-server) — monitor application health, service-level objectives (SLOs), and dependency topology through CloudWatch Application Signals.

## What is CloudWatch Application Signals?

AWS CloudWatch Application Signals is an application performance monitoring (APM) feature that automatically discovers your services, tracks SLO compliance, and surfaces latency, error rate, and dependency health data from instrumented workloads on EKS, ECS, EC2, and Lambda. This MCP server lets AI assistants query service maps, check SLO status, and retrieve performance metrics to diagnose application degradations and dependency failures. See [awslabs/mcp](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-appsignals-mcp-server) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

**Summary.** MCP server wrapper for [CloudWatch Application Signals](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-appsignals-mcp-server) — query application performance, SLO compliance, and service dependency health from CloudWatch Application Signals.

## Tools Reference

| Tool | Description |
|------|-------------|
| `audit_services` | Audit Services |
| `audit_slos` | Audit Slos |
| `audit_service_operations` | Audit Service Operations |
| `analyze_canary_failures` | Analyze Canary Failures |
| `list_monitored_services` | List Monitored Services |
| `get_service_detail` | Get Service Detail |
| `query_service_metrics` | Query Service Metrics |
| `list_service_operations` | List Service Operations |
| `get_slo` | Get Slo |
| `list_slos` | List Slos |
| `search_transaction_spans` | Search Transaction Spans |
| `query_sampled_traces` | Query Sampled Traces |
| `list_slis` | List Slis |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all services discovered by CloudWatch Application Signals and their current health status."
- "Show me the SLO compliance status for all my services over the past 7 days."
- "Which SLOs are currently breached or at risk of breaching?"
- "Show me the latency and error rate metrics for the checkout service in the last hour."
- "Display the service dependency map for my e-commerce application."
- "List all Application Signals SLOs defined in my account and their target error budgets."

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
  hackerdogs/aws-cloudwatch-appsignals-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8607:8607 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8607 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-cloudwatch-appsignals-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-cloudwatch-appsignals-mcp": {
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
        "hackerdogs/aws-cloudwatch-appsignals-mcp:latest"
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
    "aws-cloudwatch-appsignals-mcp": {
      "url": "http://localhost:8607/mcp"
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
    "aws-cloudwatch-appsignals-mcp": {
      "url": "http://localhost:8485/aws-cloudwatch-appsignals-mcp/mcp",
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
| `MCP_PORT` | `8607` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-cloudwatch-appsignals-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-cloudwatch-appsignals-mcp-test -p 8607:8607 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-cloudwatch-appsignals-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8607/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8607/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8607/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-cloudwatch-appsignals-mcp-test
```
