# MCP Server Configuration for Claude/Cursor

This file (`mcpServer.json`) contains Docker-based MCP server configurations ready to use in Claude Desktop or Cursor IDE.

## Servers Included

### 1. OCR Server
- **Name:** `ocr`
- **Image:** `hackerdogs-mcp-ocr:latest`
- **Tool:** `perform_ocr`
- **Description:** Extract text from images using Tesseract OCR
- **Supports:** Local files, URLs, and base64-encoded image data

### 2. PDF Reader Server
- **Name:** `pdf-reader`
- **Image:** `hackerdogs-mcp-pdf-reader-sylphx:latest`
- **Tool:** `read_pdf`
- **Description:** Extract text from PDF files via URLs
- **Supports:** PDF URLs via sources array format

### 3. BuiltWith Server
- **Name:** `builtwith`
- **Image:** `hackerdogs/hackerdogs-mcp-builtwith:latest` (Docker Hub)
- **Tool:** `domain-lookup`
- **Description:** Identify technology stack behind websites using BuiltWith API
- **Supports:** Domain lookup to discover frameworks, analytics tools, hosting services, CMS platforms
- **Requires:** `BUILTWITH_API_KEY` environment variable

### 4. PageSpeed Server
- **Name:** `pagespeed`
- **Image:** `hackerdogs/hackerdogs-mcp-pagespeed:latest` (Docker Hub)
- **Tool:** `run_pagespeed_test`
- **Description:** Perform comprehensive web performance analysis using Google PageSpeed Insights API
- **Supports:** Performance metrics, Core Web Vitals, SEO analysis, accessibility audits, best practices assessment
- **Requires:** `PAGESPEED_API_KEY` environment variable (optional but recommended)

## Prerequisites

1. **Docker must be installed and running**
2. **Docker images must be built** (see build instructions below)

## Building Docker Images

### OCR Server
```bash
python -c "from shared.modules.tools.mcp_docker_client import build_mcp_server_docker; import json; config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_ocr.json')); build_mcp_server_docker(config, force_rebuild=True)"
```

### PDF Reader Server
```bash
python -c "from shared.modules.tools.mcp_docker_client import build_mcp_server_docker; import json; config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_pdf_reader_sylphx.json')); build_mcp_server_docker(config, force_rebuild=True)"
```

### BuiltWith Server
```bash
python -c "from shared.modules.tools.mcp_docker_client import build_mcp_server_docker; import json; config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_builtwith.json')); build_mcp_server_docker(config, force_rebuild=True)"
```

### PageSpeed Server
```bash
python -c "from shared.modules.tools.mcp_docker_client import build_mcp_server_docker; import json; config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_pagespeed.json')); build_mcp_server_docker(config, force_rebuild=True)"
```

## Publishing to Docker Hub

All servers can be published to Docker Hub using the publish script:

```bash
./shared/modules/tools/publish_docker_images.sh
```

This will build and push:
- `hackerdogs/hackerdogs-mcp-ocr:latest`
- `hackerdogs/hackerdogs-mcp-pdf-reader-sylphx:latest`
- `hackerdogs/hackerdogs-mcp-builtwith:latest`
- `hackerdogs/hackerdogs-mcp-pagespeed:latest`

**Note:** BuiltWith and PageSpeed servers use Docker Hub images, so they will be automatically pulled when first used. OCR and PDF Reader use local images by default.

## Usage in Claude Desktop

1. Copy the contents of `mcpServer.json`
2. Open Claude Desktop settings
3. Navigate to MCP servers configuration
4. Add the JSON configuration
5. Restart Claude Desktop

## Usage in Cursor IDE

1. Copy the contents of `mcpServer.json`
2. Add to your Cursor MCP configuration file (typically `.cursor/mcp.json` or similar)
3. Restart Cursor IDE

## Configuration Format

The configuration uses standard MCP server format with Docker commands:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "--env", "ENV_VAR=value", "image:tag"],
      "description": "Server description"
    }
  }
}
```

**Note:** Container names are not specified (`--name` is omitted) to allow Docker to auto-generate unique names. This prevents conflicts when multiple discovery calls happen concurrently. Containers are ephemeral (`--rm`) so names don't need to be predictable.

## Testing

### Test OCR Server
```bash
python shared/modules/tools/tests/test_mcp_docker_ocr_functional_simple.py
```

### Test PDF Reader Server
```bash
python shared/modules/tools/tests/test_mcp_docker_pdf_reader_functional.py
```

### Test BuiltWith Server
After adding the configuration, restart your MCP client and test with:
- "What technologies is example.com using?"
- "What CMS does nytimes.com run on?"

### Test PageSpeed Server
After adding the configuration, restart your MCP client and test with:
- "Analyze the performance of example.com"
- "Run a mobile PageSpeed test on nytimes.com"
- "Check SEO and accessibility for amazon.com"

## Troubleshooting

- **Container not starting:** Ensure Docker is running and images are built
- **Permission errors:** Check Docker permissions
- **Connection issues:** Verify container names don't conflict with existing containers

