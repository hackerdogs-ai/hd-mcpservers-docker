<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# MITRE ATT&CK Remote MCP Server

MCP server wrapper for [MITRE ATT&CK](https://attack.mitre.org/) — local compliance stub that surfaces the official remote MCP endpoint at `https://attack-mcp.mitre.org/mcp`.

## What is MITRE ATT&CK?

MITRE ATT&CK is the industry-standard knowledge base of adversary tactics, techniques, and procedures (TTPs) used by real-world threat actors across enterprise, mobile, and ICS environments. This container acts as a local compliance shim — it registers with your MCP client and returns the official MITRE remote MCP URL (`https://attack-mcp.mitre.org/mcp`) so you can query ATT&CK techniques, mitigations, and threat group mappings directly through that hosted service.

**No API keys required** — the local stub runs without credentials; the upstream production endpoint at `attack-mcp.mitre.org` also requires no API key.

**Tools:**
- `remote_endpoint_info` — Return the official MITRE ATT&CK remote MCP URL and usage notes.

## Tools Reference

### `remote_endpoint_info`

Return the official remote MCP URL and notes for this integration.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "What is the remote MCP endpoint for MITRE ATT&CK and how do I connect to it?"
- "Look up ATT&CK technique T1059 (Command and Scripting Interpreter) and list its sub-techniques."
- "Which threat groups use the Spearphishing Attachment technique (T1566.001)?"
- "List all ATT&CK mitigations that apply to credential dumping (T1003)."
- "Find ATT&CK techniques associated with the APT29 threat actor group."
- "What detection opportunities does MITRE ATT&CK recommend for living-off-the-land binaries?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/mitre-attack-remote-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8516:8516 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8516 \
  hackerdogs/mitre-attack-remote-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "mitre-attack-remote-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/mitre-attack-remote-mcp:latest"],
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
    "mitre-attack-remote-mcp": {
      "url": "http://localhost:8516/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8516` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/mitre-attack-remote-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name mitre-attack-remote-mcp-test -p 8516:8516 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/mitre-attack-remote-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8516/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8516/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8516/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"remote_endpoint_info","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop mitre-attack-remote-mcp-test
```

## Running the tool directly (bypassing MCP)

You can inspect the server configuration in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/mitre-attack-remote-mcp:latest mcp_server.py --help
```
