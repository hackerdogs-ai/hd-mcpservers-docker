# MCP Docker Server Configurations

This directory contains configuration files for MCP servers that can be dynamically built and run in Docker containers.

## Usage

Each JSON file defines an MCP server configuration that can be used with `mcp_docker_client.py` to:
1. Dynamically build a Docker image
2. Generate MCP server configuration for Docker execution
3. Run the server in an isolated container

## Configuration Format

### Python (pip) Package

```json
{
  "name": "server-name",
  "package_name": "pypi-package-name",
  "base_image": "python:3.11-slim",
  "additional_packages": ["package1", "package2"],
  "entrypoint": "python -m module_name",
  "env": {
    "ENV_VAR": "value"
  }
}
```

### npm Package

```json
{
  "name": "server-name",
  "npm_package": "@scope/package-name",
  "base_image": "node:20-slim",
  "additional_packages": ["package1", "package2"],
  "entrypoint": "npx @scope/package-name",
  "env": {
    "ENV_VAR": "value"
  }
}
```

### Fields

- **name**: Server name (used for image naming)
- **package_name**: PyPI package name (for pip install) - Python packages
- **npm_package**: npm package name (for npm install) - Node.js packages
- **base_image**: Base Docker image (default: python:3.11-slim for pip, node:20-slim for npm)
- **additional_packages**: System packages to install via apt-get
- **entrypoint**: Command to run the MCP server
  - Default for pip: `python -m <package_name>`
  - Default for npm: `npx <npm_package>`
- **env**: Environment variables to pass to container
- **dockerfile**: (Optional) Custom Dockerfile content as string
- **build_context**: (Optional) Build context directory for custom Dockerfile

## Examples

### Example 1: mcp-ocr (Python/pip)

The `mcp_ocr.json` file configures the mcp-ocr server:

```json
{
  "name": "ocr",
  "package_name": "mcp-ocr",
  "base_image": "python:3.11-slim",
  "additional_packages": ["tesseract-ocr", "tesseract-ocr-eng"],
  "entrypoint": "python -m mcp_ocr"
}
```

### Example 2: PDF Reader (npm/npx)

The `mcp_pdf_reader_sylphx.json` file configures the @sylphx/pdf-reader-mcp server:

```json
{
  "name": "pdf-reader-sylphx",
  "npm_package": "@sylphx/pdf-reader-mcp",
  "base_image": "node:20-slim",
  "entrypoint": "npx @sylphx/pdf-reader-mcp"
}
```

## Building and Testing

Use the test script to build and test configurations:

```bash
python shared/modules/tools/tests/test_mcp_docker_ocr.py
```

This will:
1. Build the Docker image for mcp-ocr
2. Generate the MCP configuration
3. Display the configuration JSON for use in your MCP client

## Integration

To use a built server in your MCP configuration:

1. Load the config JSON file
2. Use `build_mcp_server_docker()` to build the image
3. Add the returned configuration to your MCP config file

Example:

```python
import json
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker

# Load config
with open("mcp_docker_configs/mcp_ocr.json") as f:
    mcp_config = json.load(f)

# Build and get Docker config
docker_config = build_mcp_server_docker(mcp_config)

# Add to your MCP config
mcp_servers_config = {
    "mcpServers": {
        docker_config["name"]: {
            "command": docker_config["command"],
            "args": docker_config["args"]
        }
    }
}
```

