<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Masscan MCP Server

MCP server wrapper for [Masscan](https://github.com/robertdavidgraham/masscan) — the fastest TCP port scanner capable of scanning the entire internet in under six minutes.

## What is Masscan?

Masscan is an asynchronous TCP port scanner by Robert Graham that uses a custom networking stack to transmit and receive packets without relying on the OS TCP/IP stack, achieving scan rates of millions of packets per second. It is designed for large-scale Internet-wide or enterprise network scanning and produces output compatible with Nmap XML format. Unlike Nmap, it does not perform service/version detection but excels at rapidly identifying which hosts have specific ports open across enormous IP ranges. See [robertdavidgraham/masscan](https://github.com/robertdavidgraham/masscan) for full documentation.

**No API keys required** — Masscan runs locally inside the Docker container. Note: high-rate scanning may require elevated privileges or `--adapter-ip` configuration.

**Tools:**
- `run_masscan` — Run masscan with CLI arguments (e.g. example.com).

## Tools Reference

### `run_masscan`

Run masscan with CLI arguments (e.g. example.com).

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | int | No | `300` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "masscan output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use masscan to scan the 10.0.0.0/8 network for open port 443 at a rate of 10000 packets/sec."
- "Run masscan against 192.168.1.0/24 for ports 22, 80, 443, and 8080 and report all open ports found."
- "Scan the range 203.0.113.0/24 with masscan for common database ports (3306, 5432, 1433, 27017)."
- "Use masscan to check which hosts in 10.10.0.0/16 have port 3389 (RDP) open."
- "Run masscan with output in JSON format against 172.16.0.0/12 scanning for port 22 and 23."
- "Perform a masscan sweep of the DMZ network 192.168.100.0/24 for all ports 1-65535."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/masscan-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8388:8388 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8388 \
  hackerdogs/masscan-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "masscan-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/masscan-mcp:latest"],
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
    "masscan-mcp": {
      "url": "http://localhost:8388/mcp"
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
    "masscan-mcp": {
      "url": "http://localhost:8485/masscan-mcp/mcp",
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
| `MCP_PORT` | `8388` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/masscan-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name masscan-mcp-test -p 8388:8388 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/masscan-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8388/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8388/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8388/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_masscan","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop masscan-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Masscan CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint masscan hackerdogs/masscan-mcp:latest --help
```
