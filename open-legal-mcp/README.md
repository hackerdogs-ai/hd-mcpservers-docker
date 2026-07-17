<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Open Legal MCP Server

MCP server wrapper for [Open Legal Compliance MCP](https://github.com/TCoder920x/open-legal-compliance-mcp) — legal compliance checking and regulatory analysis assistant.

## What is Open Legal?

Open Legal Compliance MCP is an AI-driven legal compliance assistant that helps developers, product teams, and legal professionals check software and business practices against regulatory frameworks. It surfaces potential compliance issues across jurisdictions and regulations such as GDPR, CCPA, and HIPAA. See [TCoder920x/open-legal-compliance-mcp](https://github.com/TCoder920x/open-legal-compliance-mcp) for full documentation.

**No API keys required** — Open Legal runs locally inside the Docker container.

**Tools:**
- `open_legal_info` — Return basic info / status for Open Legal Compliance MCP.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Check whether our data retention policy complies with GDPR Article 5."
- "Analyze this privacy policy for CCPA compliance gaps."
- "What regulatory requirements apply to a SaaS app that processes health data in the EU?"
- "Review our cookie consent flow for compliance with ePrivacy Directive requirements."
- "Identify potential HIPAA violations in this patient data handling workflow."
- "Does our terms of service meet the disclosure requirements for a US-based fintech app?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/open-legal-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8439:8439 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8439 \
  hackerdogs/open-legal-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "open-legal-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/open-legal-mcp:latest"],
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
    "open-legal-mcp": {
      "url": "http://localhost:8439/mcp"
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
    "open-legal-mcp": {
      "url": "http://localhost:8485/open-legal-mcp/mcp",
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
| `MCP_PORT` | `8439` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/open-legal-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name open-legal-mcp-test -p 8439:8439 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/open-legal-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8439/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8439/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8439/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"open_legal_info","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop open-legal-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Open Legal Compliance MCP server in the same container by overriding the entrypoint without starting the MCP wrapper.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/open-legal-mcp:latest mcp_server.py --help
```
