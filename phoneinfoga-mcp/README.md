<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# PhoneInfoga MCP Server

MCP server wrapper for [PhoneInfoga](https://github.com/sundowndev/phoneinfoga) — phone number OSINT via local, Numverify, Google Search, and OVH scanners.

## What is PhoneInfoga?

PhoneInfoga is an advanced OSINT tool for scanning and gathering information about phone numbers worldwide. It supports multiple scanning backends — local format validation, Numverify API, Google CSE/search scraping, and OVH carrier lookup — and returns carrier, country, line type, and online footprint data. See [sundowndev/phoneinfoga](https://github.com/sundowndev/phoneinfoga) for full documentation.

**API keys optional** — the `local` scanner runs without any keys; `numverify` requires a Numverify API key, and `googlecse` requires a Google API key and Custom Search Engine ID.

**Tools:**
- `phoneinfoga_scan` — Run PhoneInfoga scan on a phone number using one or more scanners.
- `run_phoneinfoga` — Run phoneinfoga with arbitrary CLI arguments.

## Tools Reference

### `phoneinfoga_scan`

Run PhoneInfoga scan on a phone number.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `phone_number` | str | Yes | — | Phone number to investigate (include country code, e.g. `+1234567890`) |
| `scanners` | Optional[str] | No | `None` | Comma-separated scanner names: `local,numverify,googlesearch,googlecse,ovh` (empty = all) |
| `timeout_seconds` | int | No | `120` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "phoneinfoga output will appear here"
}
```

</details>

### `run_phoneinfoga`

Run phoneinfoga with arbitrary CLI arguments.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | str | Yes | — | Command-line arguments (e.g. `"scan -n +1234567890 -D googlesearch"`) |
| `timeout_seconds` | int | No | `120` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{
  "raw": "phoneinfoga output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Scan the phone number +14155552671 using PhoneInfoga and tell me the carrier and country."
- "Run a local and numverify scan on +442071234567 to determine line type and validity."
- "Use the googlesearch scanner to find online mentions of +33123456789."
- "Scan +81312345678 with all available PhoneInfoga scanners and summarize the findings."
- "Check if +15005550006 is a valid number and what carrier it belongs to."
- "Run PhoneInfoga with the OVH scanner only on +34911234567 to get carrier information."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/phoneinfoga-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8503:8503 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8503 \
  hackerdogs/phoneinfoga-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "phoneinfoga-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/phoneinfoga-mcp:latest"],
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
    "phoneinfoga-mcp": {
      "url": "http://localhost:8503/mcp"
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
    "phoneinfoga-mcp": {
      "url": "http://localhost:8485/phoneinfoga-mcp/mcp",
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
| `MCP_PORT` | `8503` | HTTP port (only used with `streamable-http`) |
| `NUMVERIFY_API_KEY` | — | Numverify API key for the `numverify` scanner |
| `GOOGLE_API_KEY` | — | Google API key for the `googlecse` scanner |
| `GOOGLECSE_CX` | — | Google Custom Search Engine ID for the `googlecse` scanner |

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
docker build -t hackerdogs/phoneinfoga-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name phoneinfoga-mcp-test -p 8503:8503 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/phoneinfoga-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8503/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8503/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8503/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"phoneinfoga_scan","arguments":{"phone_number":"+12025550123","scanners":"local"}}}'
```

**4. Clean up:**

```bash
docker stop phoneinfoga-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the PhoneInfoga CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint phoneinfoga hackerdogs/phoneinfoga-mcp:latest --help
```
