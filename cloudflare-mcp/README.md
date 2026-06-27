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

## Tools Reference

| Tool | Description |
|------|-------------|
| `get_kvs` | Get Kvs |
| `kv_get` | Kv Get |
| `kv_put` | Kv Put |
| `kv_delete` | Kv Delete |
| `kv_list` | Kv List |
| `worker_list` | Worker List |
| `worker_get` | Worker Get |
| `worker_put` | Worker Put |
| `worker_delete` | Worker Delete |
| `worker_deploy` | Worker Deploy |
| `analytics_get` | Analytics Get |
| `workers_analytics_search` | Workers Analytics Search |
| `r2_list_buckets` | R2 List Buckets |
| `r2_create_bucket` | R2 Create Bucket |
| `r2_delete_bucket` | R2 Delete Bucket |
| `r2_list_objects` | R2 List Objects |
| `r2_get_object` | R2 Get Object |
| `r2_put_object` | R2 Put Object |
| `r2_delete_object` | R2 Delete Object |
| `d1_list_databases` | D1 List Databases |
| `d1_create_database` | D1 Create Database |
| `d1_delete_database` | D1 Delete Database |
| `d1_query` | D1 Query |
| `do_create_namespace` | Do Create Namespace |
| `do_delete_namespace` | Do Delete Namespace |
| `do_list_namespaces` | Do List Namespaces |
| `do_get_object` | Do Get Object |
| `do_list_objects` | Do List Objects |
| `do_delete_object` | Do Delete Object |
| `do_alarm_list` | Do Alarm List |
| `do_alarm_set` | Do Alarm Set |
| `do_alarm_delete` | Do Alarm Delete |
| `queue_create` | Queue Create |
| `queue_delete` | Queue Delete |
| `queue_list` | Queue List |
| `queue_get` | Queue Get |
| `queue_send_message` | Queue Send Message |
| `queue_send_batch` | Queue Send Batch |
| `queue_get_message` | Queue Get Message |
| `queue_delete_message` | Queue Delete Message |
| `queue_update_visibility` | Queue Update Visibility |
| `ai_inference` | Ai Inference |
| `ai_list_models` | Ai List Models |
| `ai_get_model` | Ai Get Model |
| `ai_embeddings` | Ai Embeddings |
| `ai_text_generation` | Ai Text Generation |
| `ai_image_generation` | Ai Image Generation |
| `workflow_get` | Workflow Get |
| `workflow_create` | Workflow Create |
| `workflow_delete` | Workflow Delete |
| `workflow_list` | Workflow List |
| `workflow_update` | Workflow Update |
| `workflow_execute` | Workflow Execute |
| `template_list` | Template List |
| `template_get` | Template Get |
| `template_create_worker` | Template Create Worker |
| `wfp_create_dispatch_namespace` | Wfp Create Dispatch Namespace |
| `wfp_delete_dispatch_namespace` | Wfp Delete Dispatch Namespace |
| `wfp_list_dispatch_namespaces` | Wfp List Dispatch Namespaces |
| `wfp_add_custom_domain` | Wfp Add Custom Domain |
| `wfp_remove_custom_domain` | Wfp Remove Custom Domain |
| `wfp_list_custom_domains` | Wfp List Custom Domains |
| `service_binding_create` | Service Binding Create |
| `service_binding_delete` | Service Binding Delete |
| `service_binding_list` | Service Binding List |
| `service_binding_update` | Service Binding Update |
| `env_var_set` | Env Var Set |
| `env_var_delete` | Env Var Delete |
| `env_var_list` | Env Var List |
| `env_var_bulk_set` | Env Var Bulk Set |
| `route_create` | Route Create |
| `route_delete` | Route Delete |
| `route_list` | Route List |
| `route_update` | Route Update |
| `cron_create` | Cron Create |
| `cron_delete` | Cron Delete |
| `cron_list` | Cron List |
| `cron_update` | Cron Update |
| `zones_list` | Zones List |
| `zones_get` | Zones Get |
| `domain_list` | Domain List |
| `secret_put` | Secret Put |
| `secret_delete` | Secret Delete |
| `secret_list` | Secret List |
| `version_list` | Version List |
| `version_get` | Version Get |
| `version_rollback` | Version Rollback |
| `wrangler_config_get` | Wrangler Config Get |
| `wrangler_config_update` | Wrangler Config Update |

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
