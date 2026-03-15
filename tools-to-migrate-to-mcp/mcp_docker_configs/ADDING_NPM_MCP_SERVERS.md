# Adding npm/npx MCP Servers to Docker Wrapper

## Overview

The MCP Docker wrapper now supports **npm packages** in addition to Python pip packages. This allows you to convert any `npx`-based MCP server into a Docker container automatically.

## Example: @sylphx/pdf-reader-mcp

### Original npx Configuration

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

### Docker Wrapper Configuration

Create `mcp_docker_configs/mcp_pdf_reader_sylphx.json`:

```json
{
  "name": "pdf-reader-sylphx",
  "npm_package": "@sylphx/pdf-reader-mcp",
  "base_image": "node:20-slim",
  "entrypoint": "npx @sylphx/pdf-reader-mcp",
  "env": {
    "NODE_ENV": "production"
  }
}
```

### Build and Use

```python
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json

# Load config
config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_pdf_reader_sylphx.json'))

# Build Docker image and get MCP config
result = build_mcp_server_docker(config)

# Result contains Docker-based MCP configuration
print(json.dumps({
    "mcpServers": {
        result["name"]: {
            "command": result["command"],
            "args": result["args"]
        }
    }
}, indent=2))
```

### Generated Output

```json
{
  "mcpServers": {
    "pdf-reader-sylphx": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--name",
        "hackerdogs-mcp-pdf-reader-sylphx-latest-container",
        "--env",
        "NODE_ENV=production",
        "hackerdogs-mcp-pdf-reader-sylphx:latest"
      ]
    }
  }
}
```

## Configuration Fields for npm Packages

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `name` | ✅ Yes | Server name (used for image naming) | `"pdf-reader-sylphx"` |
| `npm_package` | ✅ Yes | npm package name | `"@sylphx/pdf-reader-mcp"` |
| `base_image` | ❌ No | Base Docker image (default: `node:20-slim`) | `"node:20-slim"` |
| `entrypoint` | ❌ No | Command to run (default: `npx <npm_package>`) | `"npx @sylphx/pdf-reader-mcp"` |
| `additional_packages` | ❌ No | System packages via apt-get | `["curl", "wget"]` |
| `env` | ❌ No | Environment variables | `{"NODE_ENV": "production"}` |

## Benefits

✅ **No Local npm Installation**: Package runs in Docker container  
✅ **Isolation**: Each server in its own container  
✅ **Consistent Environment**: Same Node.js version every time  
✅ **Easy Migration**: Convert existing npx configs to Docker  

## Supported Package Types

The wrapper now supports:

1. **Python (pip)**: Use `package_name` field
2. **Node.js (npm)**: Use `npm_package` field
3. **Custom Dockerfile**: Use `dockerfile` field

## Testing

Test the npm package build:

```bash
python -c "from shared.modules.tools.mcp_docker_client import build_mcp_server_docker; import json; config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_pdf_reader_sylphx.json')); result = build_mcp_server_docker(config); print('✅ Success!' if result else '❌ Failed')"
```

## Docker Image

After building, the image will be available as:
- **Image Name**: `hackerdogs-mcp-{server-name}:latest`
- **Example**: `hackerdogs-mcp-pdf-reader-sylphx:latest`
- **Size**: ~516MB (includes Node.js runtime and npm package)


