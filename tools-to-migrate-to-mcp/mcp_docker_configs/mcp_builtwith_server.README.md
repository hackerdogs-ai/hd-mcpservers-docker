# BuiltWith MCP Server Configuration

This file contains the MCP server configuration for the BuiltWith MCP server using the published Docker Hub image.

## Docker Hub Image

- **Image**: `hackerdogs/hackerdogs-mcp-builtwith:latest`
- **Published**: Available on Docker Hub under the hackerdogs account
- **Source**: Built from `shared/modules/tools/osint/builtwith/bw-mcp-v1.js`

## Configuration

### For Cursor IDE

Add to `~/.cursor/mcp.json`:

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
        "hackerdogs/hackerdogs-mcp-builtwith:latest"
      ]
    }
  }
}
```

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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
        "hackerdogs/hackerdogs-mcp-builtwith:latest"
      ]
    }
  }
}
```

### For Standard MCP Configuration

Copy the contents of `mcp_builtwith_server.json` to `~/.config/mcp/servers/builtwith.json`.

## Prerequisites

1. **Docker** must be installed and running
2. **BuiltWith API Key** - Get your API key from [api.builtwith.com](https://api.builtwith.com/)
3. **Docker Hub Access** - The image will be automatically pulled from Docker Hub on first use

## Environment Variables

Replace `your-api-key-here` with your actual BuiltWith API key:

```json
"--env",
"BUILTWITH_API_KEY=your-actual-api-key"
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

## Pulling the Image

The Docker image will be automatically pulled from Docker Hub when first used. To manually pull:

```bash
docker pull hackerdogs/hackerdogs-mcp-builtwith:latest
```

## Verification

After adding the configuration, restart your MCP client (Cursor, Claude Desktop, etc.) and verify the server is connected. You should see the `domain-lookup` tool available.

## Troubleshooting

### Image Not Found

If you get an error that the image doesn't exist:
1. Ensure you're logged into Docker Hub (if required)
2. Verify the image exists: `docker pull hackerdogs/hackerdogs-mcp-builtwith:latest`
3. Check that the image was published: Visit [Docker Hub](https://hub.docker.com/r/hackerdogs/hackerdogs-mcp-builtwith)

### API Key Issues

If you get "No technologies found" errors:
1. Verify your `BUILTWITH_API_KEY` is correct
2. Check that your API key has sufficient credits/quota
3. Ensure the API key is properly set in the environment variable

### Docker Not Running

```bash
# Start Docker Desktop or Docker daemon
# On macOS: Open Docker Desktop
# On Linux: sudo systemctl start docker
```

## Related Files

- **Build Config**: `shared/modules/tools/mcp_docker_configs/mcp_builtwith.json`
- **Source Code**: `shared/modules/tools/osint/builtwith/bw-mcp-v1.js`
- **Docker Build**: `shared/modules/tools/publish_docker_images.sh`
- **Documentation**: `shared/modules/tools/mcp_docker_configs/mcp_builtwith.README.md`

## Publishing

The image is published using:

```bash
./shared/modules/tools/publish_docker_images.sh
```

This builds and pushes the image to `hackerdogs/hackerdogs-mcp-builtwith:latest` on Docker Hub.


