# PageSpeed MCP Server - Docker Wrapper

## Overview

This Docker wrapper provides access to the PageSpeed MCP server, which performs comprehensive web performance analysis using Google's PageSpeed Insights API. The server can analyze performance metrics, Core Web Vitals, SEO, accessibility, and best practices for any website.

## Features

- **Performance Metrics**: First Contentful Paint (FCP), Largest Contentful Paint (LCP), Time to Interactive (TTI), Total Blocking Time (TBT), Cumulative Layout Shift (CLS), Speed Index, Time to First Byte (TTFB)
- **SEO Analysis**: Meta description validation, robots.txt validation, structured data validation, crawlable links verification
- **Accessibility Audits**: ARIA attribute validation, color contrast checking, heading hierarchy analysis, alt text verification
- **Best Practices**: HTTPS usage, JavaScript error monitoring, deprecated API usage, image aspect ratio analysis
- **Resource Optimization**: Image optimization suggestions, JavaScript bundling analysis, CSS optimization recommendations

## Prerequisites

1. **Docker** must be installed and running

2. **Google PageSpeed Insights API Key** (Optional - not required!)
   - **The server works without an API key** - no key needed for basic usage
   - **API key is only for higher rate limits** (without key: ~25 requests/day, with key: much higher)
   - To get an API key (if you want higher limits):
     1. Go to [Google Cloud Console](https://console.cloud.google.com/)
     2. Create or select a project
     3. Enable "PageSpeed Insights API" in APIs & Services > Library
     4. Create an API key in APIs & Services > Credentials
     5. (Optional) Restrict the key to PageSpeed Insights API only

## Configuration

### Environment Variables

The server optionally accepts the `PAGESPEED_API_KEY` environment variable:

```json
{
  "env": {
    "PAGESPEED_API_KEY": "your-api-key-here"
  }
}
```

**Note**: The API key can also be passed as a parameter to the tool call, so it's optional in the Docker configuration.

## Usage

### Build the Docker Image

```python
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json

# Load config
with open('shared/modules/tools/mcp_docker_configs/mcp_pagespeed.json') as f:
    config = json.load(f)

# Optionally set API key in config
config['env']['PAGESPEED_API_KEY'] = 'your-api-key-here'

# Build Docker image and get MCP config
result = build_mcp_server_docker(config)

# Result contains:
# {
#   "name": "pagespeed",
#   "command": "docker",
#   "args": [
#     "run",
#     "--rm",
#     "-i",
#     "--env",
#     "NODE_ENV=production",
#     "--env",
#     "PAGESPEED_API_KEY=your-api-key-here",
#     "hackerdogs-mcp-pagespeed:latest"
#   ]
# }
```

### Use in MCP Configuration

Add to your MCP configuration file (e.g., `.cursor/mcp.json` or Claude Desktop config):

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

## Testing

Test the build:
```bash
python3 -c "
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker
import json
config = json.load(open('shared/modules/tools/mcp_docker_configs/mcp_pagespeed.json'))
config['env']['PAGESPEED_API_KEY'] = 'your-api-key-here'
result = build_mcp_server_docker(config)
print('✅ Success!' if result else '❌ Failed')
print(json.dumps(result, indent=2))
"
```

## Docker Image

- **Image Name**: `hackerdogs-mcp-pagespeed:latest`
- **Base Image**: `node:20-slim`
- **Source Files**: 
  - `shared/modules/tools/osint/pagespeed-mcp/package.json`
  - `shared/modules/tools/osint/pagespeed-mcp/dist/index.js`

## File Structure

The Dockerfile copies the following files into the container:
- `shared/modules/tools/osint/pagespeed-mcp/package.json` - Dependencies
- `shared/modules/tools/osint/pagespeed-mcp/package-lock.json` - Locked dependencies
- `shared/modules/tools/osint/pagespeed-mcp/dist/index.js` - Compiled MCP server

## Benefits

✅ **Isolated environment** - Runs in Docker container  
✅ **No local Node.js conflicts** - Dependencies installed in container only  
✅ **Consistent execution** - Same Node.js version every time  
✅ **Easy deployment** - Single Docker image with all dependencies  
✅ **API key flexibility** - Can be set via environment variable or tool parameter

## API Documentation

For more information about the PageSpeed Insights API:
- [PageSpeed Insights API Documentation](https://developers.google.com/speed/docs/insights/v5/get-started)
- [Google Cloud Console](https://console.cloud.google.com/) - Get API key

## Error Handling

The server handles various error cases:
- Invalid URLs
- Network timeouts
- API rate limiting (use API key for higher limits)
- Invalid parameters
- Server-side errors

## Rate Limits

- **Without API Key**: ~25 requests per day (usually sufficient for personal use)
- **With API Key**: Much higher rate limits (varies by Google Cloud project quota, typically thousands per day)

**Note**: For most users, the free tier without an API key is sufficient. Only get an API key if you need to make many requests.

## Notes

- The server uses `npm ci --production` for faster, reliable builds
- The compiled `dist/index.js` file is copied directly (no build step needed in Docker)
- The API key is optional but recommended for production use

