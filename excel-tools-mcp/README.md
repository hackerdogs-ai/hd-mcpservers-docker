<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Excel Tools MCP Server

MCP server wrapper for [Excel Tools](https://pypi.org/project/openpyxl/) — read, write, and analyze Excel and CSV spreadsheets using openpyxl and pandas.

## What is Excel Tools?

Excel Tools is a Python-based MCP server that lets AI assistants read `.xlsx`/`.xls` workbooks and CSV files, compute summary statistics, list sheet names, and write data back to CSV — all without leaving the chat. It uses [openpyxl](https://openpyxl.readthedocs.io/) for workbook access and [pandas](https://pandas.pydata.org/) for data manipulation and statistical analysis.

**No API keys required** — Excel Tools runs entirely inside the Docker container with no external service dependencies.

## Tools Reference


## Tools Reference

| Tool | Description |
|------|-------------|
| `read_excel` | Read an Excel file and return its contents as JSON. |
| `read_csv` | Read a CSV file and return its contents as JSON. |
| `describe_spreadsheet` | Get summary statistics for a spreadsheet (Excel or CSV). |
| `list_sheets` | List all sheet names in an Excel workbook. |
| `write_csv` | Write data to a CSV file. |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Read the first 50 rows of /data/sales.xlsx and summarize the columns."
- "List all sheet names in /reports/quarterly.xlsx."
- "Describe the statistics (mean, std, null counts) for every column in /data/metrics.csv."
- "Read /exports/users.csv with a semicolon delimiter and return it as JSON."
- "Write this JSON array of records to /output/results.csv with columns in the order: name, score, date."
- "Read the 'Revenue' sheet from /finance/budget.xlsx and tell me the top 10 rows by amount."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/excel-tools-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8505:8505 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8505 \
  hackerdogs/excel-tools-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "excel-tools-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/excel-tools-mcp:latest"],
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
    "excel-tools-mcp": {
      "url": "http://localhost:8505/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8505` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/excel-tools-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name excel-tools-mcp-test -p 8505:8505 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/excel-tools-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8505/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8505/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8505/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_excel_tools","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop excel-tools-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Excel Tools CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint excel-tools hackerdogs/excel-tools-mcp:latest --help
```
