<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Google Threat Intelligence MCP Server

MCP server wrapper for [Google Threat Intelligence](https://cloud.google.com/threat-intelligence) (GTI) — query file hashes, URLs, domains, and IP addresses for malware verdicts, reputation scores, and Mandiant threat intelligence. See [google/mcp-security](https://github.com/google/mcp-security) for full documentation.

## What is Google Threat Intelligence?

Google Threat Intelligence MCP (`gti-mcp`) combines VirusTotal's crowdsourced malware scanning with Mandiant's enterprise threat research to give AI assistants a comprehensive view of any indicator of compromise. You can look up file hashes against 70+ antivirus engines, check whether a domain or IP is associated with known threat actors, retrieve behavioral sandbox reports for suspicious files, and search the GTI knowledge base for CVEs, malware families, and attack campaigns.

**API key required** — a VirusTotal API key (free or premium) is required; set `VIRUSTOTAL_API_KEY`. Premium GTI features require a Google Threat Intelligence subscription.

## Tools Reference

| Tool | Description |
|------|-------------|
| `get_collection_report` | Get Collection Report |
| `get_entities_related_to_a_collection` | Get Entities Related To A Collection |
| `search_threats` | Search Threats |
| `search_campaigns` | Search Campaigns |
| `search_threat_actors` | Search Threat Actors |
| `search_malware_families` | Search Malware Families |
| `search_software_toolkits` | Search Software Toolkits |
| `search_threat_reports` | Search Threat Reports |
| `search_vulnerabilities` | Search Vulnerabilities |
| `get_collection_timeline_events` | Get Collection Timeline Events |
| `get_collection_mitre_tree` | Get Collection Mitre Tree |
| `create_collection` | Create Collection |
| `update_collection_attributes` | Update Collection Attributes |
| `update_iocs_in_collection` | Update Iocs In Collection |
| `get_collection_feature_matches` | Get Collection Feature Matches |
| `get_collections_commonalities` | Get Collections Commonalities |
| `get_file_report` | Get File Report |
| `get_entities_related_to_a_file` | Get Entities Related To A File |
| `get_file_behavior_report` | Get File Behavior Report |
| `get_file_behavior_summary` | Get File Behavior Summary |
| `analyse_file` | Analyse File |
| `search_digital_threat_monitoring` | Search Digital Threat Monitoring |
| `search_iocs` | Search Iocs |
| `get_hunting_ruleset` | Get Hunting Ruleset |
| `get_entities_related_to_a_hunting_ruleset` | Get Entities Related To A Hunting Ruleset |
| `get_domain_report` | Get Domain Report |
| `get_entities_related_to_a_domain` | Get Entities Related To A Domain |
| `get_ip_address_report` | Get Ip Address Report |
| `get_entities_related_to_an_ip_address` | Get Entities Related To An Ip Address |
| `list_threat_profiles` | List Threat Profiles |
| `get_threat_profile` | Get Threat Profile |
| `get_threat_profile_recommendations` | Get Threat Profile Recommendations |
| `get_threat_profile_associations_timeline` | Get Threat Profile Associations Timeline |
| `get_url_report` | Get Url Report |
| `get_entities_related_to_an_url` | Get Entities Related To An Url |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Look up the SHA-256 hash d41d8cd98f00b204e9800998ecf8427e on VirusTotal and tell me how many engines flagged it."
- "Check the reputation of domain malware-c2.example.com — is it associated with any threat actors?"
- "Analyze the URL https://suspicious-site.example.com/payload.exe for threats."
- "Look up IP address 45.33.32.156 and tell me if it is known for malicious activity."
- "Search GTI for the Lazarus Group threat actor and summarize their TTPs."
- "Get the sandbox behavior report for file hash abc123... and list any network connections it makes."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e VIRUSTOTAL_API_KEY \
  hackerdogs/google-threat-intelligence-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8644:8644 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8644 \
  -e VIRUSTOTAL_API_KEY \
  hackerdogs/google-threat-intelligence-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "google-threat-intelligence-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "VIRUSTOTAL_API_KEY",
        "hackerdogs/google-threat-intelligence-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "VIRUSTOTAL_API_KEY": ""
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
    "google-threat-intelligence-mcp": {
      "url": "http://localhost:8644/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8644` | HTTP port (only used with `streamable-http`) |
| `VIRUSTOTAL_API_KEY` | — | VirusTotal / Google TI API key |
| `GOOGLE_THREAT_INTELLIGENCE_API_KEY` | — | Google Threat Intelligence API key (required) |

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
docker build -t hackerdogs/google-threat-intelligence-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name google-threat-intelligence-mcp-test -p 8644:8644 \
  -e MCP_TRANSPORT=streamable-http \
  -e VIRUSTOTAL_API_KEY \
  hackerdogs/google-threat-intelligence-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8644/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8644/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8644/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop google-threat-intelligence-mcp-test
```
