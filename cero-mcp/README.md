<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Cero MCP Server

MCP server wrapper for [Cero](https://github.com/glebarez/cero) — subdomain discovery via TLS certificate scraping.

## What is Cero?

Cero is a Go tool that discovers subdomains by connecting to hosts and extracting Subject Alternative Names (SANs) from their TLS certificates, then recursively probing the discovered names. It is particularly effective for enumerating the full subdomain surface of a target without relying on DNS brute-forcing or third-party certificate transparency logs. See [github.com/glebarez/cero](https://github.com/glebarez/cero) for full documentation.

**No API keys required** — Cero runs locally inside the Docker container.

**Tools:**
- `run_cero` — Run cero with CLI arguments (e.g. a hostname) to extract subdomains from TLS certificates.

## Tools Reference

### `run_cero`

Run cero with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "cero output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run cero against example.com to discover subdomains from TLS certificate SANs."
- "Use cero on mail.example.com and recursively enumerate all certificate-linked subdomains."
- "Run cero with concurrency flags against target.io and list all discovered hostnames."
- "Extract subdomains from TLS certificates on api.example.com using cero."
- "Use cero to find additional hostnames on the same certificate as www.example.com."
- "Run cero against a list of IPs to enumerate any virtual-hosted subdomains via their TLS certs."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/cero-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8396:8396 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8396 \
  hackerdogs/cero-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "cero-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/cero-mcp:latest"],
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
    "cero-mcp": {
      "url": "http://localhost:8396/mcp"
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
    "cero-mcp": {
      "url": "http://localhost:8485/cero-mcp/mcp",
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
| `MCP_PORT` | `8396` | HTTP port (only used with `streamable-http`) |
| `BIN` | `/usr/local/bin/cero` | Bin |

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
docker build -t hackerdogs/cero-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name cero-mcp-test -p 8396:8396 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/cero-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8396/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8396/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8396/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_cero","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop cero-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Cero CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint cero hackerdogs/cero-mcp:latest --help
```
