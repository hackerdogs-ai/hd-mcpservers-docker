<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# AbuseIPDB MCP Server

MCP server for [AbuseIPDB](https://www.abuseipdb.com/) — IP reputation and abuse reporting checks.

**Requires:** `ABUSEIPDB_API_KEY` (free tier: 1000 requests/day).

**Tools:**
- `check_ip` — Check an IP address; returns abuse confidence score, country, ISP, total reports, etc.

## Deploy

### Docker Run (stdio)
```bash
docker run -i --rm -e ABUSEIPDB_API_KEY=your_key hackerdogs/abuseipdb-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8374:8374 \
  -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8374 \
  -e ABUSEIPDB_API_KEY=your_key \
  hackerdogs/abuseipdb-mcp:latest
```

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port | `8374` |
| `ABUSEIPDB_API_KEY` | AbuseIPDB API key | required |

## Example prompts

- "Check IP 8.8.8.8 on AbuseIPDB."
- "What is the abuse score for 1.2.3.4?"
