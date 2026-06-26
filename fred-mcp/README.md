<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Fred MCP Server

MCP server wrapper for [FRED](https://fred.stlouisfed.org/) — access over 800,000 economic time series from the Federal Reserve Bank of St. Louis via the FRED API.

## What is FRED?

FRED (Federal Reserve Economic Data) is the St. Louis Fed's database of economic indicators covering GDP, inflation (CPI, PCE), unemployment, interest rates, money supply, housing starts, and hundreds of other macroeconomic series updated in near real time. This MCP server provides structured access to FRED data so AI assistants can retrieve series values, search for indicators by keyword, and perform economic analysis. See [federal-reserve-mcp](https://github.com/david-reti/fred-mcp-server) for full documentation.

**API key required** — register for a free FRED API key at [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html).

## Tools Reference


## Tools Reference

| Tool | Description |
|------|-------------|
| `fred_info` | Return basic info / status for FRED MCP SERVER. |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Fetch the last 12 months of US CPI data (series CPIAUCSL) and calculate year-over-year inflation."
- "Get the current Federal Funds Rate from FRED and compare it to its value one year ago."
- "Search FRED for series related to 'unemployment rate' and list the top results."
- "Retrieve quarterly US GDP (series GDP) from 2020 to 2024 and show the growth rate each quarter."
- "Pull the 10-year Treasury yield (series GS10) for the past 5 years and identify the peak."
- "Get monthly housing starts data (series HOUST) for 2023 and summarize the trend."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/fred-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8423:8423 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8423 \
  hackerdogs/fred-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "fred-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/fred-mcp:latest"],
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
    "fred-mcp": {
      "url": "http://localhost:8423/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8423` | HTTP port (only used with `streamable-http`) |
| `FRED_API_KEY` | — | FRED API key — get one at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) |

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
docker build -t hackerdogs/fred-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name fred-mcp-test -p 8423:8423 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/fred-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8423/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8423/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8423/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_fred","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop fred-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Fred CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint fred hackerdogs/fred-mcp:latest --help
```
