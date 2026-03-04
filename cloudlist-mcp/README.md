<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Cloudlist MCP Server

MCP server wrapper for [Cloudlist](https://github.com/projectdiscovery/cloudlist) — lists assets from multiple cloud providers (AWS, GCP, Azure, DigitalOcean, Fastly, etc.) for attack surface management and cloud asset discovery.

## What is Cloudlist?

Cloudlist is a cloud asset discovery tool by ProjectDiscovery that lists assets across multiple cloud providers. It supports AWS, GCP, Azure, DigitalOcean, Scaleway, Fastly, Heroku, Linode, Namecheap, Cloudflare, Hetzner, and more, providing a unified view for attack surface management.

## Prerequisites

Cloudlist requires cloud provider credentials via a YAML configuration file. You'll need API keys or credentials for the cloud providers you want to query.

Where to get credentials:
- **AWS** — [AWS Console (IAM)](https://console.aws.amazon.com/iam/)
- **GCP** — [GCP Console (Service Accounts)](https://console.cloud.google.com/iam-admin/serviceaccounts)
- **Azure** — [Azure Portal](https://portal.azure.com)
- **DigitalOcean** — [DigitalOcean API](https://cloud.digitalocean.com/account/api/tokens)
- **Cloudflare** — [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)

Mount your config file to `/app/config/provider-config.yaml` or pass the config content directly via the `config_content` parameter.

Example provider config:

```yaml
- provider: aws
  id: main-aws
  aws_access_key: AKIAXXXXXX
  aws_secret_key: xxxxx
  aws_session_token: ""
- provider: gcp
  id: main-gcp
  gcp_service_account_key: '{...}'
```

## Tools Reference

### `list_cloud_assets`

List assets (hosts, IPs) from cloud providers (AWS, GCP, Azure, DigitalOcean, etc.).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `providers` | string | No | — | Comma-separated providers (e.g. `"aws,gcp,azure"`). Omit for all configured |
| `hosts_only` | boolean | No | `false` | Return only hostnames |
| `ips_only` | boolean | No | `false` | Return only IP addresses |
| `exclude_private` | boolean | No | `false` | Exclude private/internal IPs |
| `service` | string | No | — | Filter by service type (e.g. `"ec2"`, `"s3"`, `"route53"`) |
| `config_content` | string | No | — | YAML config with cloud provider credentials |

<details>
<summary>Example response</summary>

```json
{
  "success": true,
  "output": [{"host": "ec2-1-2-3-4.compute-1.amazonaws.com", "ip": "1.2.3.4", "provider": "aws", "service": "ec2"}]
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all cloud assets from my AWS account."
- "Show me only the public IP addresses across all my configured cloud providers."
- "List all EC2 instances from my AWS configuration."
- "Get all assets from my GCP and Azure accounts, excluding private IPs."
- "Show only hostnames from my DigitalOcean and Cloudflare providers."
- "List all Route53 DNS records from my AWS configuration."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -v $(pwd)/config:/app/config:ro \
  hackerdogs/cloudlist-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8111:8111 \
  -v $(pwd)/config:/app/config:ro \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8111 \
  hackerdogs/cloudlist-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "cloudlist-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/config:/app/config:ro",
        "hackerdogs/cloudlist-mcp:latest"
      ]
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "cloudlist-mcp": {
      "url": "http://localhost:8111/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8111` | Port for streamable-http transport |

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
docker build -t hackerdogs/cloudlist-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name cloudlist-test -p 8111:8111 \
  -e MCP_TRANSPORT=streamable-http \
  -v $(pwd)/config:/app/config:ro \
  hackerdogs/cloudlist-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8111/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8111/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8111/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_cloud_assets","arguments":{"providers":"aws","ips_only":true}}}'
```

**4. Clean up:**

```bash
docker stop cloudlist-test
```
