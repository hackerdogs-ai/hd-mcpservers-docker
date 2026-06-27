<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# OpenStreetMap MCP Server

MCP server wrapper for [OpenStreetMap](https://github.com/nicholasgasior/osm-mcp-server) — geographic search and POI lookup via the OpenStreetMap Nominatim and Overpass APIs.

## What is OpenStreetMap?

OpenStreetMap MCP Server provides AI assistants with access to [OpenStreetMap](https://www.openstreetmap.org/) geographic data, enabling location searches, points-of-interest discovery, reverse geocoding, and spatial queries using the community-maintained open map dataset. It queries the Nominatim geocoding API and Overpass API without any proprietary dependencies. See [nicholasgasior/osm-mcp-server](https://github.com/nicholasgasior/osm-mcp-server) for full documentation.

**No API keys required** — this server calls public OpenStreetMap APIs and runs out of the box.

**Summary.** OpenStreetMap MCP Server — Dockerized from upstream `osm-mcp-server` package.

## Tools Reference

| Tool | Description |
|------|-------------|
| `geocode_address` | Geocode Address |
| `reverse_geocode` | Reverse Geocode |
| `find_nearby_places` | Find Nearby Places |
| `get_route_directions` | Get Route Directions |
| `search_category` | Search Category |
| `suggest_meeting_point` | Suggest Meeting Point |
| `explore_area` | Explore Area |
| `find_schools_nearby` | Find Schools Nearby |
| `analyze_commute` | Analyze Commute |
| `find_ev_charging_stations` | Find Ev Charging Stations |
| `analyze_neighborhood` | Analyze Neighborhood |
| `find_parking_facilities` | Find Parking Facilities |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Find all coffee shops within 500 meters of Times Square, New York."
- "Reverse geocode the coordinates 48.8584, 2.2945 and tell me what is at that location."
- "Search OpenStreetMap for hospitals in central Berlin and return their addresses."
- "Find the nearest pharmacy to 221B Baker Street, London."
- "List all parks and green spaces inside a bounding box covering downtown Tokyo."
- "Get the OpenStreetMap node ID and tags for the Eiffel Tower."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/osm-mcp-server-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8656:8656 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8656 \
  hackerdogs/osm-mcp-server-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "osm-mcp-server-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/osm-mcp-server-mcp:latest"
      ],
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
    "osm-mcp-server-mcp": {
      "url": "http://localhost:8656/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8656` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/osm-mcp-server-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name osm-mcp-server-mcp-test -p 8656:8656 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/osm-mcp-server-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8656/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8656/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8656/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop osm-mcp-server-mcp-test
```
