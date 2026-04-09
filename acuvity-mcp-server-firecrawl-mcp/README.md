<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Firecrawl MCP Server

A Model Context Protocol (MCP) server implementation that integrates with Firecrawl for web scraping capabilities.

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-firecrawl-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-firecrawl-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8421 \
  -p 8421:8421 \
  hackerdogs/acuvity-mcp-server-firecrawl-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-firecrawl-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-firecrawl-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8421` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-firecrawl-mcp:latest .
```

## Test

```bash
./test.sh
```
