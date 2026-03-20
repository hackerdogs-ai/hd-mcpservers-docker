<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Shodan MCP

A dual-purpose cybersecurity server that combines Shodan’s internet-scale device intelligence with VirusTotal’s reputation analysis. It allo

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/shodan-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name shodan-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8453 \
  -p 8453:8453 \
  hackerdogs/shodan-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "shodan-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/shodan-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8453` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/shodan-mcp:latest .
```

## Test

```bash
./test.sh
```
