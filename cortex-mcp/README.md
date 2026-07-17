<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Cortex MCP Server

MCP server wrapper for [Cortex](https://github.com/TheHive-Project/Cortex) — security orchestration platform for running threat intelligence analyzers and active response actions.

## What is Cortex?

Cortex is an open-source security orchestration engine by TheHive Project that lets analysts submit observables (IPs, domains, file hashes, URLs) to a library of analyzers and responders, then collect structured reports. It acts as a unified backend for threat intelligence workflows, integrating with TheHive SIRP and dozens of third-party feeds. See [TheHive-Project/Cortex](https://github.com/TheHive-Project/Cortex) for full documentation.

**No API keys required** for the MCP wrapper itself; individual Cortex analyzers may require their own credentials configured in the Cortex instance.

**Tools:**
- `cortex_info` — Return status information for the connected Cortex MCP server.

## Tools Reference

### `cortex_info`

Return basic status for the Cortex MCP server.

_No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Check whether the Cortex MCP server is up and responding."
- "Use Cortex to analyze the observable 8.8.8.8 and return threat intelligence."
- "Submit the file hash `d41d8cd98f00b204e9800998ecf8427e` to Cortex analyzers."
- "Run a VirusTotal analyzer via Cortex for the domain `malicious-example.com`."
- "List the available Cortex analyzers for URL reputation checking."
- "Use Cortex to trigger an active response action on a suspicious IP address."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/cortex-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8410:8410 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8410 \
  hackerdogs/cortex-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "cortex-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/cortex-mcp:latest"],
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
    "cortex-mcp": {
      "url": "http://localhost:8410/mcp"
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
    "cortex-mcp": {
      "url": "http://localhost:8485/cortex-mcp/mcp",
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
| `MCP_PORT` | `8410` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/cortex-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name cortex-mcp-test -p 8410:8410 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/cortex-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8410/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8410/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8410/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_cortex","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop cortex-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Cortex CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint cortex hackerdogs/cortex-mcp:latest --help
```
