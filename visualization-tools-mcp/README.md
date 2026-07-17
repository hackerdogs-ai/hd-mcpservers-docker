<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Visualization Tools MCP Server

MCP server wrapper for Visualization Tools — generate bar charts, line charts, pie charts, and scatter plots from JSON data using matplotlib.

## What is Visualization Tools?

Visualization Tools is a Hackerdogs-built MCP server that generates PNG charts and graphs from structured data using Python's matplotlib library. AI assistants can pass JSON-formatted data to create bar charts, line charts (including multi-series), pie charts, and scatter plots — receiving either a base64-encoded PNG image or a saved file path. No external APIs or internet access are required.

**No API keys required** — visualization runs locally inside the Docker container using matplotlib.

**Summary.** MCP server wrapper for Visualization Tools — generate bar charts, line charts, pie charts, and scatter plots from JSON data using matplotlib.

**Tools:**
- `create_bar_chart` — Create a bar chart from JSON data with labels and values.
- `create_line_chart` — Create a line chart from JSON data, supporting single and multi-series.
- `create_pie_chart` — Create a pie chart from JSON labels and values.
- `create_scatter_plot` — Create a scatter plot from JSON x/y coordinate data.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Create a bar chart showing monthly sales data: Jan=1200, Feb=950, Mar=1400, Apr=1100."
- "Plot a line chart of CPU usage over time from this JSON data and save it to /tmp/cpu.png."
- "Generate a pie chart showing market share: Chrome 65%, Safari 19%, Firefox 4%, Edge 4%, Other 8%."
- "Create a scatter plot from this dataset to visualize the correlation between response time and error rate."
- "Make a multi-series line chart comparing network traffic for eth0 and eth1 over 24 hours."
- "Generate a bar chart of open vulnerability counts by severity: Critical=3, High=12, Medium=27, Low=45."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/visualization-tools-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8506:8506 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8506 \
  hackerdogs/visualization-tools-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "visualization-tools-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/visualization-tools-mcp:latest"],
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
    "visualization-tools-mcp": {
      "url": "http://localhost:8506/mcp"
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
    "visualization-tools-mcp": {
      "url": "http://localhost:8485/visualization-tools-mcp/mcp",
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
| `MCP_PORT` | `8506` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/visualization-tools-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name visualization-tools-mcp-test -p 8506:8506 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/visualization-tools-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8506/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8506/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8506/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_visualization_tools","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop visualization-tools-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Visualization Tools CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint visualization-tools hackerdogs/visualization-tools-mcp:latest --help
```
