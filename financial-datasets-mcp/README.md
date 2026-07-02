<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Financial Datasets MCP Server

MCP server wrapper for [Financial Datasets](https://github.com/virattt/financial-datasets-mcp) — access real-time and historical stock market data including income statements, balance sheets, and price history.

## What is Financial Datasets?

Financial Datasets MCP connects AI assistants to structured financial data covering public companies. It provides access to income statements, balance sheets, cash flow statements, stock price history, and company facts — allowing AI clients to perform fundamental analysis, compare companies, and answer quantitative financial questions. See [virattt/financial-datasets-mcp](https://github.com/virattt/financial-datasets-mcp) for full documentation.

**API key required** — a Financial Datasets API key is needed to access real market data.

## Tools Reference


## Tools Reference

| Tool | Description |
|------|-------------|
| `financial_datasets_info` | Return basic info / status for Financial Datasets MCP. |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Get the last 4 quarterly income statements for Apple (AAPL) and summarize revenue trends."
- "Fetch the balance sheet for Tesla (TSLA) for fiscal year 2023."
- "What is the current price and 52-week range for NVIDIA (NVDA)?"
- "Pull the cash flow statements for Microsoft and calculate free cash flow for each of the last 3 years."
- "Compare the gross margin of Amazon vs. Google over the last 5 annual periods."
- "Get company facts for Meta (META) — sector, employee count, and description."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/financial-datasets-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8420:8420 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8420 \
  hackerdogs/financial-datasets-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "financial-datasets-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/financial-datasets-mcp:latest"],
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
    "financial-datasets-mcp": {
      "url": "http://localhost:8420/mcp"
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
    "financial-datasets-mcp": {
      "url": "http://localhost:8485/financial-datasets-mcp/mcp",
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
| `MCP_PORT` | `8420` | HTTP port (only used with `streamable-http`) |
| `FINANCIAL_DATASETS_API_KEY` | — | API key for the Financial Datasets service |

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
docker build -t hackerdogs/financial-datasets-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name financial-datasets-mcp-test -p 8420:8420 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/financial-datasets-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8420/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8420/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8420/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_financial_datasets","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop financial-datasets-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Financial Datasets CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint financial-datasets hackerdogs/financial-datasets-mcp:latest --help
```
