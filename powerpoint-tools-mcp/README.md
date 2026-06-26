<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# PowerPoint Tools MCP Server

MCP server wrapper for PowerPoint Tools — create, read, and inspect PPTX presentations using python-pptx.

## What is PowerPoint Tools?

PowerPoint Tools MCP Server provides AI assistants with the ability to programmatically create, read, and inspect Microsoft PowerPoint (.pptx) files using the `python-pptx` library. It supports building multi-slide decks from structured JSON definitions with title, content, and layout options, as well as extracting all text content and structural metadata from existing presentations — all running locally inside the Docker container.

**No API keys required** — PowerPoint Tools runs entirely locally inside the Docker container.

**Tools:**
- `create_presentation` — Create a PowerPoint presentation from JSON slide definitions.
- `read_presentation` — Read a PPTX file and extract text from all slides.
- `get_presentation_info` — Get metadata and structure info about a PowerPoint file.

## Tools Reference

### `create_presentation`

Create a PowerPoint presentation from JSON slide definitions.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `slides_json` | string | Yes | — | JSON array of slide objects: `[{"title": "...", "content": "...", "layout": "title_and_content"}]`. Layouts: `title`, `title_and_content`, `section_header`, `blank` |
| `output_path` | string | Yes | — | Output `.pptx` file path |
| `title` | string | No | — | Optional presentation title for the first slide |

### `read_presentation`

Read a PowerPoint file and extract text from all slides.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | string | Yes | — | Path to `.pptx` file |

### `get_presentation_info`

Get metadata and structure info about a PowerPoint file.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | string | Yes | — | Path to `.pptx` file |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Create a 5-slide PowerPoint presentation about cloud security best practices and save it to /tmp/security.pptx."
- "Read the text from all slides in /data/quarterly-report.pptx and summarize the key points."
- "Build a PPTX presentation with a title slide and 3 content slides from this outline: [outline text]."
- "Inspect the structure of /data/proposal.pptx — how many slides are there and what shapes does each slide contain?"
- "Create a section-header slide followed by three bullet-point slides for a product demo deck."
- "Extract all text from /tmp/conference-talk.pptx and generate speaker notes for each slide."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/powerpoint-tools-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8507:8507 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8507 \
  hackerdogs/powerpoint-tools-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "powerpoint-tools-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/powerpoint-tools-mcp:latest"],
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
    "powerpoint-tools-mcp": {
      "url": "http://localhost:8507/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8507` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/powerpoint-tools-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name powerpoint-tools-mcp-test -p 8507:8507 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/powerpoint-tools-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8507/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8507/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8507/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_presentation","arguments":{"slides_json":"[{\"title\":\"Hello World\",\"content\":\"First slide content\",\"layout\":\"title_and_content\"}]","output_path":"/tmp/test.pptx"}}}'
```

**4. Clean up:**

```bash
docker stop powerpoint-tools-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the PowerPoint Tools MCP server in the same container by overriding the entrypoint without starting the MCP wrapper.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/powerpoint-tools-mcp:latest mcp_server.py --help
```
