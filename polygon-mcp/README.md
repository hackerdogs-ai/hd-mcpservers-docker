<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Polygon MCP Server

MCP server wrapper for [Polygon.io](https://polygon.io/) — real-time and historical stock, options, forex, and crypto market data via the Polygon.io API.

## What is Polygon?

Polygon.io is a financial market data platform providing real-time and historical data for US stocks, options, foreign exchange, and cryptocurrencies. This MCP server wraps the Polygon.io API so AI assistants can fetch ticker quotes, OHLCV bars, trade ticks, options chains, news, and aggregated market snapshots in a single conversation. An API key is required for all data access.

**API key required** — sign up and get your key at [polygon.io](https://polygon.io/).

**Tools:**
- `polygon_info` — Return basic info / status for Polygon MCP server.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Get the current stock price and daily change for AAPL using the Polygon API."
- "Fetch the last 30 days of daily OHLCV bars for TSLA and calculate its average volume."
- "Look up the options chain for NVDA expiring next month and show strikes near the money."
- "What were the top 10 most active stocks by volume on the NYSE yesterday?"
- "Get the current EUR/USD forex rate and the 1-hour bars for the past 24 hours."
- "Fetch the latest news articles about MSFT from Polygon and summarize the sentiment."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/polygon-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8445:8445 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8445 \
  hackerdogs/polygon-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "polygon-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/polygon-mcp:latest"],
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
    "polygon-mcp": {
      "url": "http://localhost:8445/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8445` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/polygon-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name polygon-mcp-test -p 8445:8445 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/polygon-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8445/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8445/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8445/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"polygon_info","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop polygon-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Polygon MCP server in the same container by overriding the entrypoint without starting the MCP wrapper.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/polygon-mcp:latest mcp_server.py --help
```
