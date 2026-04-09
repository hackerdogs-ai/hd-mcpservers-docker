<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Abuse.ch MCP Server

MCP server for [Abuse.ch](https://abuse.ch) threat intelligence: **MalwareBazaar**, **URLhaus**, and **ThreatFox**.

**Requires:** `ABUSECH_API_KEY` (get a free key at [auth.abuse.ch](https://auth.abuse.ch)).

**Tools:**
- `urlhaus_host` — URLhaus host report for a hostname or IP
- `urlhaus_url` — URLhaus URL report
- `malwarebazaar_hash` — MalwareBazaar info for a SHA256 hash
- `threatfox_iocs` — Recent ThreatFox IOCs (days: 1–365)

## Deploy

### Docker Compose
```bash
docker-compose up -d
```
Set `ABUSECH_API_KEY` in the environment or a `.env` file.

### Docker Run (stdio)
```bash
docker run -i --rm -e ABUSECH_API_KEY=your_key hackerdogs/abusech-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8373:8373 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8373 \
  -e ABUSECH_API_KEY=your_key \
  hackerdogs/abusech-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`; set `ABUSECH_API_KEY` in `env`.  
**HTTP:** Connect to `http://localhost:8373` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8373` |
| `ABUSECH_API_KEY` | Abuse.ch API key | required |

## Example prompts

- "Check URLhaus for host example.com."
- "Get MalwareBazaar info for hash abc123..."
- "List recent ThreatFox IOCs for the last 7 days."
