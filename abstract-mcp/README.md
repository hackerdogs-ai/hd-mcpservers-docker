<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Abstract MCP Server

MCP server wrapper for [AbstractAPI](https://www.abstractapi.com/) — multi-endpoint data enrichment for phone, email, IP, IBAN, VAT, holidays, FX, company, and timezone lookups.

## What is AbstractAPI?

AbstractAPI is a collection of REST APIs that provide structured data enrichment across nine distinct domains: phone number intelligence, email reputation and deliverability, IP geolocation, IBAN validation, VAT number validation, public holidays by country, live foreign-exchange rates, company enrichment by domain, and current timezone lookups. See [abstractapi.com](https://www.abstractapi.com/) for full documentation. Each endpoint requires its own API key set via the corresponding environment variable.

**API keys required** — Each endpoint uses a separate key (e.g. `ABSTRACT_PHONE_API_KEY`, `ABSTRACT_EMAIL_API_KEY`, `ABSTRACT_IP_API_KEY`). Set only the keys for the endpoints you intend to use.

**Tools:**
- `abstract_phone_intelligence` — Look up carrier, line type, and validity for a phone number.
- `abstract_email_reputation` — Check deliverability, MX records, and disposable status for an email address.
- `abstract_ip_intelligence` — Retrieve geolocation, ASN, and threat flags for an IP address.
- `abstract_iban_validation` — Validate an IBAN and return bank and country metadata.
- `abstract_vat_validation` — Validate a European VAT number and return company name and address.
- `abstract_holidays` — Look up public holidays for a country on a given date.
- `abstract_exchange_rates` — Get live exchange rate between two currency codes.
- `abstract_company_enrichment` — Enrich company data (industry, employee count, location) by domain name.
- `abstract_timezone` — Get the current local time and UTC offset for any location string.

## Tools Reference

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Check the phone number +14155552671 for carrier and line type using AbstractAPI."
- "Is the email address user@tempmail.com deliverable and is it a disposable address?"
- "Look up geolocation and threat information for the IP address 8.8.8.8."
- "Validate the IBAN GB29NWBK60161331926819 and tell me which bank it belongs to."
- "What public holidays does Germany have on December 25, 2025?"
- "Get the current exchange rate from USD to EUR and from EUR to JPY."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/abstract-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8501:8501 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8501 \
  hackerdogs/abstract-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "abstract-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/abstract-mcp:latest"],
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
    "abstract-mcp": {
      "url": "http://localhost:8501/mcp"
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
    "abstract-mcp": {
      "url": "http://localhost:8485/abstract-mcp/mcp",
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
| `MCP_PORT` | `8501` | HTTP port (only used with `streamable-http`) |
| `ABSTRACT_TIMEZONE_API_KEY` | — | Abstract Timezone API Key (required) |
| `ABSTRACT_VAT_API_KEY` | — | Abstract Vat API Key (required) |
| `ABSTRACT_HOLIDAYS_API_KEY` | — | Abstract Holidays API Key (required) |
| `ABSTRACT_COMPANY_API_KEY` | — | Abstract Company API Key (required) |
| `ABSTRACT_EXCHANGE_API_KEY` | — | Abstract Exchange API Key (required) |
| `ABSTRACT_IBAN_API_KEY` | — | Abstract Iban API Key (required) |

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
docker build -t hackerdogs/abstract-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name abstract-mcp-test -p 8501:8501 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/abstract-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8501/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8501/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8501/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_abstract","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop abstract-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Abstract CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint abstract hackerdogs/abstract-mcp:latest --help
```
