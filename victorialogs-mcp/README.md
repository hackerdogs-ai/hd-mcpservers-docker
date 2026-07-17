<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Victorialogs MCP Server

MCP server wrapper for [VictoriaLogs](https://docs.victoriametrics.com/victorialogs/) — query and analyze logs stored in VictoriaLogs using LogsQL.

## What is Victorialogs?

VictoriaLogs is a high-performance, cost-efficient log management system by VictoriaMetrics, designed as a drop-in replacement for Elasticsearch/Grafana Loki at a fraction of the resource cost. This MCP server lets AI assistants query logs using LogsQL — VictoriaLogs' query language — including full-text search, structured field filtering, aggregations, and time-series hit counts. See [VictoriaLogs documentation](https://docs.victoriametrics.com/victorialogs/) for full documentation.

**No API keys required** — connect to your VictoriaLogs instance by setting `VICTORIALOGS_URL` (defaults to `http://localhost:9428`).

**Summary.** MCP server wrapper for [VictoriaLogs](https://docs.victoriametrics.com/victorialogs/) — query and analyze logs using LogsQL against a VictoriaLogs instance.

**Tools:**
- `victorialogs_query` — Run a LogsQL query and return matching log lines.
- `victorialogs_hits` — Get log hit counts over time bucketed by a time step.
- `victorialogs_stats` — Retrieve aggregated statistics for a LogsQL query.
- `victorialogs_field_names` — List all field names present in logs matching a query.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Query VictoriaLogs for all error-level log lines from the last hour."
- "Search my logs for entries containing 'connection refused' and show the 50 most recent."
- "Get hit counts for the query '_msg:\"timeout\"' bucketed by 15-minute intervals over the past day."
- "What are all the field names present in logs from the nginx service?"
- "Show aggregated statistics for HTTP 5xx errors from the last 6 hours."
- "Query VictoriaLogs for all logs from the 'auth' service where level is 'warn' or 'error'."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/victorialogs-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8527:8527 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8527 \
  hackerdogs/victorialogs-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "victorialogs-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/victorialogs-mcp:latest"],
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
    "victorialogs-mcp": {
      "url": "http://localhost:8527/mcp"
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
    "victorialogs-mcp": {
      "url": "http://localhost:8485/victorialogs-mcp/mcp",
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
| `MCP_PORT` | `8527` | HTTP port (only used with `streamable-http`) |
| `VICTORIALOGS_URL` | `http://localhost:9428` | URL of your VictoriaLogs instance |

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
docker build -t hackerdogs/victorialogs-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name victorialogs-mcp-test -p 8527:8527 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/victorialogs-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8527/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8527/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8527/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_victorialogs","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop victorialogs-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Victorialogs CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint victorialogs hackerdogs/victorialogs-mcp:latest --help
```
