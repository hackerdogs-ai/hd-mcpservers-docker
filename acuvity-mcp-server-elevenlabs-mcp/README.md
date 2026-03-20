<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Eleven Labs MCP Server

Official ElevenLabs Model Context Protocol (MCP) server that enables interaction with powerful Text to Speech and audio processing APIs.   E

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-elevenlabs-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8417 \
  -p 8417:8417 \
  hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-elevenlabs-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8417` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest .
```

## Test

```bash
./test.sh
```
