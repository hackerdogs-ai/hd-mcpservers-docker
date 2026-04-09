<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# AACT Clinical Trials MCP Server

A Model Context Protocol (MCP) server implementation that provides access to the AACT (Aggregate Analysis of ClinicalTrials.gov https://aact

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/ctgov-mcp-docker-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name ctgov-mcp-docker-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8401 \
  -p 8401:8401 \
  hackerdogs/ctgov-mcp-docker-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "ctgov-mcp-docker-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/ctgov-mcp-docker-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8401` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/ctgov-mcp-docker-mcp:latest .
```

## Test

```bash
./test.sh
```
