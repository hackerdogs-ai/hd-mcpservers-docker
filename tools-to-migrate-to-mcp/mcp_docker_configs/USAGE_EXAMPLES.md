# MCP Docker Wrapper - Usage Examples

## Supported Package Types

The MCP Docker wrapper supports three types of MCP servers:

1. **Python (pip) packages** - Use `package_name` field
2. **Node.js (npm) packages** - Use `npm_package` field  
3. **Custom Dockerfiles** - Use `dockerfile` field

## Example 1: Python Package (mcp-ocr)

```json
{
  "name": "ocr",
  "package_name": "mcp-ocr",
  "base_image": "python:3.11-slim",
  "additional_packages": ["tesseract-ocr", "tesseract-ocr-eng"],
  "entrypoint": "python -m mcp_ocr"
}
```

**Usage:**
```python
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json

config = json.load(open('mcp_docker_configs/mcp_ocr.json'))
result = build_mcp_server_docker(config)
```

## Example 2: npm Package (@sylphx/pdf-reader-mcp)

```json
{
  "name": "pdf-reader-sylphx",
  "npm_package": "@sylphx/pdf-reader-mcp",
  "base_image": "node:20-slim",
  "entrypoint": "npx @sylphx/pdf-reader-mcp"
}
```

**Usage:**
```python
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json

config = json.load(open('mcp_docker_configs/mcp_pdf_reader_sylphx.json'))
result = build_mcp_server_docker(config)
```

**Generated MCP Config:**
```json
{
  "mcpServers": {
    "pdf-reader-sylphx": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "NODE_ENV=production",
        "hackerdogs-mcp-pdf-reader-sylphx:latest"
      ]
    }
  }
}
```

**Note:** Container names are not specified (`--name` is omitted) to allow Docker to auto-generate unique names. This prevents conflicts when multiple discovery calls happen concurrently.

**Note:** Container names are not specified (`--name` is omitted) to allow Docker to auto-generate unique names. This prevents conflicts when multiple discovery calls happen concurrently.

## Example 3: Custom Dockerfile

```json
{
  "name": "custom-server",
  "dockerfile": "FROM node:20-slim\nRUN npm install -g my-package\nENTRYPOINT [\"npx\", \"my-package\"]"
}
```

## Converting npx Commands to Docker

If you have an MCP server that uses `npx`, you can convert it to Docker:

### Original npx Config:
```json
{
  "mcpServers": {
    "pdf-reader": {
      "command": "npx",
      "args": ["@sylphx/pdf-reader-mcp"]
    }
  }
}
```

### Docker Wrapper Config:
```json
{
  "name": "pdf-reader-sylphx",
  "npm_package": "@sylphx/pdf-reader-mcp",
  "base_image": "node:20-slim"
}
```

### Result:
The wrapper will:
1. Build a Docker image with Node.js and the npm package installed
2. Generate Docker run command configuration
3. Return MCP-compatible config ready to use

## Benefits of Docker Wrapper

✅ **Isolation**: Each server runs in its own container  
✅ **No Local Installation**: No need to install npm/pip packages on host  
✅ **Consistent Environment**: Same environment every time  
✅ **Easy Management**: Build once, use anywhere  
✅ **Security**: Container isolation and resource limits  

