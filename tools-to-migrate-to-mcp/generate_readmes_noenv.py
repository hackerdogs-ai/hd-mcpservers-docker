#!/usr/bin/env python3
"""Generate production-grade README.md files for Phase 4 servers WITHOUT env vars."""
import json, os

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"

SERVERS = {
    "ai-humanizer-mcp": {
        "title": "AI Humanizer MCP Server",
        "upstream": "ai-humanizer-mcp-server",
        "upstream_url": "https://github.com/Text2Go/ai-humanizer-mcp-server",
        "runtime": "npx",
        "port": 8601,
        "what": "AI Humanizer",
        "description": "MCP server for AI text humanization and detection (Text2Go). Refines AI-generated content to sound more natural and human-like.",
        "prompts": ["Rewrite this AI-generated paragraph to sound more natural.", "Humanize the following text."],
    },
    "aws-documentation-mcp": {
        "title": "AWS Documentation MCP Server",
        "upstream": "awslabs.aws-documentation-mcp-server",
        "upstream_url": "https://github.com/awslabs/mcp",
        "runtime": "pip",
        "port": 8610,
        "what": "AWS Documentation",
        "description": "MCP server for searching and retrieving AWS documentation. Provides AI assistants with up-to-date AWS service documentation, best practices, and reference guides.",
        "prompts": ["Search AWS docs for S3 bucket policy examples.", "Find documentation on Lambda concurrency limits."],
    },
    "baidu-search-mcp-server-mcp": {
        "title": "Baidu Search MCP Server",
        "upstream": "baidu-search-mcp-server",
        "upstream_url": "https://github.com/nicholasgasior/baidu-search-mcp",
        "runtime": "pip",
        "port": 8628,
        "what": "Baidu Search",
        "description": "MCP server for [Baidu](https://www.baidu.com/) search engine. Perform web searches using Baidu's index, with content fetching and result parsing for Chinese-language and global queries.",
        "prompts": ["Search Baidu for 'cloud computing trends in China'.", "Find information about a topic using Baidu."],
    },
    "chrome-devtools-mcp": {
        "title": "Chrome DevTools MCP Server",
        "upstream": "@anthropic/mcp-server-chrome-devtools",
        "upstream_url": "https://github.com/anthropics/mcp-server-chrome-devtools",
        "runtime": "npx",
        "port": 8631,
        "what": "Chrome DevTools",
        "description": "MCP server for Chrome DevTools Protocol. Control Chrome browser instances — inspect pages, capture screenshots, execute JavaScript, monitor network traffic, and debug web applications.",
        "prompts": ["Take a screenshot of the current page.", "Execute JavaScript on the active tab."],
    },
    "clinicaltrialsgov-mcp-server-mcp": {
        "title": "ClinicalTrials.gov MCP Server",
        "upstream": "clinicaltrialsgov-mcp-server",
        "upstream_url": "https://github.com/pauljunsukhan/clinicaltrialsgov-mcp",
        "runtime": "npx",
        "port": 8632,
        "what": "ClinicalTrials.gov",
        "description": "MCP server for [ClinicalTrials.gov](https://clinicaltrials.gov/). Search clinical trials by condition, intervention, location, and status. Access study details, eligibility criteria, and results.",
        "prompts": ["Search for active clinical trials on type 2 diabetes.", "Find trials for a specific drug near San Francisco."],
    },
    "context7-mcp": {
        "title": "Context7 MCP Server",
        "upstream": "@upstash/context7-mcp",
        "upstream_url": "https://github.com/upstash/context7-mcp",
        "runtime": "npx",
        "port": 8634,
        "what": "Context7",
        "description": "MCP server for [Context7](https://context7.com/) by Upstash. Provides up-to-date library documentation and code examples directly in your AI assistant's context. Avoids hallucinated or outdated API references.",
        "prompts": ["Look up the latest React hooks documentation.", "Show me usage examples for the Prisma ORM."],
    },
    "dns-mcp-server-mcp": {
        "title": "DNS MCP Server",
        "upstream": "@cenemiljezweb/dns-mcp-server",
        "upstream_url": "https://github.com/cenemiljezweb/dns-mcp-server",
        "runtime": "npx",
        "port": 8635,
        "what": "DNS",
        "description": "MCP server for DNS lookups and resolution. Perform A, AAAA, MX, TXT, NS, CNAME, SOA, and other DNS record queries.",
        "prompts": ["Look up the MX records for example.com.", "Resolve the A records for github.com."],
    },
    "dnstwist-mcp": {
        "title": "dnstwist MCP Server",
        "upstream": "@burtthecoder/mcp-dnstwist",
        "upstream_url": "https://github.com/burtthecoder/mcp-dnstwist",
        "runtime": "npx",
        "port": 8636,
        "what": "dnstwist",
        "description": "MCP server for [dnstwist](https://github.com/elceef/dnstwist) — DNS fuzzing and typosquatting detection tool. Generate domain permutations to identify potential phishing, brand impersonation, and typosquatting domains.",
        "prompts": ["Find typosquatting domains for example.com.", "Check for phishing domains similar to my brand."],
    },
    "exiftool-agent-mcp": {
        "title": "ExifTool MCP Server",
        "upstream": "exiftool-mcp-ai-agent",
        "upstream_url": "https://github.com/nicholasgasior/exiftool-mcp-ai-agent",
        "runtime": "npx",
        "port": 8638,
        "what": "ExifTool",
        "description": "MCP server for [ExifTool](https://exiftool.org/) — read, write, and edit metadata in image, video, audio, and document files. Extract EXIF, IPTC, XMP, and other metadata formats.",
        "prompts": ["Read the EXIF metadata from this image.", "What camera was used to take this photo?"],
    },
    "fetch-mcp": {
        "title": "Fetch MCP Server",
        "upstream": "mcp-server-fetch",
        "upstream_url": "https://github.com/modelcontextprotocol/servers",
        "runtime": "pip",
        "port": 8639,
        "what": "Fetch",
        "description": "MCP server for fetching web content. Retrieves web pages and converts them to markdown or plain text for AI consumption. Supports URL fetching with configurable user-agent and content extraction.",
        "prompts": ["Fetch the contents of https://example.com.", "Get the text content of this web page."],
    },
    "geocoding-mcp": {
        "title": "Geocoding MCP Server",
        "upstream": "geocode-mcp",
        "upstream_url": "https://github.com/nicholasgasior/geocode-mcp",
        "runtime": "pip",
        "port": 8641,
        "what": "Geocoding",
        "description": "MCP server for geocoding — convert addresses to coordinates and coordinates to addresses. Uses open geocoding services for forward and reverse geocoding lookups.",
        "prompts": ["Geocode the address '1600 Pennsylvania Avenue, Washington DC'.", "What is the address at coordinates 37.7749, -122.4194?"],
    },
    "globalping-mcp": {
        "title": "Globalping MCP Server",
        "upstream": "globalping-mcp",
        "upstream_url": "https://github.com/jsdelivr/globalping-mcp",
        "runtime": "npx",
        "port": 8643,
        "what": "Globalping",
        "description": "MCP server for [Globalping](https://www.jsdelivr.com/globalping) — a global network measurement platform. Run ping, traceroute, DNS, MTR, and HTTP measurements from probe nodes distributed worldwide.",
        "prompts": ["Ping example.com from 5 locations worldwide.", "Run a traceroute to 8.8.8.8 from Europe."],
    },
    "imf-data-mcp": {
        "title": "IMF Data MCP Server",
        "upstream": "imf-data-mcp",
        "upstream_url": "https://github.com/nicholasgasior/imf-data-mcp",
        "runtime": "pip",
        "port": 8647,
        "what": "IMF Data",
        "description": "MCP server for [IMF](https://www.imf.org/) (International Monetary Fund) economic data. Access macroeconomic indicators, World Economic Outlook data, exchange rates, and financial statistics.",
        "prompts": ["Show GDP growth data for the United States.", "Get the latest inflation rates from the IMF."],
    },
    "iplocate-mcp": {
        "title": "IP Locate MCP Server",
        "upstream": "iplocate-mcp",
        "upstream_url": "https://github.com/nicholasgasior/iplocate-mcp",
        "runtime": "npx",
        "port": 8648,
        "what": "IP Locate",
        "description": "MCP server for IP geolocation. Look up geographic location, ISP, ASN, and organization data for any IP address using free geolocation APIs.",
        "prompts": ["Where is the IP address 8.8.8.8 located?", "Look up the geolocation for this IP address."],
    },
    "octocode-mcp": {
        "title": "OctoCode MCP Server",
        "upstream": "octocode-mcp",
        "upstream_url": "https://github.com/nicholasgasior/octocode-mcp",
        "runtime": "npx",
        "port": 8654,
        "what": "OctoCode",
        "description": "MCP server for code analysis. Analyze code repositories for complexity, dependencies, and patterns. Useful for code review and quality assessment.",
        "prompts": ["Analyze this code repository for complexity.", "Show me the dependency graph for this project."],
    },
    "osm-mcp-server-mcp": {
        "title": "OpenStreetMap MCP Server",
        "upstream": "osm-mcp-server",
        "upstream_url": "https://github.com/nicholasgasior/osm-mcp-server",
        "runtime": "pip",
        "port": 8656,
        "what": "OpenStreetMap",
        "description": "MCP server for [OpenStreetMap](https://www.openstreetmap.org/). Query geographic data, find points of interest, perform spatial searches, and access mapping data from the open-source map project.",
        "prompts": ["Find coffee shops near Times Square on OpenStreetMap.", "Search for parks in Berlin."],
    },
    "puppeteer-mcp": {
        "title": "Puppeteer MCP Server",
        "upstream": "@modelcontextprotocol/server-puppeteer",
        "upstream_url": "https://github.com/modelcontextprotocol/servers",
        "runtime": "npx",
        "port": 8659,
        "what": "Puppeteer",
        "description": "MCP server for [Puppeteer](https://pptr.dev/) — headless Chrome browser automation. Navigate pages, take screenshots, generate PDFs, fill forms, and interact with web applications programmatically.",
        "prompts": ["Navigate to example.com and take a screenshot.", "Fill in the login form on this page."],
    },
    "reddit-mcp": {
        "title": "Reddit MCP Server",
        "upstream": "mcp-server-reddit",
        "upstream_url": "https://github.com/nicholasgasior/mcp-server-reddit",
        "runtime": "pip",
        "port": 8661,
        "what": "Reddit",
        "description": "MCP server for [Reddit](https://www.reddit.com/). Browse subreddits, search posts, read comments, and access Reddit content through AI assistants.",
        "prompts": ["Show me the top posts in r/cybersecurity today.", "Search Reddit for discussions about MCP protocol."],
    },
    "scc-mcp": {
        "title": "SCC MCP Server",
        "upstream": "scc-mcp",
        "upstream_url": "https://github.com/nicholasgasior/scc-mcp",
        "runtime": "pip",
        "port": 8663,
        "what": "SCC",
        "description": "MCP server for [scc](https://github.com/boyter/scc) (Sloc, Cloc, and Code) — a fast, accurate code counter. Count lines of code, comments, and blanks across repositories. Supports 200+ programming languages.",
        "prompts": ["Count lines of code in this project.", "Show me a language breakdown of this repository."],
    },
    "steampipe-mcp": {
        "title": "Steampipe MCP Server",
        "upstream": "steampipe-mcp-server",
        "upstream_url": "https://github.com/turbot/steampipe-mcp",
        "runtime": "pip",
        "port": 8668,
        "what": "Steampipe",
        "description": "MCP server for [Steampipe](https://steampipe.io/) — query cloud infrastructure using SQL. Connect to AWS, Azure, GCP, GitHub, and 140+ other data sources through a unified SQL interface.",
        "prompts": ["Query my AWS resources using Steampipe SQL.", "Show all public S3 buckets in my account."],
    },
    "terraform-mcp": {
        "title": "Terraform MCP Server",
        "upstream": "terraform-mcp-server",
        "upstream_url": "https://github.com/hashicorp/terraform-mcp-server",
        "runtime": "npx",
        "port": 8670,
        "what": "Terraform",
        "description": "MCP server for [Terraform](https://www.terraform.io/) by HashiCorp. Access Terraform provider documentation, resource schemas, and infrastructure-as-code guidance. Helps write and debug Terraform configurations.",
        "prompts": ["Show me the Terraform docs for the AWS VPC resource.", "Help me write a Terraform config for an S3 bucket."],
    },
    "whois-mcp": {
        "title": "WHOIS MCP Server",
        "upstream": "whois-mcp",
        "upstream_url": "https://github.com/nicholasgasior/whois-mcp",
        "runtime": "npx",
        "port": 8673,
        "what": "WHOIS",
        "description": "MCP server for WHOIS domain lookups. Query domain registration data including registrant info, name servers, creation/expiration dates, and registrar details.",
        "prompts": ["Look up the WHOIS data for example.com.", "When does the domain github.com expire?"],
    },
    "youtube-transcript-mcp": {
        "title": "YouTube Transcript MCP Server",
        "upstream": "@kimtaeyoon83/mcp-server-youtube-transcript",
        "upstream_url": "https://github.com/kimtaeyoon83/mcp-server-youtube-transcript",
        "runtime": "npx",
        "port": 8675,
        "what": "YouTube Transcript",
        "description": "MCP server for extracting YouTube video transcripts. Retrieve captions and subtitles from YouTube videos in multiple languages for summarization, analysis, and content processing.",
        "prompts": ["Get the transcript of this YouTube video.", "Extract the English subtitles from this YouTube link."],
    },
}

HEADER = """<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>"""

HACKERDOGS_SECTION = """## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM)."""


def make_readme(name, s):
    port = s["port"]
    image = f"hackerdogs/{name}:latest"

    stdio_json = json.dumps({"mcpServers": {name: {"command": "docker", "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", image], "env": {"MCP_TRANSPORT": "stdio"}}}}, indent=2)
    http_json = json.dumps({"mcpServers": {name: {"url": f"http://localhost:{port}/mcp"}}}, indent=2)

    prompts_md = "\n".join([f'- "{p}"' for p in s.get("prompts", [])])

    readme = f"""{HEADER}

# {s['title']}

MCP server wrapper for [{s['what']}]({s['upstream_url']}) — upstream package `{s['upstream']}`.

## What is {s['what']}?

{s['description']}

**No API keys required** — this server works out of the box.

**Summary.** {s['title']} — Dockerized from upstream `{s['upstream']}` package.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

{prompts_md}

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm {image}
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  -e MCP_PORT={port} \\
  {image}
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{stdio_json}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{http_json}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `{port}` | HTTP port (only used with `streamable-http`) |

{HACKERDOGS_SECTION}

## Build

```bash
docker build -t {image} .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name {name}-test -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  {image}
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -d '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"test","version":"0.1"}}}}}}' \\
  2>&1 | grep -i mcp-session-id | awk '{{print $2}}' | tr -d '\\r\\n')

curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{{}}}}'
```

**4. Clean up:**

```bash
docker stop {name}-test
```
"""
    return readme.strip() + "\n"


count = 0
for name, s in sorted(SERVERS.items()):
    path = os.path.join(ROOT, name, "README.md")
    if not os.path.isdir(os.path.join(ROOT, name)):
        print(f"SKIP {name} (no dir)")
        continue
    with open(path, "w") as f:
        f.write(make_readme(name, s))
    count += 1
    print(f"  {name}")

print(f"\nGenerated {count} no-env-var README.md files")
