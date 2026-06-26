<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# VariFlight MCP Server

MCP server wrapper for [VariFlight](https://github.com/AirSavvy/variflight-mcp) — real-time flight tracking, historical flight data, and airport/airline information via VariFlight's aviation API.

## What is VariFlight?

VariFlight is a Chinese aviation data platform providing comprehensive flight intelligence covering global commercial flights, with strong coverage of Asian routes. This MCP server wraps the VariFlight API, giving AI assistants the ability to track live flight positions, retrieve departure and arrival information for airports, look up historical flight records, and query airline schedules. See [AirSavvy/variflight-mcp](https://github.com/AirSavvy/variflight-mcp) for full documentation.

**API key required** — sign up at [variflight.com](https://www.variflight.com/) and set `VARIFLIGHT_API_KEY`.

**Summary.** MCP server wrapper for [VariFlight](https://github.com/AirSavvy/variflight-mcp) — real-time flight tracking, historical flight data, and airport/airline information via VariFlight's aviation API.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Track the real-time status and position of flight CA981."
- "Show all departure flights from Beijing Capital Airport (PEK) for today."
- "What is the current arrival status of flight MU5137?"
- "Retrieve historical flight data for Air China flight CA1234 on 2024-11-15."
- "List all flights scheduled between Shanghai Pudong (PVG) and Tokyo Narita (NRT) tomorrow."
- "What is the typical on-time performance rate for flights operated by China Eastern Airlines?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e VARIFLIGHT_API_KEY \
  hackerdogs/variflight-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8672:8672 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8672 \
  -e VARIFLIGHT_API_KEY \
  hackerdogs/variflight-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "variflight-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "VARIFLIGHT_API_KEY",
        "hackerdogs/variflight-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "VARIFLIGHT_API_KEY": ""
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
    "variflight-mcp": {
      "url": "http://localhost:8672/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8672` | HTTP port (only used with `streamable-http`) |
| `VARIFLIGHT_API_KEY` | — | VariFlight API key |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/variflight-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name variflight-mcp-test -p 8672:8672 \
  -e MCP_TRANSPORT=streamable-http \
  -e VARIFLIGHT_API_KEY \
  hackerdogs/variflight-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8672/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8672/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8672/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop variflight-mcp-test
```
