<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Open Legal Compliance MCP

Based on the README.md for the repository TCoder920x/open-legal-compliance-mcp

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/open-legal-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name open-legal-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8439 \
  -p 8439:8439 \
  hackerdogs/open-legal-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "open-legal-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/open-legal-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8439` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/open-legal-mcp:latest .
```

## Test

```bash
./test.sh
```
