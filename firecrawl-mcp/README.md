<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Firecrawl MCP Server

MCP server wrapper for [Firecrawl](https://firecrawl.dev/) — JavaScript-rendered web scraping and full-site crawling with clean markdown output. See [mendableai/firecrawl](https://github.com/mendableai/firecrawl) for full documentation.

## What is Firecrawl?

Firecrawl is a managed web scraping API that handles headless browser rendering, anti-bot bypasses, and content extraction so you get clean, LLM-ready markdown instead of raw HTML. The MCP server exposes tools for scraping individual URLs, crawling entire websites, and performing structured data extraction with a JSON schema. It is ideal for turning dynamic web pages — documentation sites, product listings, dashboards — into content an AI can reason about.

**API key required** — sign up at [firecrawl.dev](https://firecrawl.dev/) and set `FIRECRAWL_API_KEY`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `firecrawl_scrape` | Firecrawl Scrape |
| `firecrawl_map` | Firecrawl Map |
| `firecrawl_search` | Firecrawl Search |
| `firecrawl_search_feedback` | Firecrawl Search Feedback |
| `firecrawl_feedback` | Firecrawl Feedback |
| `firecrawl_crawl` | Firecrawl Crawl |
| `firecrawl_check_crawl_status` | Firecrawl Check Crawl Status |
| `firecrawl_extract` | Firecrawl Extract |
| `firecrawl_agent` | Firecrawl Agent |
| `firecrawl_agent_status` | Firecrawl Agent Status |
| `firecrawl_interact` | Firecrawl Interact |
| `firecrawl_interact_stop` | Firecrawl Interact Stop |
| `firecrawl_parse` | Firecrawl Parse |
| `firecrawl_monitor_create` | Firecrawl Monitor Create |
| `firecrawl_monitor_list` | Firecrawl Monitor List |
| `firecrawl_monitor_get` | Firecrawl Monitor Get |
| `firecrawl_monitor_update` | Firecrawl Monitor Update |
| `firecrawl_monitor_delete` | Firecrawl Monitor Delete |
| `firecrawl_monitor_run` | Firecrawl Monitor Run |
| `firecrawl_monitor_checks` | Firecrawl Monitor Checks |
| `firecrawl_monitor_check` | Firecrawl Monitor Check |
| `firecrawl_research_search_papers` | Firecrawl Research Search Papers |
| `firecrawl_research_inspect_paper` | Firecrawl Research Inspect Paper |
| `firecrawl_research_related_papers` | Firecrawl Research Related Papers |
| `firecrawl_research_read_paper` | Firecrawl Research Read Paper |
| `firecrawl_research_search_github` | Firecrawl Research Search Github |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Scrape https://docs.example.com/getting-started and summarize the installation steps."
- "Crawl all pages under https://blog.example.com and find posts about security."
- "Extract the product name, price, and description from https://shop.example.com/item/42 using structured extraction."
- "Scrape the table of contents at https://docs.example.com and list all section headings."
- "Crawl https://example.com with a depth of 2 and return all pages that mention 'authentication'."
- "Fetch https://status.example.com as markdown and tell me if any services are degraded."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e FIRECRAWL_API_KEY \
  hackerdogs/firecrawl-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8640:8640 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8640 \
  -e FIRECRAWL_API_KEY \
  hackerdogs/firecrawl-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "firecrawl-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "FIRECRAWL_API_KEY",
        "hackerdogs/firecrawl-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "FIRECRAWL_API_KEY": ""
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
    "firecrawl-mcp": {
      "url": "http://localhost:8640/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8640` | HTTP port (only used with `streamable-http`) |
| `FIRECRAWL_API_KEY` | — | Firecrawl API key — get one at [firecrawl.dev](https://firecrawl.dev/) |

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
docker build -t hackerdogs/firecrawl-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name firecrawl-mcp-test -p 8640:8640 \
  -e MCP_TRANSPORT=streamable-http \
  -e FIRECRAWL_API_KEY \
  hackerdogs/firecrawl-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8640/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8640/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8640/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop firecrawl-mcp-test
```
