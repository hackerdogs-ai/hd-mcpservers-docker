<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# PDF Reader MCP Server

MCP server wrapper for [PDF Reader MCP (Sylphx)](https://github.com/sylphxltd/pdf-reader-mcp) — extract and query text content from PDF files via URL or local path.

## What is PDF Reader?

PDF Reader MCP (by Sylphx) enables AI assistants to read, extract, and reason over PDF documents by fetching them from a URL or local file path and returning structured text content. It is built on the `@sylphx/pdf-reader-mcp` npm package and supports multi-page extraction and section targeting. See [sylphxltd/pdf-reader-mcp](https://github.com/sylphxltd/pdf-reader-mcp) for full documentation.

**No API keys required** — PDF Reader runs entirely locally inside the Docker container.

**Tools:**
- `pdf_reader_info` — Return basic info / status for PDF Reader MCP Server (Sylphx).

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Read the PDF at https://example.com/report.pdf and summarize its key findings."
- "Extract all text from pages 3 through 7 of /data/contract.pdf."
- "What does the PDF at https://arxiv.org/pdf/2301.00001.pdf say about methodology?"
- "Read /tmp/invoice.pdf and extract the total amount due and payment terms."
- "Fetch the PDF from https://example.com/manual.pdf and find the section on troubleshooting."
- "Compare the content of two PDFs: /data/v1.pdf and /data/v2.pdf, highlighting differences."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/pdf-reader-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8442:8442 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8442 \
  hackerdogs/pdf-reader-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "pdf-reader-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/pdf-reader-mcp:latest"],
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
    "pdf-reader-mcp": {
      "url": "http://localhost:8442/mcp"
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
    "pdf-reader-mcp": {
      "url": "http://localhost:8485/pdf-reader-mcp/mcp",
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
| `MCP_PORT` | `8442` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/pdf-reader-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name pdf-reader-mcp-test -p 8442:8442 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/pdf-reader-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8442/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8442/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8442/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"pdf_reader_info","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop pdf-reader-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the PDF Reader MCP server in the same container by overriding the entrypoint without starting the MCP wrapper.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/pdf-reader-mcp:latest mcp_server.py --help
```
