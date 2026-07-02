<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# ExifTool Agent MCP Server

MCP server wrapper for [ExifTool](https://exiftool.org/) — extract and analyze metadata from images, video, audio, and document files via the `exiftool-mcp-ai-agent` npm package. See [nicholasgasior/exiftool-mcp-ai-agent](https://github.com/nicholasgasior/exiftool-mcp-ai-agent) for full documentation.

## What is ExifTool?

ExifTool is Phil Harvey's industry-standard metadata library and command-line application for reading, writing, and editing metadata in virtually any file format, including JPEG, RAW camera files, PDF, MP4, and MP3. This MCP agent wraps the `exiftool-mcp-ai-agent` npm package, which exposes ExifTool's capabilities to AI assistants so they can inspect camera settings, GPS coordinates, copyright tags, and hundreds of other metadata fields without leaving the chat.

**No API keys required** — runs entirely inside the Docker container using the bundled ExifTool binary.

## Tools Reference

| Tool | Description |
|------|-------------|
| `EXIF_all_or_some` | Exif All Or Some |
| `EXIF_location` | Exif Location |
| `EXIF_timestamp` | Exif Timestamp |
| `EXIF_location_and_timestamp` | Exif Location And Timestamp |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Extract all metadata from /photos/DSC_0042.jpg and tell me the camera model and lens used."
- "What GPS coordinates are embedded in /images/vacation.jpeg?"
- "Read the author, creator, and copyright tags from /docs/report.pdf."
- "Show me every XMP tag in /assets/hero.png."
- "Extract the creation date and duration from /videos/clip.mp4."
- "List all metadata tags for /audio/track.mp3 and identify the bit rate and sample rate."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/exiftool-agent-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8638:8638 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8638 \
  hackerdogs/exiftool-agent-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "exiftool-agent-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "hackerdogs/exiftool-agent-mcp:latest"
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
    "exiftool-agent-mcp": {
      "url": "http://localhost:8638/mcp"
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
    "exiftool-agent-mcp": {
      "url": "http://localhost:8485/exiftool-agent-mcp/mcp",
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
| `MCP_PORT` | `8638` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/exiftool-agent-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name exiftool-agent-mcp-test -p 8638:8638 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/exiftool-agent-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8638/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8638/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8638/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop exiftool-agent-mcp-test
```
