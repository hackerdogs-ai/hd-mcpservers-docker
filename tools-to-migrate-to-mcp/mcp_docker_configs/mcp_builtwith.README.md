# BuiltWith MCP Server - Docker Wrapper

## Overview

This Docker wrapper provides access to the BuiltWith MCP server, which identifies the technology stack behind websites using the BuiltWith API. The server can discover frameworks, analytics tools, hosting services, CMS platforms, and more.

## Features

- **Domain Lookup**: Get comprehensive technology profiles for any website
- **Live Technologies Only**: Returns only currently active technologies
- **Detailed Information**: Provides technology name, description, tag, and documentation links

## Prerequisites

1. **BuiltWith API Key**: You need a valid API key from [BuiltWith](https://api.builtwith.com/)
2. **Docker**: Must be installed and running

## Configuration

### Environment Variables

The server requires the `BUILTWITH_API_KEY` environment variable:

```json
{
  "env": {
    "BUILTWITH_API_KEY": "your-api-key-here"
  }
}
```

## Usage

### Build the Docker Image

```python
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json

# Load config
with open('shared/modules/tools/mcp_docker_configs/mcp_builtwith.json') as f:
    config = json.load(f)

# Set API key in config
config['env']['BUILTWITH_API_KEY'] = 'your-api-key-here'

# Build Docker image and get MCP config
result = build_mcp_server_docker(config)

# Result contains:
# {
#   "name": "builtwith",
#   "command": "docker",
#   "args": [
#     "run",
#     "--rm",
#     "-i",
#     "--env",
#     "NODE_ENV=production",
#     "--env",
#     "BUILTWITH_API_KEY=your-api-key-here",
#     "hackerdogs-mcp-builtwith:latest"
#   ]
# }
```

### Use in MCP Configuration

Add to your MCP configuration file (e.g., `.cursor/mcp.json` or Claude Desktop config):

```json
{
  "mcpServers": {
    "builtwith": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "BUILTWITH_API_KEY=your-api-key-here",
        "hackerdogs-mcp-builtwith:latest"
      ]
    }
  }
}
```

## Available Tools

### `domain-lookup`

Returns the live web technologies used on a root domain.

**Parameters:**
- `domain` (string): The domain name to analyze (e.g., "example.com")

**Example Usage:**
- "What technologies is example.com using?"
- "What CMS does nytimes.com run on?"
- "Does amazon.com use Google Analytics?"
- "What JavaScript frameworks are used by spotify.com?"
- "What hosting provider does netflix.com use?"

**Response Format:**
```json
[
  {
    "Name": "Technology Name",
    "Description": "Technology description",
    "Tag": "Technology tag",
    "Link": "Documentation URL"
  }
]
```

## Testing

Test the build:
```bash
python3 -c "
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json
config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_builtwith.json'))
config['env']['BUILTWITH_API_KEY'] = 'your-api-key-here'
result = build_mcp_server_docker(config)
print('✅ Success!' if result else '❌ Failed')
print(json.dumps(result, indent=2))
"
```

## Docker Image

- **Image Name**: `hackerdogs-mcp-builtwith:latest`
- **Base Image**: `node:20-slim`
- **Source File**: `shared/modules/tools/osint/builtwith/bw-mcp-v1.js`

## File Structure

The Dockerfile copies the following files into the container:
- `shared/modules/tools/osint/builtwith/package.json` - Dependencies
- `shared/modules/tools/osint/builtwith/bw-mcp-v1.js` - MCP server implementation

## Benefits

✅ **Isolated environment** - Runs in Docker container  
✅ **No local Node.js conflicts** - Dependencies installed in container only  
✅ **Consistent execution** - Same Node.js version every time  
✅ **Easy deployment** - Single Docker image with all dependencies  
✅ **API key security** - API key passed as environment variable

## API Documentation

For more information about the BuiltWith API:
- [BuiltWith API Documentation](https://api.builtwith.com/)
- [BuiltWith Domain API](https://api.builtwith.com/domain-api)

## Error Handling

The server handles various error cases:
- Invalid API responses
- JSON parsing errors
- Missing or empty technology data
- Network errors

All errors return a structured error message:
```json
{
  "error": "No technologies found"
}
```


