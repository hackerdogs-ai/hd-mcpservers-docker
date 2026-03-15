# AbuseIPDB MCP Server

A Model Context Protocol (MCP) server implementation that provides seamless integration with the AbuseIPDB API for IP reputation checking and abuse report management.

## Overview

This MCP server enables AI assistants and automated systems to query AbuseIPDB's threat intelligence database, allowing you to check IP addresses for malicious activity, retrieve abuse confidence scores, and access detailed historical report data through a standardized protocol interface.

## Features

- **IP Reputation Checks** - Query any IPv4 or IPv6 address for abuse reports
- **Confidence Scoring** - Get abuse confidence scores (0-100) based on report frequency and severity
- **Detailed Reporting** - Access comprehensive abuse report metadata and categories
- **Historical Data** - Query abuse reports within configurable time windows (up to 365 days)
- **Flexible Output** - Toggle between concise summaries and verbose detailed responses
- **Standards-Based** - Built on the Model Context Protocol for seamless integration

## Prerequisites

- **Python**: 3.13 or higher
- **AbuseIPDB API Key**: [Register for a free API key](https://www.abuseipdb.com/account/api)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Salmanwz/mcp-abuseipdb.git
cd mcp-abuseipdb
```

### 2. Install UV Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install Dependencies

```bash
uv add mcp[cli] httpx
```

## Configuration

### Option 1: Environment Variable (Standalone Usage)

```bash
export ABUSEIPDB_API_KEY="your_api_key_here"
```

### Option 2: Claude Desktop Integration

Add the following configuration to your Claude Desktop config file (`claude_desktop_config.json`):

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "abuseipdb": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-abuseipdb",
        "run",
        "abusedb.py"
      ],
      "env": {
        "ABUSEIPDB_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/mcp-abuseipdb` with the actual path and `your_api_key_here` with your API key.

## Usage

### Starting the Server (Standalone)

```bash
uv run abusedb.py
```

### Available Tools

#### `check` - IP Address Reputation Lookup

Queries AbuseIPDB for abuse reports associated with a given IP address.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ipAddress` | string | ✅ Yes | - | IPv4 or IPv6 address to check |
| `maxAgeInDays` | integer | ❌ No | 30 | Maximum age of reports (1-365 days) |
| `verbose` | boolean | ❌ No | false | Include detailed report breakdowns |

**Example Requests:**

```python
# Basic check - last 30 days
{
  "ipAddress": "1.2.3.4"
}

# Check with custom time window
{
  "ipAddress": "1.2.3.4",
  "maxAgeInDays": 90
}

# Verbose output with full details
{
  "ipAddress": "1.2.3.4",
  "maxAgeInDays": 90,
  "verbose": true
}
```

**Response Structure:**

```json
{
  "data": {
    "ipAddress": "1.2.3.4",
    "abuseConfidenceScore": 75,
    "totalReports": 42,
    "lastReportedAt": "2025-10-13T14:23:01+00:00",
    "isWhitelisted": false,
    "countryCode": "US",
    "usageType": "Data Center/Web Hosting/Transit",
    "isp": "Example Hosting Inc",
    "domain": "example-host.com",
    "reports": [...]  // Only included when verbose=true
  }
}
```

## Use Cases

- **Security Operations**: Integrate IP reputation checks into SOC workflows
- **Incident Response**: Quickly assess threat levels during investigations
- **Threat Intelligence**: Enrich security alerts with abuse data
- **Network Monitoring**: Automate suspicious IP detection and blocking
- **Log Analysis**: Cross-reference connection logs with known malicious IPs

## API Rate Limits

Free tier API keys are limited to **1,000 checks per day**. Upgrade to a premium plan for higher limits.

## Troubleshooting

### API Key Issues

```bash
# Verify your API key is set
echo $ABUSEIPDB_API_KEY

# Test connectivity
curl -G https://api.abuseipdb.com/api/v2/check \
  --data-urlencode "ipAddress=8.8.8.8" \
  -H "Key: $ABUSEIPDB_API_KEY"
```

### Claude Desktop Connection

1. Verify the config file path and JSON syntax
2. Restart Claude Desktop after configuration changes
3. Check the MCP server logs for connection errors

## Development

### Project Structure

```
mcp-abuseipdb/
├── abusedb.py          # Main MCP server implementation
├── pyproject.toml      # UV/Python dependencies
├── README.md           # This file
└── LICENSE            # License information
```

### Running Tests

```bash
# Add test dependencies
uv add pytest pytest-asyncio httpx

# Run tests
uv run pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Security

This server handles sensitive threat intelligence data. Best practices:

- **Never commit API keys** to version control
- Store API keys in environment variables or secure vaults
- Use HTTPS for all API communications (enforced by default)
- Implement rate limiting in production deployments
- Monitor API usage for anomalies

## Resources

- [AbuseIPDB Official Documentation](https://docs.abuseipdb.com/)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [UV Package Manager Docs](https://docs.astral.sh/uv/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io/)
- Powered by [AbuseIPDB](https://www.abuseipdb.com/)
- Uses [UV](https://github.com/astral-sh/uv) for dependency management

---

**Note**: This is an unofficial implementation and is not affiliated with or endorsed by AbuseIPDB.
