<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Notion MCP Server

MCP server wrapper for [Notion](https://github.com/notionhq/notion-mcp-server) — upstream package `@notionhq/notion-mcp-server`.

## What is Notion?

This MCP server connects AI assistants to your [Notion](https://notion.so/) workspace, enabling them to search pages, read and create content, manage databases, and update blocks through the Notion API. It is the official Notion MCP server published by Notionhq. See [notionhq/notion-mcp-server](https://github.com/notionhq/notion-mcp-server) for full documentation.

**Integration token required** — create a Notion integration and get your token at [notion.so/my-integrations](https://www.notion.so/my-integrations). Share the pages or databases you want to access with the integration.

**Summary.** Notion MCP Server — Dockerized from upstream `@notionhq/notion-mcp-server` package.

## Tools Reference

| Tool | Description |
|------|-------------|
| `API-get-user` | Api Get User |
| `API-get-users` | Api Get Users |
| `API-get-self` | Api Get Self |
| `API-post-search` | Api Post Search |
| `API-get-block-children` | Api Get Block Children |
| `API-patch-block-children` | Api Patch Block Children |
| `API-retrieve-a-block` | Api Retrieve A Block |
| `API-update-a-block` | Api Update A Block |
| `API-delete-a-block` | Api Delete A Block |
| `API-retrieve-a-page` | Api Retrieve A Page |
| `API-patch-page` | Api Patch Page |
| `API-post-page` | Api Post Page |
| `API-retrieve-a-page-property` | Api Retrieve A Page Property |
| `API-retrieve-a-comment` | Api Retrieve A Comment |
| `API-create-a-comment` | Api Create A Comment |
| `API-query-data-source` | Api Query Data Source |
| `API-retrieve-a-data-source` | Api Retrieve A Data Source |
| `API-update-a-data-source` | Api Update A Data Source |
| `API-create-a-data-source` | Api Create A Data Source |
| `API-list-data-source-templates` | Api List Data Source Templates |
| `API-retrieve-a-database` | Api Retrieve A Database |
| `API-move-page` | Api Move Page |
| `API-retrieve-page-markdown` | Api Retrieve Page Markdown |
| `API-update-page-markdown` | Api Update Page Markdown |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Search my Notion workspace for all pages related to 'Q3 roadmap'."
- "Create a new page in my Engineering database titled 'API Rate Limiting Design'."
- "Read the contents of my 'Meeting Notes' Notion page from last Monday."
- "Add a new row to my Notion task tracker database with status 'In Progress'."
- "List all pages in my 'Projects' database that have the tag 'security'."
- "Update the 'Status' property of the 'Deploy to Production' task to 'Done'."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e OPENAI_API_KEY \
  -e NOTION_TOKEN \
  hackerdogs/notion-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8652:8652 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8652 \
  -e OPENAI_API_KEY \
  -e NOTION_TOKEN \
  hackerdogs/notion-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "notion-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "OPENAI_API_KEY",
        "-e",
        "NOTION_TOKEN",
        "hackerdogs/notion-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "OPENAI_API_KEY": "",
        "NOTION_TOKEN": ""
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
    "notion-mcp": {
      "url": "http://localhost:8652/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8652` | HTTP port (only used with `streamable-http`) |
| `OPENAI_API_KEY` | — | OpenAI API key (used for AI features) |
| `NOTION_TOKEN` | — | Notion integration token — create at [notion.so/my-integrations](https://www.notion.so/my-integrations) |
| `NOTION_API_KEY` | — | Notion API key (required) |

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
docker build -t hackerdogs/notion-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name notion-mcp-test -p 8652:8652 \
  -e MCP_TRANSPORT=streamable-http \
  -e OPENAI_API_KEY \
  -e NOTION_TOKEN \
  hackerdogs/notion-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8652/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8652/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8652/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop notion-mcp-test
```
