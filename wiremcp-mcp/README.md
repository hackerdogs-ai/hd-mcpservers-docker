<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Wiremcp

A Model Context Protocol (MCP) server that connects AI assistants to Wireshark (via tshark) for real-time network traffic analysis. It empow

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/wiremcp-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name wiremcp-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8458 \
  -p 8458:8458 \
  hackerdogs/wiremcp-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "wiremcp-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/wiremcp-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8458` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/wiremcp-mcp:latest .
```

## Test

```bash
./test.sh
```
