<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Exiftool MCP Server

MCP server wrapper for [ExifTool](https://exiftool.org/) — extract metadata from images, PDFs, video, and audio files via a custom FastMCP server backed by the `exiftool` system binary.

## What is Exiftool?

ExifTool is Phil Harvey's widely-used command-line tool for reading metadata from virtually any file format, covering EXIF camera data, GPS location, IPTC copyright tags, XMP properties, and hundreds of vendor-specific fields. This server wraps the system `exiftool` binary installed in the Docker image and exposes a single `exiftool_extract` tool that accepts a local file path or an HTTP(S) URL, downloading the file automatically when a URL is provided.

**No API keys required** — ExifTool runs locally inside the Docker container with the binary installed via `apt`.

## Tools Reference

### `exiftool_extract`

Extract metadata from an image, PDF, or document file.

    Args:
        file_path: Local file path or http(s) URL.
        extract_gps: Include GPS tags (default True).
        extract_author: Include author/creator tags (default True).
        output_format: 'json' (default) or 'text'.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | str | Yes | — | File path |
| `extract_gps` | bool | No | `True` | Extract gps |
| `extract_author` | bool | No | `True` | Extract author |
| `output_format` | str | No | `"json"` | Output format |

<details>
<summary>Example response</summary>

```json
{
  "raw": "exiftool output will appear here"
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Extract all metadata from /photos/IMG_4521.jpg and tell me the camera model, exposure time, and aperture."
- "What GPS coordinates are embedded in the image at https://example.com/photo.jpg?"
- "Read the author and creator metadata from /docs/contract.pdf, excluding GPS tags."
- "Extract metadata from /video/clip.mov in plain text format."
- "Show me all XMP and IPTC tags in /assets/hero_image.png."
- "Check /downloads/suspicious.jpg for any embedded GPS location or author information."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/exiftool-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8502:8502 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8502 \
  hackerdogs/exiftool-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "exiftool-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/exiftool-mcp:latest"],
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
    "exiftool-mcp": {
      "url": "http://localhost:8502/mcp"
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
    "exiftool-mcp": {
      "url": "http://localhost:8485/exiftool-mcp/mcp",
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
| `MCP_PORT` | `8502` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/exiftool-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name exiftool-mcp-test -p 8502:8502 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/exiftool-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8502/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8502/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8502/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"exiftool_extract","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop exiftool-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Exiftool CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint exiftool hackerdogs/exiftool-mcp:latest --help
```
