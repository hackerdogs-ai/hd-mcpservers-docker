<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Acuvity Server Azure MCP Server

MCP server wrapper for [Microsoft Azure MCP Server](https://github.com/acuvity/mcp-servers-registry) — AI agent integration with Microsoft Azure cloud services.

## What is Azure MCP?

The Microsoft Azure MCP server gives AI agents natural-language access to Azure cloud services, enabling operations such as listing and managing resource groups, querying Azure Monitor logs, interacting with Azure Storage, and working with other Azure APIs. It uses Azure SDK authentication (service principal, managed identity, or CLI credentials) to connect to your Azure subscription. Azure credentials are required — configure authentication via environment variables or Azure CLI before running the container.

**Tools:**
- `acuvity_mcp_server_azure_info` — Confirm that the Azure MCP server is running and ready to accept requests.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all resource groups in my Azure subscription and their locations."
- "Use the Azure MCP server to show all virtual machines in the 'production' resource group and their power state."
- "Query Azure Monitor logs for failed login attempts on my App Service in the last 24 hours."
- "List all storage accounts in my subscription and identify any that have public blob access enabled."
- "Show me all Azure resources with the tag 'environment=prod' across all resource groups."
- "Check that the Azure MCP server is running and that my Azure credentials are configured."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-azure-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8432:8432 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8432 \
  hackerdogs/acuvity-mcp-server-azure-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "acuvity-mcp-server-azure-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/acuvity-mcp-server-azure-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
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
    "acuvity-mcp-server-azure-mcp": {
      "url": "http://localhost:8432/mcp"
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
    "acuvity-mcp-server-azure-mcp": {
      "url": "http://localhost:8485/acuvity-mcp-server-azure-mcp/mcp",
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
| `MCP_PORT` | `8432` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/acuvity-mcp-server-azure-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name acuvity-mcp-server-azure-mcp-test -p 8432:8432 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/acuvity-mcp-server-azure-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8432/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8432/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8432/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_acuvity_server_azure","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop acuvity-mcp-server-azure-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Acuvity Server Azure CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint acuvity-server-azure hackerdogs/acuvity-mcp-server-azure-mcp:latest --help
```
