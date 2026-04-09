# abstract-mcp

MCP server wrapping 9 AbstractAPI endpoints for intelligence lookups.

## Tools

| Tool | API Key Env Var | Endpoint |
|------|----------------|----------|
| abstract_phone_intelligence | ABSTRACT_PHONE_API_KEY | Phone lookup |
| abstract_email_reputation | ABSTRACT_EMAIL_API_KEY | Email reputation |
| abstract_iban_validation | ABSTRACT_IBAN_API_KEY | IBAN validation |
| abstract_vat_validation | ABSTRACT_VAT_API_KEY | VAT validation |
| abstract_ip_intelligence | ABSTRACT_IP_API_KEY | IP geolocation/intelligence |
| abstract_holidays | ABSTRACT_HOLIDAYS_API_KEY | Holiday lookup by date/country |
| abstract_exchange_rates | ABSTRACT_EXCHANGE_API_KEY | Live FX rates |
| abstract_company_enrichment | ABSTRACT_COMPANY_API_KEY | Company data by domain |
| abstract_timezone | ABSTRACT_TIMEZONE_API_KEY | Current time by location |

## Quick Start

```bash
docker build -t abstract-mcp .
docker run -p 8501:8501 -e MCP_TRANSPORT=streamable-http abstract-mcp
```
