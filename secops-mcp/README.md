<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# SecOps MCP Server

MCP server wrapper for a multi-tool security operations runner — invoke nuclei, subfinder, naabu, httpx, nmap, sqlmap, and other whitelisted security CLI tools via subprocess from AI assistants.

## What is SecOps MCP Server?

SecOps MCP Server is a custom Python FastMCP server that exposes an allowlisted set of security CLI tools — including nuclei, subfinder, naabu, httpx, dnsx, katana, gau, waybackurls, ffuf, gobuster, nmap, amass, sqlmap, wfuzz, whatweb, and nikto — as MCP tools. Install the desired binaries into the image or mount them at runtime; the server discovers available tools on PATH and rejects any tool not in the allowlist.

**No API keys required** — all tools run locally inside the Docker container. Individual tools may require API keys of their own (e.g. nuclei templates update, Shodan for nmap NSE scripts).

**Tools:**
- `list_tools` — List which SecOps CLI tools are installed and available on PATH.
- `run_secops_tool` — Run a whitelisted security CLI tool by name with the given space-separated arguments.

## Tools Reference

### `list_tools`

List which SecOps CLI tools are installed and available on PATH.

### `run_secops_tool`

Run a whitelisted security CLI tool by name.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tool_name` | str | Yes | — | Name of the tool to run (e.g. `nuclei`, `nmap`) |
| `args` | str | Yes | — | Space-separated CLI arguments |
| `timeout_seconds` | int | No | `120` | Max execution time (10–600 seconds) |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all SecOps tools that are currently installed and available in the container."
- "Run nuclei against https://example.com using the CVE templates and report any findings."
- "Use subfinder to enumerate subdomains of target.com and return the full list."
- "Run naabu on 192.168.1.1 to scan the top 1000 ports and identify open services."
- "Execute httpx against a list of URLs to check which ones are alive and return their status codes."
- "Run nmap with service version detection (-sV) against 10.0.0.1 and parse the output."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/secops-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8379:8379 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8379 \
  hackerdogs/secops-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "secops-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/secops-mcp:latest"],
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
    "secops-mcp": {
      "url": "http://localhost:8379/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8379` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/secops-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name secops-mcp-test -p 8379:8379 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/secops-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8379/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8379/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8379/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_secops","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop secops-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Secops CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint secops hackerdogs/secops-mcp:latest --help
```
