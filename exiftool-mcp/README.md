# exiftool-mcp

MCP server for extracting metadata from images, PDFs, and documents using ExifTool.

## Tools

| Tool | Description |
|------|------------|
| exiftool_extract | Extract metadata (EXIF, IPTC, XMP, GPS, author) from files or URLs |

## Quick Start

```bash
docker build -t exiftool-mcp .
docker run -p 8502:8502 -e MCP_TRANSPORT=streamable-http exiftool-mcp
```

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "exiftool-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/exiftool-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8502:8502 -e MCP_TRANSPORT=streamable-http hackerdogs/exiftool-mcp:latest
```

```json
{
  "mcpServers": {
    "exiftool-mcp": {
      "url": "http://localhost:8502/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
