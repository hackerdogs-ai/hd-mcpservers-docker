<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Nmap MCP Server

MCP server wrapper for [Nmap](https://nmap.org/) — network discovery, port scanning, service/version detection, and OS fingerprinting.

## What is Nmap?

Nmap is the industry-standard open-source network scanner for host discovery, port scanning, service and version detection, and OS fingerprinting across TCP/UDP. It supports NSE (Nmap Scripting Engine) scripts for vulnerability detection, banner grabbing, brute-force checks, and more. See [nmap.org](https://nmap.org/) for full documentation.

**No API keys required** — Nmap runs locally inside the Docker container.

**Tools:**
- `run_nmap` — Run nmap with CLI arguments and return the scan output.

## Tools Reference

### `run_nmap`

Run nmap with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"-sV -p 80,443 example.com"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "nmap output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use nmap to do a SYN scan of 192.168.1.0/24 and detect service versions on open ports."
- "Scan example.com for the top 1000 ports and identify the operating system."
- "Run an nmap script scan using the `vuln` category against 10.0.0.1."
- "Do a UDP scan of the top 100 ports on 192.168.1.100 and report which services respond."
- "Use nmap to detect the TLS certificate details on port 443 of target.example.com."
- "Run nmap with `-sC -sV` on 10.10.0.5 and summarize all open ports and their services."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/nmap-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8390:8390 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8390 \
  hackerdogs/nmap-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "nmap-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/nmap-mcp:latest"],
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
    "nmap-mcp": {
      "url": "http://localhost:8390/mcp"
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
    "nmap-mcp": {
      "url": "http://localhost:8485/nmap-mcp/mcp",
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
| `MCP_PORT` | `8390` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/nmap-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name nmap-mcp-test -p 8390:8390 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/nmap-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8390/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8390/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8390/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_nmap","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop nmap-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Nmap CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint nmap hackerdogs/nmap-mcp:latest --help
```
