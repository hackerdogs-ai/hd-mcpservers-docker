<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# OCR MCP Server

MCP server wrapper for [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — extract text from images and scanned PDFs using Tesseract with optional structured bounding-box output.

## What is Tesseract OCR?

Tesseract is an open-source optical character recognition engine originally developed by HP and now maintained by Google. This MCP server wraps Tesseract (via `pytesseract` and `pdf2image`) to expose two tools: extracting text from images (base64-encoded or file path) and extracting text from scanned PDFs by converting pages to images and running OCR. See [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) for full documentation.

**No API keys required** — OCR runs entirely locally inside the Docker container using Tesseract and Poppler.

**Tools:**
- `extract_text_from_image` — Extract text from an image using Tesseract. Accepts base64-encoded images or local file paths; outputs plain text or structured JSON with word bounding boxes and confidence scores.
- `extract_text_from_pdf` — Extract text from a scanned PDF by converting pages to images and running OCR. Accepts a file path or base64-encoded PDF.
- `ocr_info` — Return OCR server status and Tesseract version information.

## Tools Reference

### `extract_text_from_image`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_data` | str | Yes | — | Base64-encoded image or local file path |
| `language` | str | No | `eng` | Tesseract language code (e.g. `eng`, `spa`, `fra`, `deu`) |
| `output_format` | str | No | `text` | `text` for plain string or `structured` for JSON with bounding boxes |

### `extract_text_from_pdf`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | str | Yes | — | Path to PDF file or base64-encoded PDF |
| `pages` | str | No | — | Comma-separated 1-based page numbers; empty for all pages |
| `language` | str | No | `eng` | Tesseract language code |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Extract all text from this base64-encoded screenshot of a terminal window."
- "OCR this scanned invoice PDF and return the text from page 1."
- "Run OCR on this image with Spanish language support (`spa`)."
- "Extract text from this image in structured mode so I get word positions and confidence scores."
- "OCR all pages of this scanned PDF and combine the output into a single document."
- "What version of Tesseract is installed in the OCR MCP server?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/ocr-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8438:8438 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8438 \
  hackerdogs/ocr-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "ocr-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/ocr-mcp:latest"],
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
    "ocr-mcp": {
      "url": "http://localhost:8438/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `streamable-http` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8438` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/ocr-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name ocr-mcp-test -p 8438:8438 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/ocr-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8438/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8438/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8438/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"ocr_info","arguments":{}}}'
```

**4. Clean up:**

```bash
docker stop ocr-mcp-test
```

## Running the tool directly (bypassing MCP)

You can inspect the OCR server in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint tesseract hackerdogs/ocr-mcp:latest --help
```
