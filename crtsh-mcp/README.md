<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Crtsh MCP Server

MCP server wrapper for [crt.sh](https://crt.sh) — discover subdomains and certificate history by querying the public SSL/TLS Certificate Transparency logs.

## What is crt.sh?

crt.sh is a public Certificate Transparency (CT) log search engine operated by Comodo/Sectigo. It indexes every publicly issued TLS certificate and lets security researchers enumerate subdomains, track certificate issuance, and audit wildcard coverage for any domain — all without touching the target. It requires no API key because it queries the public crt.sh web API.

**No API keys required** — queries the public crt.sh API over HTTPS.

**Tools:**
- `crtsh` — Query crt.sh to discover subdomains and SSL certificate history for a target domain.

## Tools Reference

### `crtsh`

Discover subdomains from SSL/TLS Certificate Transparency logs via crt.sh.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target` | str | Yes | — | Target domain (e.g. `example.com`) |

<details>
<summary>Example response</summary>

```json
{
  "raw": "crtsh output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use crt.sh to enumerate all subdomains for example.com from SSL certificate logs."
- "Find all TLS certificates ever issued for tesla.com and list unique subdomains."
- "Check crt.sh for wildcard certificates issued for *.target-domain.com."
- "Use crt.sh to discover internal subdomain names exposed through public certificate transparency logs."
- "Search crt.sh for recent certificate issuance for my domain to detect unauthorized certificates."
- "Enumerate subdomains of a target organization using certificate transparency logs as a passive reconnaissance step."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/crtsh-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8381:8381 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8381 \
  hackerdogs/crtsh-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "crtsh-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/crtsh-mcp:latest"],
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
    "crtsh-mcp": {
      "url": "http://localhost:8381/mcp"
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
    "crtsh-mcp": {
      "url": "http://localhost:8485/crtsh-mcp/mcp",
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
| `MCP_PORT` | `8381` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/crtsh-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name crtsh-mcp-test -p 8381:8381 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/crtsh-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8381/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8381/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8381/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"crtsh","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop crtsh-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Crtsh CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint crtsh hackerdogs/crtsh-mcp:latest --help
```
