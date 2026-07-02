<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# AWS Bedrock AgentCore MCP Server

MCP server wrapper for [Bedrock AgentCore](https://github.com/awslabs/mcp/tree/main/src/amazon-bedrock-agentcore-mcp-server) — build, configure, and operate Amazon Bedrock AgentCore resources including Runtime, Memory, Gateway, Code Interpreter, Browser, Observability, and Identity services.

## What is Bedrock AgentCore?

Amazon Bedrock AgentCore is AWS's managed platform for deploying production AI agents, providing built-in capabilities for memory management, code execution, browser automation, observability, and secure identity. This MCP server exposes the full AgentCore control plane to AI assistants, enabling them to search AgentCore documentation, configure runtime environments, set up memory stores, and manage gateways and identity resources. See [awslabs/mcp](https://github.com/awslabs/mcp/tree/main/src/amazon-bedrock-agentcore-mcp-server) for full documentation.

**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.

**Summary.** MCP server wrapper for [Bedrock AgentCore](https://github.com/awslabs/mcp/tree/main/src/amazon-bedrock-agentcore-mcp-server) — configure and manage Amazon Bedrock AgentCore agent infrastructure including Runtime, Memory, and Gateway services.

## Tools Reference

| Tool | Description |
|------|-------------|
| `search_agentcore_docs` | Search Agentcore Docs |
| `fetch_agentcore_doc` | Fetch Agentcore Doc |
| `create_agent_runtime` | Create Agent Runtime |
| `get_agent_runtime` | Get Agent Runtime |
| `update_agent_runtime` | Update Agent Runtime |
| `delete_agent_runtime` | Delete Agent Runtime |
| `list_agent_runtimes` | List Agent Runtimes |
| `list_agent_runtime_versions` | List Agent Runtime Versions |
| `create_agent_runtime_endpoint` | Create Agent Runtime Endpoint |
| `get_agent_runtime_endpoint` | Get Agent Runtime Endpoint |
| `update_agent_runtime_endpoint` | Update Agent Runtime Endpoint |
| `delete_agent_runtime_endpoint` | Delete Agent Runtime Endpoint |
| `list_agent_runtime_endpoints` | List Agent Runtime Endpoints |
| `invoke_agent_runtime` | Invoke Agent Runtime |
| `stop_runtime_session` | Stop Runtime Session |
| `get_runtime_guide` | Get Runtime Guide |
| `memory_create` | Memory Create |
| `memory_get` | Memory Get |
| `memory_update` | Memory Update |
| `memory_delete` | Memory Delete |
| `memory_list` | Memory List |
| `memory_create_event` | Memory Create Event |
| `memory_get_event` | Memory Get Event |
| `memory_delete_event` | Memory Delete Event |
| `memory_list_events` | Memory List Events |
| `memory_list_actors` | Memory List Actors |
| `memory_list_sessions` | Memory List Sessions |
| `memory_get_record` | Memory Get Record |
| `memory_delete_record` | Memory Delete Record |
| `memory_list_records` | Memory List Records |
| `memory_retrieve_records` | Memory Retrieve Records |
| `memory_batch_create_records` | Memory Batch Create Records |
| `memory_batch_update_records` | Memory Batch Update Records |
| `memory_batch_delete_records` | Memory Batch Delete Records |
| `memory_list_extraction_jobs` | Memory List Extraction Jobs |
| `memory_start_extraction_job` | Memory Start Extraction Job |
| `get_memory_guide` | Get Memory Guide |
| `identity_create_workload_identity` | Identity Create Workload Identity |
| `identity_get_workload_identity` | Identity Get Workload Identity |
| `identity_update_workload_identity` | Identity Update Workload Identity |
| `identity_delete_workload_identity` | Identity Delete Workload Identity |
| `identity_list_workload_identities` | Identity List Workload Identities |
| `identity_create_api_key_provider` | Identity Create Api Key Provider |
| `identity_get_api_key_provider` | Identity Get Api Key Provider |
| `identity_update_api_key_provider` | Identity Update Api Key Provider |
| `identity_delete_api_key_provider` | Identity Delete Api Key Provider |
| `identity_list_api_key_providers` | Identity List Api Key Providers |
| `identity_create_oauth2_provider` | Identity Create Oauth2 Provider |
| `identity_get_oauth2_provider` | Identity Get Oauth2 Provider |
| `identity_update_oauth2_provider` | Identity Update Oauth2 Provider |
| `identity_delete_oauth2_provider` | Identity Delete Oauth2 Provider |
| `identity_list_oauth2_providers` | Identity List Oauth2 Providers |
| `identity_get_token_vault` | Identity Get Token Vault |
| `identity_set_token_vault_cmk` | Identity Set Token Vault Cmk |
| `identity_put_resource_policy` | Identity Put Resource Policy |
| `identity_get_resource_policy` | Identity Get Resource Policy |
| `identity_delete_resource_policy` | Identity Delete Resource Policy |
| `get_identity_guide` | Get Identity Guide |
| `gateway_create` | Gateway Create |
| `gateway_get` | Gateway Get |
| `gateway_update` | Gateway Update |
| `gateway_delete` | Gateway Delete |
| `gateway_list` | Gateway List |
| `gateway_target_create` | Gateway Target Create |
| `gateway_target_get` | Gateway Target Get |
| `gateway_target_update` | Gateway Target Update |
| `gateway_target_delete` | Gateway Target Delete |
| `gateway_target_list` | Gateway Target List |
| `gateway_target_synchronize` | Gateway Target Synchronize |
| `gateway_resource_policy_put` | Gateway Resource Policy Put |
| `gateway_resource_policy_get` | Gateway Resource Policy Get |
| `gateway_resource_policy_delete` | Gateway Resource Policy Delete |
| `get_gateway_guide` | Get Gateway Guide |
| `policy_engine_create` | Policy Engine Create |
| `policy_engine_get` | Policy Engine Get |
| `policy_engine_update` | Policy Engine Update |
| `policy_engine_delete` | Policy Engine Delete |
| `policy_engine_list` | Policy Engine List |
| `policy_create` | Policy Create |
| `policy_get` | Policy Get |
| `policy_update` | Policy Update |
| `policy_delete` | Policy Delete |
| `policy_list` | Policy List |
| `policy_generation_start` | Policy Generation Start |
| `policy_generation_get` | Policy Generation Get |
| `policy_generation_list` | Policy Generation List |
| `policy_generation_list_assets` | Policy Generation List Assets |
| `get_policy_guide` | Get Policy Guide |
| `start_browser_session` | Start Browser Session |
| `get_browser_session` | Get Browser Session |
| `stop_browser_session` | Stop Browser Session |
| `list_browser_sessions` | List Browser Sessions |
| `browser_navigate` | Browser Navigate |
| `browser_navigate_back` | Browser Navigate Back |
| `browser_navigate_forward` | Browser Navigate Forward |
| `browser_click` | Browser Click |
| `browser_type` | Browser Type |
| `browser_fill_form` | Browser Fill Form |
| `browser_select_option` | Browser Select Option |
| `browser_hover` | Browser Hover |
| `browser_press_key` | Browser Press Key |
| `browser_upload_file` | Browser Upload File |
| `browser_handle_dialog` | Browser Handle Dialog |
| `browser_mouse_wheel` | Browser Mouse Wheel |
| `browser_snapshot` | Browser Snapshot |
| `browser_take_screenshot` | Browser Take Screenshot |
| `browser_wait_for` | Browser Wait For |
| `browser_console_messages` | Browser Console Messages |
| `browser_network_requests` | Browser Network Requests |
| `browser_evaluate` | Browser Evaluate |
| `browser_tabs` | Browser Tabs |
| `browser_close` | Browser Close |
| `browser_resize` | Browser Resize |
| `start_code_interpreter_session` | Start Code Interpreter Session |
| `stop_code_interpreter_session` | Stop Code Interpreter Session |
| `get_code_interpreter_session` | Get Code Interpreter Session |
| `list_code_interpreter_sessions` | List Code Interpreter Sessions |
| `execute_code` | Execute Code |
| `execute_command` | Execute Command |
| `install_packages` | Install Packages |
| `upload_file` | Upload File |
| `download_file` | Download File |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all AgentCore Runtime environments in my Bedrock account."
- "Show me the available AgentCore Memory stores and their configurations."
- "Search the AgentCore documentation for how to set up browser automation."
- "List all AgentCore Gateways and show me their endpoint URLs."
- "Show me the AgentCore Observability settings and current tracing configuration."
- "Help me understand how to configure AgentCore Identity for my agent deployment."

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
  hackerdogs/aws-bedrock-agentcore-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8604:8604 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8604 \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-bedrock-agentcore-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "aws-bedrock-agentcore-mcp": {
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
        "hackerdogs/aws-bedrock-agentcore-mcp:latest"
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
    "aws-bedrock-agentcore-mcp": {
      "url": "http://localhost:8604/mcp"
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
    "aws-bedrock-agentcore-mcp": {
      "url": "http://localhost:8485/aws-bedrock-agentcore-mcp/mcp",
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
| `MCP_PORT` | `8604` | HTTP port (only used with `streamable-http`) |
| `AWS_REGION` | — | AWS region (e.g. `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | — | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | — | AWS secret access key |

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
docker build -t hackerdogs/aws-bedrock-agentcore-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name aws-bedrock-agentcore-mcp-test -p 8604:8604 \
  -e MCP_TRANSPORT=streamable-http \
  -e AWS_REGION \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  hackerdogs/aws-bedrock-agentcore-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8604/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8604/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8604/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop aws-bedrock-agentcore-mcp-test
```
