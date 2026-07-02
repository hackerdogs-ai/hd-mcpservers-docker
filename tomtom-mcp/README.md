<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# TomTom MCP Server

MCP server wrapper for [TomTom](https://github.com/tomtom-org/tomtom-mcp) — geocoding, routing, traffic, and point-of-interest search via TomTom's mapping APIs.

## What is TomTom?

TomTom provides global mapping, navigation, and traffic data APIs used in automotive, fleet management, and location-based services. This MCP server wraps TomTom's official MCP integration, enabling AI assistants to geocode addresses, calculate driving and walking routes, retrieve real-time traffic conditions, and search for nearby points of interest. See [tomtom-org/tomtom-mcp](https://github.com/tomtom-org/tomtom-mcp) for full documentation.

**API key required** — sign up at [developer.tomtom.com](https://developer.tomtom.com/) to get a `TOMTOM_API_KEY`.

**Summary.** MCP server wrapper for [TomTom](https://github.com/tomtom-org/tomtom-mcp) — geocoding, routing, traffic, and point-of-interest search via TomTom's mapping APIs.

## Tools Reference

| Tool | Description |
|------|-------------|
| `tomtom-geocode` | Tomtom Geocode |
| `tomtom-reverse-geocode` | Tomtom Reverse Geocode |
| `tomtom-fuzzy-search` | Tomtom Fuzzy Search |
| `tomtom-poi-search` | Tomtom Poi Search |
| `tomtom-nearby` | Tomtom Nearby |
| `tomtom-routing` | Tomtom Routing |
| `tomtom-waypoint-routing` | Tomtom Waypoint Routing |
| `tomtom-reachable-range` | Tomtom Reachable Range |
| `tomtom-traffic` | Tomtom Traffic |
| `tomtom-static-map` | Tomtom Static Map |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Calculate a driving route from New York to Boston and show the estimated travel time with current traffic."
- "Geocode the address '1600 Amphitheatre Parkway, Mountain View, CA' and return its coordinates."
- "Find all coffee shops within 500 meters of 48.8566° N, 2.3522° E (Paris city center)."
- "Reverse geocode coordinates 51.5074, -0.1278 to get the street address."
- "Show current traffic conditions on the M25 motorway near London."
- "Calculate the fastest walking route from the Eiffel Tower to the Louvre Museum."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e TOMTOM_API_KEY \
  hackerdogs/tomtom-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8671:8671 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8671 \
  -e TOMTOM_API_KEY \
  hackerdogs/tomtom-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "tomtom-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "TOMTOM_API_KEY",
        "hackerdogs/tomtom-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "TOMTOM_API_KEY": ""
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
    "tomtom-mcp": {
      "url": "http://localhost:8671/mcp"
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
    "tomtom-mcp": {
      "url": "http://localhost:8485/tomtom-mcp/mcp",
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
| `MCP_PORT` | `8671` | HTTP port (only used with `streamable-http`) |
| `TOMTOM_API_KEY` | — | TomTom API key — get one at [developer.tomtom.com](https://developer.tomtom.com/) |

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
docker build -t hackerdogs/tomtom-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name tomtom-mcp-test -p 8671:8671 \
  -e MCP_TRANSPORT=streamable-http \
  -e TOMTOM_API_KEY \
  hackerdogs/tomtom-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8671/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8671/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8671/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop tomtom-mcp-test
```
