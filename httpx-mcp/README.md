<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Httpx MCP Server

MCP server wrapper for [httpx](https://github.com/projectdiscovery/httpx) — fast multi-purpose HTTP probing toolkit from ProjectDiscovery.

## What is Httpx?

httpx is a fast and feature-rich HTTP toolkit from ProjectDiscovery that probes lists of hosts/URLs for live web servers and extracts detailed HTTP response metadata including status codes, content length, page titles, web technologies (via Wappalyzer), TLS certificate details, response hashes, and CDN information. It is widely used in bug bounty recon and penetration testing to quickly filter large lists of discovered hosts down to live HTTP services. See [projectdiscovery/httpx](https://github.com/projectdiscovery/httpx) for full documentation.

**No API keys required** — httpx runs locally inside the Docker container.

**Tools:**
- `run_httpx` — Run httpx with CLI arguments (e.g. example.com).

## Tools Reference

### `run_httpx`

Run httpx with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "httpx output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use httpx to probe a list of subdomains and identify which ones are serving live HTTP/HTTPS."
- "Run httpx against example.com and extract the page title, status code, and content length."
- "Probe 192.168.1.0/24 on ports 80 and 443 with httpx and report active web servers."
- "Use httpx with -tech-detect to fingerprint the web technology stack of https://example.com."
- "Run httpx on these 500 URLs from our recon output and filter for only 200 OK responses."
- "Use httpx to extract TLS certificate information from all HTTPS endpoints in this host list."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/httpx-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8386:8386 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8386 \
  hackerdogs/httpx-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "httpx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/httpx-mcp:latest"],
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
    "httpx-mcp": {
      "url": "http://localhost:8386/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8386` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/httpx-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name httpx-mcp-test -p 8386:8386 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/httpx-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8386/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8386/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8386/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_httpx","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop httpx-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Httpx CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint httpx hackerdogs/httpx-mcp:latest --help
```
