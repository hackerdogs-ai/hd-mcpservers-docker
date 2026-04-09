<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Trivy Security MCP server

A Model Context Protocol (MCP) server that integrates the Trivy security scanner. It enables AI assistants to perform automated security ass

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/trivy-security-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name trivy-security-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8456 \
  -p 8456:8456 \
  hackerdogs/trivy-security-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "trivy-security-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/trivy-security-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8456` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/trivy-security-mcp:latest .
```

## Test

```bash
./test.sh
```
