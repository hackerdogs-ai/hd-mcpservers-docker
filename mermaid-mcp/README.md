<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Mermaid MCP Server

MCP server wrapper for [Mermaid](https://github.com/mermaid-js/mermaid-cli) — render Mermaid diagram source into SVG or PNG output.

## What is Mermaid?

Mermaid is a text-based diagramming language that lets you create flowcharts, sequence diagrams, class diagrams, Gantt charts, and more using a simple Markdown-like syntax. This MCP server wraps the official `@mermaid-js/mermaid-cli` (`mmdc`) tool to convert Mermaid source code into SVG or PNG images. See [mermaid-js/mermaid-cli](https://github.com/mermaid-js/mermaid-cli) for full documentation.

**No API keys required** — Mermaid renders diagrams locally inside the Docker container using a headless Chromium browser.

**Tools:**
- `render_mermaid` — Render Mermaid diagram source to SVG or PNG. Accepts raw Mermaid syntax and an `output_format` of `svg` (default) or `png`.

## Tools Reference

### `render_mermaid`

Render a Mermaid diagram to SVG or PNG.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content` | str | Yes | — | Mermaid diagram source code |
| `output_format` | str | No | `svg` | Output format: `svg` or `png` |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Render this Mermaid flowchart as an SVG: `graph TD; A-->B; B-->C`."
- "Create a Mermaid sequence diagram for a login flow and render it to PNG."
- "Generate a Mermaid class diagram for a simple user model and return the SVG."
- "Draw a Gantt chart in Mermaid showing a 3-sprint project timeline."
- "Render a Mermaid state diagram for an order lifecycle (placed, shipped, delivered)."
- "Convert this Mermaid ER diagram to SVG so I can embed it in my docs."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/mermaid-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8524:8524 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8524 \
  hackerdogs/mermaid-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "mermaid-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/mermaid-mcp:latest"],
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
    "mermaid-mcp": {
      "url": "http://localhost:8524/mcp"
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
    "mermaid-mcp": {
      "url": "http://localhost:8485/mermaid-mcp/mcp",
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
| `MCP_PORT` | `8524` | HTTP port (only used with `streamable-http`) |
| `PUPPETEER_EXECUTABLE_PATH` | `/usr/bin/chromium` | Puppeteer executable path |

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
docker build -t hackerdogs/mermaid-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name mermaid-mcp-test -p 8524:8524 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/mermaid-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8524/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8524/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8524/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"render_mermaid","arguments":{"content":"graph TD; A-->B","output_format":"svg"}}}'
```

**4. Clean up:**

```bash
docker stop mermaid-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Mermaid CLI (`mmdc`) in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint mmdc hackerdogs/mermaid-mcp:latest --help
```
