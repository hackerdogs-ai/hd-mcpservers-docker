# phoneinfoga-mcp

MCP server for phone number OSINT using PhoneInfoga.

## Tools

| Tool | Description |
|------|------------|
| phoneinfoga_scan | Structured phone scan with scanner selection |
| run_phoneinfoga | Raw CLI access to phoneinfoga |

## Scanners

- **local**: Basic phone number validation and formatting
- **numverify**: Carrier, location, line type (requires NUMVERIFY_API_KEY)
- **googlesearch**: Google dork search for phone number
- **googlecse**: Google Custom Search (requires GOOGLE_API_KEY + GOOGLECSE_CX)
- **ovh**: OVH telecom lookup

## Quick Start

```bash
docker build -t phoneinfoga-mcp .
docker run -p 8503:8503 -e MCP_TRANSPORT=streamable-http phoneinfoga-mcp
```
