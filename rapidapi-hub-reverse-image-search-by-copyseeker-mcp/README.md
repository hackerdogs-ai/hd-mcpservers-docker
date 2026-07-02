<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# RapidAPI Reverse Image Search MCP Server

MCP server wrapper for [CopySeeker Reverse Image Search](https://rapidapi.com/copyseeker/api/reverse-image-search-by-copyseeker) via RapidAPI — find image origins, detect copies, and discover visually similar content.

## What is RapidAPI Reverse Image Search?

CopySeeker's Reverse Image Search API, accessed via the RapidAPI Hub, lets you submit an image URL and receive a ranked list of matching or visually similar images found across the web, including their source URLs and metadata. It is useful for copyright detection, content moderation, and OSINT image tracing.

**API key required** — sign up at [rapidapi.com](https://rapidapi.com/) and subscribe to the CopySeeker Reverse Image Search API to obtain a `RAPIDAPI_KEY`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `rapidapi-reverse-image-search_health_check` | Rapidapi Reverse Image Search Health Check |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Reverse image search https://example.com/photo.jpg and show me where else this image appears online."
- "Find the original source of this product photo: https://cdn.shop.example.com/item.png."
- "Check whether the image at this URL has been copied to other websites without attribution."
- "Search for visually similar images to this logo and list the top 5 results with their source URLs."
- "Identify whether this screenshot of a face has been used elsewhere on the internet."
- "Run a reverse image search on this URL and report back any matches ranked by similarity score."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e RAPIDAPI_KEY \
  hackerdogs/rapidapi-hub-reverse-image-search-by-copyseeker-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8660:8660 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8660 \
  -e RAPIDAPI_KEY \
  hackerdogs/rapidapi-hub-reverse-image-search-by-copyseeker-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "RAPIDAPI_KEY",
        "hackerdogs/rapidapi-hub-reverse-image-search-by-copyseeker-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "RAPIDAPI_KEY": ""
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
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": {
      "url": "http://localhost:8660/mcp"
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
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": {
      "url": "http://localhost:8485/rapidapi-hub-reverse-image-search-by-copyseeker-mcp/mcp",
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
| `MCP_PORT` | `8660` | HTTP port (only used with `streamable-http`) |
| `RAPIDAPI_KEY` | — | RapidAPI key — sign up at [rapidapi.com](https://rapidapi.com/) |

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
docker build -t hackerdogs/rapidapi-hub-reverse-image-search-by-copyseeker-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name rapidapi-hub-reverse-image-search-by-copyseeker-mcp-test -p 8660:8660 \
  -e MCP_TRANSPORT=streamable-http \
  -e RAPIDAPI_KEY \
  hackerdogs/rapidapi-hub-reverse-image-search-by-copyseeker-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8660/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8660/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8660/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop rapidapi-hub-reverse-image-search-by-copyseeker-mcp-test
```
