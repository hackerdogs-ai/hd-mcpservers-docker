# powerpoint-tools-mcp

MCP server for creating and reading PowerPoint (PPTX) presentations.

## Tools

| Tool | Description |
|------|------------|
| create_presentation | Create a PPTX from JSON slide definitions |
| read_presentation | Extract text from all slides in a PPTX |
| get_presentation_info | Get metadata and shape info for a PPTX |

## Quick Start

```bash
docker build -t powerpoint-tools-mcp .
docker run -p 8507:8507 -e MCP_TRANSPORT=streamable-http powerpoint-tools-mcp
```

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "powerpoint-tools-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/powerpoint-tools-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8507:8507 -e MCP_TRANSPORT=streamable-http hackerdogs/powerpoint-tools-mcp:latest
```

```json
{
  "mcpServers": {
    "powerpoint-tools-mcp": {
      "url": "http://localhost:8507/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
