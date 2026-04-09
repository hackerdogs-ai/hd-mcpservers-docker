<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Microsoft Fabric RTI MCP Server

MCP server wrapper for [Microsoft Fabric RTI](https://github.com/microsoft/fabric-rti-mcp) — upstream package `microsoft-fabric-rti-mcp`.

## What is Microsoft Fabric RTI?

MCP server for [Microsoft Fabric](https://www.microsoft.com/en-us/microsoft-fabric) Real-Time Intelligence. Query and analyze real-time data streams, KQL databases, and eventhouses.

**API key required** — configure in your Microsoft Fabric workspace.

**Summary.** Microsoft Fabric RTI MCP Server — Dockerized from upstream `microsoft-fabric-rti-mcp` package.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Query real-time data from my Fabric eventhouse."
- "Show recent events in my KQL database."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e FABRIC_API_KEY \
  hackerdogs/ms-fabric-rti-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8650:8650 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8650 \
  -e FABRIC_API_KEY \
  hackerdogs/ms-fabric-rti-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "ms-fabric-rti-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "FABRIC_API_KEY",
        "hackerdogs/ms-fabric-rti-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "FABRIC_API_KEY": ""
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
    "ms-fabric-rti-mcp": {
      "url": "http://localhost:8650/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8650` | HTTP port (only used with `streamable-http`) |
| `FABRIC_API_KEY` | — | Microsoft Fabric API key |

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
docker build -t hackerdogs/ms-fabric-rti-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name ms-fabric-rti-mcp-test -p 8650:8650 \
  -e MCP_TRANSPORT=streamable-http \
  -e FABRIC_API_KEY \
  hackerdogs/ms-fabric-rti-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8650/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8650/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8650/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop ms-fabric-rti-mcp-test
```
