<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Acuvity Server Elevenlabs MCP Server

MCP server wrapper for [ElevenLabs](https://github.com/elevenlabs/elevenlabs-mcp) — AI-powered text-to-speech and audio generation via the ElevenLabs API.

## What is Acuvity Server Elevenlabs?

ElevenLabs MCP Server is the official ElevenLabs integration for Model Context Protocol, enabling AI assistants to synthesize high-quality speech, clone voices, and process audio through the ElevenLabs cloud API. It supports converting text to speech in dozens of voices and languages, as well as audio-to-audio transformations. See [elevenlabs/elevenlabs-mcp](https://github.com/elevenlabs/elevenlabs-mcp) for full documentation.

**API key required** — set `ELEVENLABS_API_KEY` to your ElevenLabs API key before starting the server.

**Tools:**
- `acuvity_mcp_server_elevenlabs_info` — Return basic info / status for Eleven Labs MCP Server.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use ElevenLabs to convert the following paragraph to speech in the Rachel voice and save it as audio."
- "Generate a voiceover for this product description using ElevenLabs with a professional male voice."
- "List all available ElevenLabs voices and their language support."
- "Convert this 500-word article to an MP3 podcast episode using ElevenLabs text-to-speech."
- "Use ElevenLabs to synthesize speech in Spanish using the multilingual v2 model."
- "Check my ElevenLabs account character quota and how many credits remain this month."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e ELEVENLABS_API_KEY=your_api_key_here \
  hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8417:8417 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8417 \
  -e ELEVENLABS_API_KEY=your_api_key_here \
  hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "acuvity-mcp-server-elevenlabs-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "ELEVENLABS_API_KEY", "hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "ELEVENLABS_API_KEY": "your_api_key_here"
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
    "acuvity-mcp-server-elevenlabs-mcp": {
      "url": "http://localhost:8417/mcp"
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
    "acuvity-mcp-server-elevenlabs-mcp": {
      "url": "http://localhost:8485/acuvity-mcp-server-elevenlabs-mcp/mcp",
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
| `MCP_PORT` | `8417` | HTTP port (only used with `streamable-http`) |
| `ELEVENLABS_API_KEY` | _(required)_ | Your ElevenLabs API key |

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
docker build -t hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name acuvity-mcp-server-elevenlabs-mcp-test -p 8417:8417 \
  -e MCP_TRANSPORT=streamable-http \
  -e ELEVENLABS_API_KEY=your_api_key_here \
  hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8417/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8417/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8417/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_acuvity_server_elevenlabs","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop acuvity-mcp-server-elevenlabs-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Acuvity Server Elevenlabs CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint acuvity-server-elevenlabs hackerdogs/acuvity-mcp-server-elevenlabs-mcp:latest --help
```
