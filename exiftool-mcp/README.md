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
