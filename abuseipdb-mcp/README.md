<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Abuseipdb MCP Server

MCP server wrapper for [AbuseIPDB](https://www.abuseipdb.com/) — community-powered IP reputation and abuse reporting database.

## What is AbuseIPDB?

AbuseIPDB is a public database where system administrators and security teams report IP addresses observed performing malicious activity (port scans, brute-force attacks, spam, DDoS, etc.). Each IP lookup returns an abuse confidence score (0–100%), total report count, country, ISP, usage type, and the timestamps of recent reports from within a configurable look-back window. See [abuseipdb.com](https://www.abuseipdb.com/) for full documentation. **API key required** — set `ABUSEIPDB_API_KEY` before running the container.

**Tools:**
- `check_ip` — Query AbuseIPDB for an IP address and return its abuse confidence score, report count, country, ISP, and recent activity over a configurable number of days (default 90, max 365).

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Check the AbuseIPDB reputation of 185.220.101.47 and tell me its abuse confidence score."
- "Is 45.33.32.156 in AbuseIPDB? How many reports has it received in the last 30 days?"
- "Look up 103.21.244.0 in AbuseIPDB and report the ISP, country, and usage type."
- "Check these five IP addresses in AbuseIPDB and flag any with a confidence score above 80%."
- "Query AbuseIPDB for 192.0.2.1 using a 7-day look-back window and summarize the findings."
- "My firewall blocked 222.186.30.0 — check AbuseIPDB to see if it is a known scanner."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/abuseipdb-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8374:8374 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8374 \
  hackerdogs/abuseipdb-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "abuseipdb-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/abuseipdb-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "abuseipdb-mcp": {
      "url": "http://localhost:8374/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.


## Securely Accessing MCP

When running through the [Hackerdogs MCP Farm](https://hackerdogs.ai), servers are accessed through the authenticated gateway instead of direct container ports:

```json
{
  "mcpServers": {
    "abuseipdb-mcp": {
      "url": "http://localhost:8485/abuseipdb-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

> **Farm access:** The MCP Farm gateway handles authentication, rate limiting, and routing. Replace `localhost:8485` with your farm's host address and use your API key from the farm admin panel. See [Hackerdogs](https://hackerdogs.ai) for details.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8374` | HTTP port (only used with `streamable-http`) |
| `ABUSEIPDB_API_KEY` | `` | Abuseipdb api key |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use naabu to scan example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/abuseipdb-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name abuseipdb-mcp-test -p 8374:8374 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/abuseipdb-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8374/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8374/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8374/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_abuseipdb","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop abuseipdb-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Abuseipdb CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint abuseipdb hackerdogs/abuseipdb-mcp:latest --help
```
