<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Crawl4Ai MCP Server

MCP server wrapper for [Crawl4AI](https://github.com/unclecode/crawl4ai) — high-performance, AI-ready web crawler that extracts clean markdown content from any URL.

## What is Crawl4AI?

Crawl4AI is an open-source Python web crawler purpose-built for LLM workflows. It fetches pages, strips boilerplate, and returns clean structured text or markdown, with optional CSS selector targeting and screenshot capture. It connects to a running Crawl4AI service instance via its REST API. See [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) for full documentation.

**Optional API token** — set `CRAWL4AI_API_TOKEN` if your Crawl4AI service instance requires authentication. The `CRAWL4AI_URL` environment variable points to the service (default: `http://localhost:11235`).

**Tools:**
- `crawl4ai_crawl` — Crawl a URL and return extracted text content, with optional CSS selector filtering and screenshot capture.

## Tools Reference

### `crawl4ai_crawl`

Crawl a URL using the Crawl4AI service and return extracted page text.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | URL to crawl |
| `css_selector` | string | No | `""` | Limit extraction to elements matching this CSS selector |
| `screenshot` | boolean | No | `false` | Capture a screenshot alongside the text extraction |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Crawl https://example.com and return the extracted text content."
- "Use Crawl4AI to fetch the main article text from a news URL, targeting only the `.article-body` CSS class."
- "Crawl a documentation page and extract all the text so I can summarize it."
- "Take a screenshot while crawling https://example.com to verify the page loaded correctly."
- "Use Crawl4AI to fetch product descriptions from an e-commerce page."
- "Extract the text from multiple research paper abstract pages for summarization."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/crawl4ai-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8521:8521 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8521 \
  hackerdogs/crawl4ai-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "crawl4ai-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/crawl4ai-mcp:latest"],
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
    "crawl4ai-mcp": {
      "url": "http://localhost:8521/mcp"
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
    "crawl4ai-mcp": {
      "url": "http://localhost:8485/crawl4ai-mcp/mcp",
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
| `MCP_PORT` | `8521` | HTTP port (only used with `streamable-http`) |
| `CRAWL4AI_API_TOKEN` | `` | Crawl4ai api token |

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
docker build -t hackerdogs/crawl4ai-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name crawl4ai-mcp-test -p 8521:8521 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/crawl4ai-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8521/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8521/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8521/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_crawl4ai","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop crawl4ai-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Crawl4Ai CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint crawl4ai hackerdogs/crawl4ai-mcp:latest --help
```
