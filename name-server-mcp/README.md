<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Name Server MCP Server

MCP server wrapper for Name Server — identify whether a given IP address belongs to a known public DNS resolver (Google, Cloudflare, Quad9, OpenDNS, AdGuard).

## What is Name Server?

Name Server MCP Server provides a quick lookup to determine whether an IP address is a well-known public DNS resolver. It maintains a curated list of resolver IPs from major providers including Google (8.8.8.8, 8.8.4.4), Cloudflare (1.1.1.1, 1.0.0.1), Quad9, OpenDNS, and AdGuard, and returns the provider name when matched. This is useful for network reconnaissance, firewall auditing, and DNS traffic analysis.

**No API keys required** — Name Server runs locally inside the Docker container with no external API calls.

**Tools:**
- `nameserver_check_ip` — Check if an IP address is a known public DNS resolver and return the provider name.

## Tools Reference

### `nameserver_check_ip`

Check if an IP is a known public DNS resolver.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ip` | str | Yes | — | IP address to look up |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Is 8.8.8.8 a public DNS resolver? Who operates it?"
- "Check if 1.1.1.1 is a known public DNS resolver."
- "I see DNS traffic going to 9.9.9.9 — is that a legitimate public resolver?"
- "Is 208.67.222.222 associated with a public DNS provider?"
- "Check these IPs and tell me which ones are public DNS resolvers: 1.0.0.1, 94.140.14.14, 192.168.1.1."
- "Our firewall logs show DNS queries to 149.112.112.112 — what resolver is that?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/name-server-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8525:8525 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8525 \
  hackerdogs/name-server-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "name-server-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/name-server-mcp:latest"],
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
    "name-server-mcp": {
      "url": "http://localhost:8525/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8525` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/name-server-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name name-server-mcp-test -p 8525:8525 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/name-server-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8525/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8525/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8525/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"nameserver_check_ip","arguments":{"ip":"8.8.8.8"}}}'
```

**4. Clean up:**

```bash
docker stop name-server-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Name Server MCP server in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/name-server-mcp:latest mcp_server.py --help
```
