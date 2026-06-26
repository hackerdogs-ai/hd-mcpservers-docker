<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Webc MCP Server

MCP server wrapper for Webc — multi-tool web content and domain intelligence with 13 built-in analysis functions.

## What is Webc?

Webc is a custom web content analysis server providing webpage fetching and parsing, DNS/WHOIS/SSL lookups, IP geolocation, TCP port checking, email and entity extraction, sensitive data detection (credit cards, AWS keys, JWTs), language detection, and key-term extraction. It combines capabilities from httpx, dnspython, python-whois, BeautifulSoup, and langdetect into a single MCP interface. No external API keys are required — all tools run locally inside the container.

## Tools Reference

| Tool | Description |
|------|-------------|
| `analyze_webpage` | Fetch a URL and return title, meta tags, text preview, links, and images |
| `extract_text` | Extract clean readable text from a webpage (strips nav/scripts/styles) |
| `extract_emails` | Find email addresses in text or at a URL |
| `extract_entities` | Extract URLs, IPs, phone numbers, MD5/SHA256 hashes, and emails |
| `find_sensitive_data` | Detect credit cards, SSNs, AWS keys, JWTs, and private keys in text |
| `analyze_domain` | Combined DNS + WHOIS + TLD analysis for a domain |
| `resolve_dns` | Resolve A, AAAA, MX, NS, TXT records for a domain |
| `get_whois` | WHOIS registration data for a domain or IP |
| `get_ip_location` | GeoIP lookup (country, city, ASN) via ip-api.com |
| `get_ssl_certificate` | Retrieve TLS certificate subject, issuer, SAN, and expiry |
| `scan_port` | Check if a TCP port is open on a host |
| `detect_language` | Identify the language of a text passage |
| `extract_keyterms` | Top-N key terms by frequency from text |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use webc to analyze the webpage at https://example.com and extract all links and meta tags."
- "Extract all email addresses and IP addresses found on https://target.com/contact."
- "Run a WHOIS lookup and DNS resolution for suspicious-domain.io."
- "Check if port 8080 is open on 10.0.0.5 and retrieve its SSL certificate details."
- "Scan the text below for sensitive data like API keys, JWTs, or credit card numbers."
- "Detect the language of this paste and extract the top 20 key terms from it."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/webc-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8504:8504 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8504 \
  hackerdogs/webc-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "webc-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/webc-mcp:latest"],
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
    "webc-mcp": {
      "url": "http://localhost:8504/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8504` | HTTP port (only used with `streamable-http`) |

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
docker build -t hackerdogs/webc-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name webc-mcp-test -p 8504:8504 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/webc-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8504/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8504/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8504/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_webc","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop webc-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Webc CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint webc hackerdogs/webc-mcp:latest --help
```
