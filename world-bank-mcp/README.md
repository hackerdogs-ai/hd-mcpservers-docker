<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# World Bank MCP Server

MCP server wrapper for [World Bank MCP](https://github.com/anshumax/world-bank-mcp) — access to the open World Bank data API for global economic and development indicators.

## What is World Bank MCP?

The World Bank MCP server enables AI assistants to query the World Bank's open data API, which covers thousands of development indicators across 200+ countries — including GDP, poverty rates, population, education, health, energy, and climate data. It allows natural-language retrieval of economic statistics, country comparisons, and time-series data from the World Bank catalog. See [github.com/anshumax/world-bank-mcp](https://github.com/anshumax/world-bank-mcp) for full documentation. No API keys are required — the World Bank data API is publicly accessible.

## Tools Reference

| Tool | Description |
|------|-------------|
| `world_bank_info` | Return status information for the World Bank MCP server |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use the World Bank MCP to fetch the GDP per capita for Nigeria from 2010 to 2023."
- "Compare the poverty headcount ratio for India and Bangladesh over the last 10 years using World Bank data."
- "Get the World Bank indicator for CO2 emissions (metric tons per capita) for the top 10 emitting countries."
- "What is the current life expectancy at birth for all countries in Sub-Saharan Africa according to World Bank data?"
- "Use the World Bank API to find the literacy rate for women in South Asia from 2000 to 2020."
- "Retrieve World Bank data on internet usage rates for Latin American countries and rank them by 2022 values."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/world-bank-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8459:8459 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8459 \
  hackerdogs/world-bank-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "world-bank-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/world-bank-mcp:latest"],
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
    "world-bank-mcp": {
      "url": "http://localhost:8459/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8459` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/world-bank-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name world-bank-mcp-test -p 8459:8459 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/world-bank-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8459/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8459/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8459/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_world_bank","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop world-bank-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the World Bank CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint world-bank hackerdogs/world-bank-mcp:latest --help
```
