# PageSpeed MCP Server Configuration

This file contains the MCP server configuration for the PageSpeed MCP server using the published Docker Hub image.

## Docker Hub Image

- **Image**: `hackerdogs/hackerdogs-mcp-pagespeed:latest`
- **Published**: Available on Docker Hub under the hackerdogs account
- **Source**: Built from `shared/modules/tools/osint/pagespeed-mcp/`

## Configuration

### For Cursor IDE

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "pagespeed": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "PAGESPEED_API_KEY=your-api-key-here",
        "hackerdogs/hackerdogs-mcp-pagespeed:latest"
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
    "pagespeed": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env",
        "PAGESPEED_API_KEY=your-api-key-here",
        "hackerdogs/hackerdogs-mcp-pagespeed:latest"
      ]
    }
  }
}
```

### For Standard MCP Configuration

Copy the contents of `mcp_pagespeed_server.json` to `~/.config/mcp/servers/pagespeed.json`.

## Prerequisites

1. **Docker** must be installed and running
2. **Google PageSpeed Insights API Key** (Optional but recommended)
   - **The server works without an API key** - no key required for basic usage
   - **API key is only needed for higher rate limits** (without key: ~25 requests/day, with key: much higher limits)
   - See "Getting a PageSpeed API Key" section below if you want higher limits
3. **Docker Hub Access** - The image will be automatically pulled from Docker Hub on first use

## Getting a PageSpeed API Key (Optional)

If you want higher rate limits, you can get a free Google PageSpeed Insights API key:

1. **Go to Google Cloud Console**: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. **Create or select a project**
3. **Enable the PageSpeed Insights API**:
   - Go to "APIs & Services" > "Library"
   - Search for "PageSpeed Insights API"
   - Click "Enable"
4. **Create an API Key**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key
5. **Optional: Restrict the API key** (recommended for security):
   - Click on the created API key
   - Under "API restrictions", select "Restrict key"
   - Choose "PageSpeed Insights API"
   - Save

**Note**: The API key is completely optional. The server works fine without it, just with lower rate limits.

## Environment Variables (Optional)

The API key is **completely optional**. The server works without it.

If you want to use an API key for higher rate limits, add it as an environment variable:

```json
"--env",
"PAGESPEED_API_KEY=your-actual-api-key"
```

**Alternative**: You can also pass the API key as a parameter to the `run_pagespeed_test` tool call instead of using an environment variable.

## Available Tools

### `run_pagespeed_test`

Runs a comprehensive PageSpeed Insights test on a URL.

**Parameters:**
- `url` (string, required): The URL to analyze (e.g., "https://example.com")
- `strategy` (enum, optional): "mobile" or "desktop" (default: "mobile")
- `category` (array, optional): Categories to analyze - ["accessibility", "best-practices", "performance", "pwa", "seo"] (default: ["performance"])
- `locale` (string, optional): Locale for the report (default: "en")
- `apiKey` (string, optional): Google PageSpeed Insights API key (optional, can also be set via environment variable)

**Example Usage:**
- "Analyze the performance of example.com"
- "Run a mobile PageSpeed test on nytimes.com"
- "Check SEO and accessibility for amazon.com"
- "Get Core Web Vitals for spotify.com"
- "Analyze performance, SEO, and accessibility for netflix.com"

**Response Format:**
```json
{
  "lighthouseResult": {
    "categories": {
      "performance": { "score": 0.95, ... },
      "accessibility": { "score": 0.98, ... },
      "best-practices": { "score": 0.92, ... },
      "seo": { "score": 0.99, ... }
    },
    "audits": { ... },
    "timing": { ... },
    "stackPacks": { ... }
  }
}
```

## Pulling the Image

The Docker image will be automatically pulled from Docker Hub when first used. To manually pull:

```bash
docker pull hackerdogs/hackerdogs-mcp-pagespeed:latest
```

## Verification

After adding the configuration, restart your MCP client (Cursor, Claude Desktop, etc.) and verify the server is connected. You should see the `run_pagespeed_test` tool available.

## Troubleshooting

### Image Not Found

If you get an error that the image doesn't exist:
1. Ensure you're logged into Docker Hub (if required)
2. Verify the image exists: `docker pull hackerdogs/hackerdogs-mcp-pagespeed:latest`
3. Check that the image was published: Visit [Docker Hub](https://hub.docker.com/r/hackerdogs/hackerdogs-mcp-pagespeed)

### API Key Issues

If you're using an API key and get rate limit errors:
1. Verify your `PAGESPEED_API_KEY` is correct
2. Check that the PageSpeed Insights API is enabled in your Google Cloud project
3. Ensure the API key has sufficient quota
4. **Note**: If you don't have an API key, the server still works but with lower rate limits (~25 requests/day). This is usually fine for personal use.

### Docker Not Running

```bash
# Start Docker Desktop or Docker daemon
# On macOS: Open Docker Desktop
# On Linux: sudo systemctl start docker
```

### Rate Limiting

- **Without API Key**: Limited to a few requests per day
- **With API Key**: Higher rate limits (varies by Google Cloud project quota)
- If you hit rate limits, wait and retry, or use an API key for higher limits

## Related Files

- **Build Config**: `shared/modules/tools/mcp_docker_configs/mcp_pagespeed.json`
- **Source Code**: `shared/modules/tools/osint/pagespeed-mcp/`
- **Docker Build**: `shared/modules/tools/publish_docker_images.sh`
- **Documentation**: `shared/modules/tools/mcp_docker_configs/mcp_pagespeed.README.md`

## Publishing

The image is published using:

```bash
./shared/modules/tools/publish_docker_images.sh
```

This builds and pushes the image to `hackerdogs/hackerdogs-mcp-pagespeed:latest` on Docker Hub.

## Performance Metrics

The server provides detailed analysis including:

- **Performance Metrics**: FCP, LCP, TTI, TBT, CLS, Speed Index, TTFB
- **SEO Analysis**: Meta tags, structured data, robots.txt, crawlability
- **Accessibility**: ARIA attributes, color contrast, heading hierarchy, alt text
- **Best Practices**: HTTPS, JavaScript errors, deprecated APIs, image optimization

