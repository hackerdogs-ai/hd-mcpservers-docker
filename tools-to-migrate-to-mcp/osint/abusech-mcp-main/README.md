# abusech-mcp 🚦

**abusech-mcp** is an MCP server that fetches threat intelligence from multiple [abuse.ch](https://abuse.ch/) platforms, including MalwareBazaar, URLhaus, and ThreatFox.

## Features

- Unified VT-like API for querying file, URL, IP, and domain intelligence
- Uses Pydantic schemas for robust data validation and serialization
- **Powered by [fastmcp](https://gofastmcp.com/getting-started/welcome):**
- **Unified API layer:** Directly use functions from `abusech_intel.py` to obtain correlated intelligence from abuse.ch platforms—serving as a unified API layer since the platforms themselves do not provide one

## Requirements

- Python 3.10+
- abuse.ch API key (set as `ABUSECH_API_KEY` environment variable)

## Usage

Start the MCP server:

```bash
python abusech_mcp.py
```

## Available Tools

- `get_ip_report(ip: str)`: Get a comprehensive IP report from URLhaus and ThreatFox
- `get_domain_report(domain: str)`: Get a domain report from URLhaus and ThreatFox
- `get_url_report(url: str)`: Get a URL report from URLhaus and ThreatFox
- `get_file_report(hash_value: str)`: Get a file report (MD5/SHA-1/SHA-256) from MalwareBazaar, URLhaus, and ThreatFox

## Configuration

Set your API key as an environment variable:

```bash
export ABUSECH_API_KEY=your_api_key_here
```

## License

MIT License
