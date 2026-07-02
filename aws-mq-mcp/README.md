<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS MQ MCP Server

MCP server wrapper for [Amazon MQ](https://github.com/awslabs/mcp/tree/main/src/amazon-mq-mcp-server) — list, describe, and monitor Amazon MQ message brokers running ActiveMQ or RabbitMQ.

## What is Amazon MQ?

Amazon MQ is a managed message broker service that supports Apache ActiveMQ and RabbitMQ, enabling reliable asynchronous messaging for distributed applications without managing broker infrastructure. This MCP server exposes Amazon MQ broker state, configuration, and queue metrics through natural-language queries via the `awslabs.amazon-mq-mcp-server` package. See [awslabs/mcp](https://github.com/awslabs/mcp) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `delete_broker` | Delete Broker |
| `delete_configuration` | Delete Configuration |
| `describe_broker` | Describe Broker |
| `describe_broker_engine_types` | Describe Broker Engine Types |
| `describe_broker_instance_options` | Describe Broker Instance Options |
| `describe_configuration` | Describe Configuration |
| `describe_configuration_revision` | Describe Configuration Revision |
| `describe_shared_resources` | Describe Shared Resources |
| `describe_user` | Describe User |
| `list_brokers` | List Brokers |
| `list_configuration_revisions` | List Configuration Revisions |
| `list_configurations` | List Configurations |
| `list_tags` | List Tags |
| `list_users` | List Users |
| `promote` | Promote |
| `reboot_broker` | Reboot Broker |
| `update_broker` | Update Broker |
| `update_configuration` | Update Configuration |
| `rabbimq_broker_initialize_connection` | Rabbimq Broker Initialize Connection |
| `rabbimq_broker_initialize_connection_with_oauth` | Rabbimq Broker Initialize Connection With Oauth |
| `rabbitmq_broker_get_guideline` | Rabbitmq Broker Get Guideline |
| `rabbitmq_broker_list_queues` | Rabbitmq Broker List Queues |
| `rabbitmq_broker_list_exchanges` | Rabbitmq Broker List Exchanges |
| `rabbitmq_broker_list_vhosts` | Rabbitmq Broker List Vhosts |
| `rabbitmq_broker_get_queue_info` | Rabbitmq Broker Get Queue Info |
| `rabbitmq_broker_get_exchange_info` | Rabbitmq Broker Get Exchange Info |
| `rabbitmq_broker_list_shovels` | Rabbitmq Broker List Shovels |
| `rabbitmq_broker_get_shovel_info` | Rabbitmq Broker Get Shovel Info |
| `rabbitmq_broker_get_cluster_nodes_info` | Rabbitmq Broker Get Cluster Nodes Info |
| `rabbitmq_broker_list_connections` | Rabbitmq Broker List Connections |
| `rabbitmq_broker_list_consumers` | Rabbitmq Broker List Consumers |
| `rabbitmq_broker_list_users` | Rabbitmq Broker List Users |
| `rabbitmq_broker_is_in_alarm` | Rabbitmq Broker Is In Alarm |
| `rabbitmq_broker_is_quorum_critical` | Rabbitmq Broker Is Quorum Critical |
| `rabbitmq_broker_get_broker_definition` | Rabbitmq Broker Get Broker Definition |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all Amazon MQ brokers in my account and their current status."
- "Show me the configuration details for the ActiveMQ broker named 'orders-prod'."
- "Which of my RabbitMQ brokers are in a degraded or maintenance state?"
- "Describe the storage and instance type for each of my MQ brokers."
- "Find all MQ brokers that don't have automatic minor version upgrades enabled."
- "What are the endpoints for the 'payments-broker' RabbitMQ instance?"

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
  hackerdogs/aws-mq-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8616:8616 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8616 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-mq-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-mq-mcp": {
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
        "hackerdogs/aws-mq-mcp:latest"
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
    "aws-mq-mcp": {
      "url": "http://localhost:8616/mcp"
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
    "aws-mq-mcp": {
      "url": "http://localhost:8485/aws-mq-mcp/mcp",
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
| `MCP_PORT` | `8616` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/aws-mq-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-mq-mcp-test -p 8616:8616 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-mq-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8616/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8616/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8616/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-mq-mcp-test
```
