<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Earthquake MCP Server

MCP server wrapper for [USGS Earthquake Hazards Program](https://earthquake.usgs.gov) — query real-time and historical seismic event data from the USGS and IRIS networks.

## What is the Earthquake (USGS) MCP Server?

This MCP server integrates with the USGS Earthquake Hazards Program data feeds and the IRIS (Incorporated Research Institutions for Seismology) seismological data services. It enables AI assistants to query recent earthquake activity, filter by magnitude and region, retrieve waveform metadata, and access historical seismic records — all via the public USGS and IRIS APIs with no authentication needed.

**No API keys required** — queries the public USGS and IRIS data APIs.

**Tools:**
- `earthquake_info` — Return status information for the connected USGS MCP server.

## Tools Reference

### `earthquake_info`

Return basic status for the USGS Earthquake MCP server.

_No parameters._

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "List all earthquakes magnitude 5.0 or greater that occurred in the last 7 days worldwide."
- "Query USGS for seismic events near the Pacific Ring of Fire in the past 30 days."
- "What was the largest earthquake recorded in California in 2024?"
- "Retrieve real-time earthquake data for Japan and show magnitude, depth, and coordinates."
- "Use the USGS feed to find all significant earthquakes (M6+) since January 2025."
- "Look up historical seismic activity for a specific geographic region using IRIS data."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/earthquake-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8457:8457 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8457 \
  hackerdogs/earthquake-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "earthquake-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/earthquake-mcp:latest"],
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
    "earthquake-mcp": {
      "url": "http://localhost:8457/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8457` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/earthquake-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name earthquake-mcp-test -p 8457:8457 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/earthquake-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8457/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8457/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8457/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_earthquake","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop earthquake-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Earthquake CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint earthquake hackerdogs/earthquake-mcp:latest --help
```
