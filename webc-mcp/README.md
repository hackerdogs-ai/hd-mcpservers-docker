# webc-mcp

Web Content Analysis MCP Server — curated from the original 30-tool suite down to 13 validated, self-contained tools with no external dependencies.

## Tool Audit

The original `webc_langchain.py` had **30 tools**. After audit:
- **Removed 17 tools** — redundant, non-functional, or out of scope (geo distance, credit card validation, duplicate NLP methods, tools requiring paid translation APIs)
- **Kept 13 tools** — all validated with standard library implementations

## Tools

### Web Content (5 tools)
| Tool | Description |
|------|------------|
| `analyze_webpage` | Fetch URL → title, meta, text preview, links, images |
| `extract_text` | Extract clean text from webpage (strips nav/scripts) |
| `extract_emails` | Find email addresses in text or webpage |
| `extract_entities` | Find URLs, emails, IPs, phones, hashes in text/URL |
| `find_sensitive_data` | Detect PII: credit cards, SSN, AWS keys, JWTs |

### Domain / Network (6 tools)
| Tool | Description |
|------|------------|
| `analyze_domain` | Combined DNS + WHOIS + TLD analysis |
| `resolve_dns` | DNS record resolution (A, AAAA, MX, NS, TXT) |
| `get_whois` | WHOIS lookup for domain or IP |
| `get_ip_location` | GeoIP lookup via ip-api.com |
| `get_ssl_certificate` | SSL/TLS certificate details |
| `scan_port` | TCP port open/closed check |

### Text / NLP (2 tools)
| Tool | Description |
|------|------------|
| `detect_language` | Language detection with probability scores |
| `extract_keyterms` | Key term extraction via word frequency |

## Quick Start

```bash
docker build -t webc-mcp .
docker run -p 8504:8504 -e MCP_TRANSPORT=streamable-http webc-mcp
```
