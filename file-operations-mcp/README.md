<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# File Operations MCP Server

MCP server wrapper for File Operations — convert files between CSV, JSON, and Excel formats and inspect file metadata.

## What is File Operations?

File Operations is a Python MCP server that provides lightweight file format conversion and inspection tools backed by pandas. It can convert a CSV to a JSON array of records, convert a JSON array back to a CSV, or retrieve size and modification timestamp for any file on the local filesystem. It is designed for quick data-interchange tasks where the AI needs to reformat structured data without writing ad-hoc code.

**No API keys required** — File Operations runs entirely inside the Docker container with no external service dependencies.

## Tools Reference


## Tools Reference

| Tool | Description |
|------|-------------|
| `convert_csv_to_json` | Convert CSV file to JSON. |
| `convert_json_to_csv` | Convert JSON file to CSV. |
| `file_info` | Get file information (size, type, modification time). |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Convert /data/export.csv to JSON and show me the first 5 records."
- "Convert /data/users.json to a CSV file at /output/users.csv."
- "Get the file size and last-modified time for /uploads/report.xlsx."
- "Take the JSON array I just gave you, write it to /tmp/output.csv, then confirm the row count."
- "Convert /logs/events.csv to JSON so I can process it as structured data."
- "Check whether /data/input.csv exists and how large it is before converting it."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/file-operations-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8522:8522 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8522 \
  hackerdogs/file-operations-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "file-operations-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/file-operations-mcp:latest"],
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
    "file-operations-mcp": {
      "url": "http://localhost:8522/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8522` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/file-operations-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name file-operations-mcp-test -p 8522:8522 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/file-operations-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8522/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8522/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8522/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_file_operations","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop file-operations-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the File Operations CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint file-operations hackerdogs/file-operations-mcp:latest --help
```
