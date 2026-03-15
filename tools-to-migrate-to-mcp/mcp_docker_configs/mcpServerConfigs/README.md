# MCP Server Docker Configurations

This directory contains individual `mcpServers` configuration files for each Docker-based MCP server published to Docker Hub under the `hackerdogs` organization.

## Overview

Each JSON file in this directory follows the standard MCP server configuration format (`mcpServers`) and can be:
- Used directly in Claude Desktop, Cursor IDE, or other MCP-compatible clients
- Merged into larger configuration files
- Referenced for Docker image names and environment variables

## Available Servers

### 1. OCR Server (`ocr.json`)
- **Docker Image**: `hackerdogs/hackerdogs-mcp-ocr:latest`
- **Description**: Extract text from images using Tesseract OCR
- **Environment Variables**: `PYTHONUNBUFFERED=1`
- **Source**: PyPI package `mcp-ocr`

### 2. PDF Reader Server (`pdf-reader-sylphx.json`)
- **Docker Image**: `hackerdogs/hackerdogs-mcp-pdf-reader-sylphx:latest`
- **Description**: Extract text from PDF files using @sylphx/pdf-reader-mcp
- **Environment Variables**: `NODE_ENV=production`
- **Source**: npm package `@sylphx/pdf-reader-mcp`

### 3. RSS Server (`rss.json`)
- **Docker Image**: `hackerdogs/rss-mcp:latest`
- **Description**: Fetch and parse RSS feeds using rss-mcp npm package
- **Environment Variables**: 
  - `NODE_ENV=production`
  - `NODE_OPTIONS=--no-warnings`
- **Source**: npm package `rss-mcp`

### 4. BuiltWith Server (`builtwith.json`)
- **Docker Image**: `hackerdogs/hackerdogs-mcp-builtwith:latest`
- **Description**: Identify technology stack behind websites using BuiltWith API
- **Environment Variables**: 
  - `NODE_ENV=production`
  - `BUILTWITH_API_KEY=your-api-key-here` (required)
- **Source**: Custom Dockerfile from `shared/modules/tools/osint/builtwith/`

### 5. PageSpeed Server (`pagespeed.json`)
- **Docker Image**: `hackerdogs/hackerdogs-mcp-pagespeed:latest`
- **Description**: Perform comprehensive web performance analysis using Google PageSpeed Insights API
- **Environment Variables**: `NODE_ENV=production`
- **Note**: API key is optional (can be passed as tool parameter or via `--env PAGESPEED_API_KEY`)
- **Source**: Custom Dockerfile from `shared/modules/tools/osint/pagespeed-mcp/`

### 6. YouTube Server (`youtube.json`)
- **Docker Image**: `hackerdogs/hackerdogs-mcp-youtube:latest`
- **Description**: Interact with YouTube content through Model Context Protocol. Enables video information retrieval, transcript management, channel management, and playlist operations.
- **Environment Variables**: 
  - `NODE_ENV=production`
  - `YOUTUBE_API_KEY=your-youtube-api-key-here` (required)
  - `YOUTUBE_TRANSCRIPT_LANG=en` (optional, defaults to 'en')
- **Source**: npm package `zubeid-youtube-mcp-server` from [GitHub](https://github.com/ZubeidHendricks/youtube-mcp-server)

### 7. Alpaca MCP Server (`alpaca.json`)
- **Docker Image**: `mcp/alpaca:latest` — **build locally** (not published to Docker Hub)
- **Description**: Alpaca Trading API via MCP (stocks, ETF, options, crypto, portfolio, market data).
- **Environment Variables**: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_PAPER_TRADE=True` (optional)
- **Source**: [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server). See `alpaca.README.md` for build steps.

## Usage

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "ocr": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "PYTHONUNBUFFERED=1",
        "hackerdogs/hackerdogs-mcp-ocr:latest"
      ]
    }
  }
}
```

### For Cursor IDE

Add to `.cursor/mcp.json` or workspace settings:

```json
{
  "mcpServers": {
    "ocr": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "PYTHONUNBUFFERED=1",
        "hackerdogs/hackerdogs-mcp-ocr:latest"
      ]
    }
  }
}
```

### Merging Multiple Servers

You can combine multiple server configs by merging the `mcpServers` objects:

```json
{
  "mcpServers": {
    "ocr": { ... },
    "pdf-reader-sylphx": { ... },
    "rss": { ... },
    "builtwith": { ... },
    "pagespeed": { ... },
    "youtube": { ... }
  }
}
```

## Prerequisites

1. **Docker**: Must be installed and running
2. **Docker Hub Access**: Images are pulled from `hackerdogs` organization on Docker Hub
3. **API Keys**: Some servers require API keys (BuiltWith, YouTube, PageSpeed)
   - Set these via `--env` flags in the Docker args or replace placeholder values

## Publishing

These Docker images are built and published using the `publish_docker_images.sh` script located in `shared/modules/tools/`.

To rebuild and republish all images:

```bash
cd shared/modules/tools
./publish_docker_images.sh
```

## Related Files

- **Docker Build Configs**: `../mcp_*.json` - Configuration files used to build Docker images
- **Publish Script**: `../../publish_docker_images.sh` - Script to build and publish images
- **Docker Client**: `../../mcp_docker_client.py` - Python module for building MCP Docker images
- **Combined Config**: `../mcpServer.json` - Combined configuration with all servers

## Notes

- All images use `--rm` flag to automatically remove containers after execution
- All images use `-i` flag for interactive mode (required for stdio communication)
- Environment variables can be customized by modifying the `--env` entries in the args array
- For servers requiring API keys, replace placeholder values with actual keys before use


