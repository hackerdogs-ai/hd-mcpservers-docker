<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Whatsmyname MCP Server

MCP server wrapper for [WhatsMyName](https://github.com/WebBreacher/WhatsMyName) — OSINT username enumeration across hundreds of websites.

## What is Whatsmyname?

WhatsMyName is an open-source OSINT tool that checks whether a given username is registered on a large number of websites by querying the community-maintained [wmn-data.json](https://github.com/WebBreacher/WhatsMyName/blob/main/wmn-data.json) dataset. It sends HTTP requests to each site's profile URL and checks for a known presence string to confirm the account exists. See [WebBreacher/WhatsMyName](https://github.com/WebBreacher/WhatsMyName) for full documentation. No API keys are required — it runs locally and fetches the latest site list at runtime.

## Tools Reference

| Tool | Description |
|------|-------------|
| `whatsmyname_check` | Check if a username exists across up to `limit` sites from the WhatsMyName dataset |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use WhatsMyName to check if the username 'johndoe' appears on any social media or forum sites."
- "Search for the username 'hackerman42' across the first 100 sites in the WhatsMyName dataset."
- "Run a WhatsMyName lookup on 'target_user' and list every site where the account was found."
- "Check if 'alice_smith' has accounts registered across gaming, coding, or dating platforms."
- "Enumerate the username 'unknown_actor' and return all matches with their category and URL."
- "How many sites did WhatsMyName check when looking up 'example_user', and how many hits were found?"

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/whatsmyname-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8528:8528 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8528 \
  hackerdogs/whatsmyname-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "whatsmyname-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/whatsmyname-mcp:latest"],
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
    "whatsmyname-mcp": {
      "url": "http://localhost:8528/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8528` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/whatsmyname-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name whatsmyname-mcp-test -p 8528:8528 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/whatsmyname-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8528/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8528/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8528/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_whatsmyname","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop whatsmyname-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Whatsmyname CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint whatsmyname hackerdogs/whatsmyname-mcp:latest --help
```
