#!/usr/bin/env python3
"""AbstractAPI MCP Server — phone, email, IP, IBAN, VAT, holidays, FX, company, timezone."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("abstract-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8501"))
mcp = FastMCP("AbstractAPI MCP Server", instructions="Multi-endpoint AbstractAPI intelligence: phone, email, IP, IBAN, VAT, holidays, FX rates, company enrichment, timezone.")


@mcp.tool()
def abstract_phone_intelligence(phone: str) -> str:
    """Look up phone number intelligence via AbstractAPI. Requires ABSTRACT_PHONE_API_KEY."""
    key = os.environ.get("ABSTRACT_PHONE_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_PHONE_API_KEY not set"})
    if not phone or not phone.strip():
        return json.dumps({"error": "phone is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://phoneintelligence.abstractapi.com/v1/", params={"api_key": key, "phone": phone.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_email_reputation(email: str) -> str:
    """Check email reputation and deliverability via AbstractAPI. Requires ABSTRACT_EMAIL_API_KEY."""
    key = os.environ.get("ABSTRACT_EMAIL_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_EMAIL_API_KEY not set"})
    if not email or not email.strip():
        return json.dumps({"error": "email is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://emailreputation.abstractapi.com/v1/", params={"api_key": key, "email": email.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_iban_validation(iban: str) -> str:
    """Validate an IBAN number via AbstractAPI. Requires ABSTRACT_IBAN_API_KEY."""
    key = os.environ.get("ABSTRACT_IBAN_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_IBAN_API_KEY not set"})
    if not iban or not iban.strip():
        return json.dumps({"error": "iban is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://ibanvalidation.abstractapi.com/v1/", params={"api_key": key, "iban": iban.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_vat_validation(vat_number: str) -> str:
    """Validate a VAT number via AbstractAPI. Requires ABSTRACT_VAT_API_KEY."""
    key = os.environ.get("ABSTRACT_VAT_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_VAT_API_KEY not set"})
    if not vat_number or not vat_number.strip():
        return json.dumps({"error": "vat_number is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://vat.abstractapi.com/v1/validate/", params={"api_key": key, "vat_number": vat_number.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_ip_intelligence(ip_address: str) -> str:
    """Look up IP geolocation and intelligence via AbstractAPI. Requires ABSTRACT_IP_API_KEY."""
    key = os.environ.get("ABSTRACT_IP_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_IP_API_KEY not set"})
    if not ip_address or not ip_address.strip():
        return json.dumps({"error": "ip_address is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://ip-intelligence.abstractapi.com/v1/", params={"api_key": key, "ip_address": ip_address.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_holidays(country: str, year: int, month: int, day: int) -> str:
    """Look up holidays for a given country and date via AbstractAPI. Requires ABSTRACT_HOLIDAYS_API_KEY."""
    key = os.environ.get("ABSTRACT_HOLIDAYS_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_HOLIDAYS_API_KEY not set"})
    if not country or not country.strip():
        return json.dumps({"error": "country is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://holidays.abstractapi.com/v1/", params={"api_key": key, "country": country.strip(), "year": year, "month": month, "day": day})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_exchange_rates(base: str, target: str) -> str:
    """Get live exchange rates between currencies via AbstractAPI. Requires ABSTRACT_EXCHANGE_API_KEY."""
    key = os.environ.get("ABSTRACT_EXCHANGE_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_EXCHANGE_API_KEY not set"})
    if not base or not base.strip():
        return json.dumps({"error": "base is required"})
    if not target or not target.strip():
        return json.dumps({"error": "target is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://exchange-rates.abstractapi.com/v1/live/", params={"api_key": key, "base": base.strip(), "target": target.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_company_enrichment(domain: str) -> str:
    """Enrich company data by domain via AbstractAPI. Requires ABSTRACT_COMPANY_API_KEY."""
    key = os.environ.get("ABSTRACT_COMPANY_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_COMPANY_API_KEY not set"})
    if not domain or not domain.strip():
        return json.dumps({"error": "domain is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://companyenrichment.abstractapi.com/v2/", params={"api_key": key, "domain": domain.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def abstract_timezone(location: str) -> str:
    """Get current time for a location via AbstractAPI. Requires ABSTRACT_TIMEZONE_API_KEY."""
    key = os.environ.get("ABSTRACT_TIMEZONE_API_KEY", "")
    if not key:
        return json.dumps({"error": "ABSTRACT_TIMEZONE_API_KEY not set"})
    if not location or not location.strip():
        return json.dumps({"error": "location is required"})
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.get("https://timezone.abstractapi.com/v1/current_time/", params={"api_key": key, "location": location.strip()})
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text[:500]})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting abstract-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
