<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS Serverless MCP Server

MCP server wrapper for [AWS Serverless](https://github.com/awslabs/mcp/tree/main/src/aws-serverless-mcp-server) — build, deploy, and monitor serverless applications using AWS SAM (Serverless Application Model) and Lambda through natural language.

## What is AWS Serverless MCP?

The AWS Serverless MCP server (`awslabs.aws-serverless-mcp-server`) provides AI-assisted tooling for the full AWS serverless application lifecycle: scaffolding SAM templates, deploying stacks via `sam deploy`, invoking Lambda functions, tailing CloudWatch Logs, and inspecting deployed serverless resources. It is designed to accelerate serverless development workflows by making SAM commands and Lambda management accessible through conversational prompts. See [awslabs/mcp](https://github.com/awslabs/mcp) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `webapp_deployment_help` | Webapp Deployment Help |
| `deploy_serverless_app_help` | Deploy Serverless App Help |
| `get_iac_guidance` | Get Iac Guidance |
| `get_lambda_event_schemas` | Get Lambda Event Schemas |
| `get_lambda_guidance` | Get Lambda Guidance |
| `get_serverless_templates` | Get Serverless Templates |
| `sam_build` | Sam Build |
| `sam_deploy` | Sam Deploy |
| `sam_init` | Sam Init |
| `sam_local_invoke` | Sam Local Invoke |
| `sam_logs` | Sam Logs |
| `list_registries` | List Registries |
| `search_schema` | Search Schema |
| `describe_schema` | Describe Schema |
| `get_metrics` | Get Metrics |
| `configure_domain` | Configure Domain |
| `deploy_webapp` | Deploy Webapp |
| `update_webapp_frontend` | Update Webapp Frontend |
| `esm_guidance` | Esm Guidance |
| `esm_kafka_troubleshoot` | Esm Kafka Troubleshoot |
| `esm_optimize` | Esm Optimize |
| `secure_esm_msk_policy` | Secure Esm Msk Policy |
| `secure_esm_sqs_policy` | Secure Esm Sqs Policy |
| `secure_esm_kinesis_policy` | Secure Esm Kinesis Policy |
| `secure_esm_dynamodb_policy` | Secure Esm Dynamodb Policy |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all Lambda functions in my account and their runtimes and memory settings."
- "Show me the recent CloudWatch Logs for the 'order-processor' Lambda function."
- "Deploy my SAM application from the current template.yaml to the 'staging' stack."
- "Invoke the 'send-notification' Lambda function with a test payload and show the response."
- "Which Lambda functions have not been invoked in the last 30 days?"
- "Show me all SAM-deployed CloudFormation stacks and their deployment status."

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
  hackerdogs/aws-serverless-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8623:8623 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8623 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-serverless-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-serverless-mcp": {
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
        "hackerdogs/aws-serverless-mcp:latest"
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
    "aws-serverless-mcp": {
      "url": "http://localhost:8623/mcp"
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
| `MCP_PORT` | `8623` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-serverless-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-serverless-mcp-test -p 8623:8623 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-serverless-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8623/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8623/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8623/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-serverless-mcp-test
```
