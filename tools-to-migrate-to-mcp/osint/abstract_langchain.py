"""
AbstractAPI Tools for LangChain Agents

This module provides LangChain tools for multiple AbstractAPI endpoints:
- Phone Intelligence API
- Email Reputation API
- IBAN Validation API
- VAT Validation API
- IP Intelligence API
- Holidays API
- Exchange Rates API
- Company Enrichment API
- Timezone API

References:
- AbstractAPI docs: https://www.abstractapi.com/

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

These tools require API keys. Keys should be supplied via ToolRuntime (preferred),
following the same pattern used in other tools like `browserless_langchain.py`.

Retrieval Priority (in order):
1) PRIMARY: runtime.state["environment_variables"][<instance>][KEY]
   - Searches through all instances inside the environment_variables dict
   - First match wins per key
2) SECONDARY: runtime.state["api_keys"][KEY]

Expected key naming pattern:
- <SERVICE>_API_KEY

Supported keys:
- PHONE_INTELLIGENCE_API_KEY
- EMAIL_REPUTATION_API_KEY
- IBAN_VALIDATION_API_KEY
- VAT_API_KEY
- IP_INTELLIGENCE_API_KEY
- HOLIDAYS_API_KEY
- EXCHANGE_RATES_API_KEY
- COMPANY_ENRICHMENT_API_KEY
- TIMEZONE_API_KEY

Security Notes:
- API keys are masked in logs. Never log raw keys.
- Inputs like phone numbers, emails, IBANs, VAT numbers may be sensitive; logs are minimized.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

import requests
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key

logger = setup_logger(__name__, log_file_path="logs/abstractapi_tools.log")

# Reuse connections under load
_SESSION = requests.Session()


class AbstractSecurityAgentState(AgentState):
    """Extended agent state for AbstractAPI operations."""
    user_id: str = ""


def _get_api_key_from_runtime(
    runtime: ToolRuntime,
    key_name: str,
) -> Optional[str]:
    """
    Retrieve an API key from ToolRuntime state.

    Key resolution order:
    1) runtime.state["environment_variables"][<instance>][key_name]
    2) runtime.state["api_keys"][key_name]
    """
    # PRIMARY: runtime.state.environment_variables[<instance>][KEY]
    if runtime and getattr(runtime, "state", None):
        env_vars_dict = runtime.state.get("environment_variables", {})
        if isinstance(env_vars_dict, dict):
            for instance_name, env_vars in env_vars_dict.items():
                if not isinstance(env_vars, dict):
                    continue
                val = env_vars.get(key_name)
                if val:
                    safe_log_info(
                        logger,
                        "[_get_api_key_from_runtime] Found API key in runtime env",
                        key_name=key_name,
                        instance_name=instance_name,
                        api_key_masked=mask_api_key(str(val)),
                    )
                    return str(val)

        # SECONDARY: runtime.state.api_keys[KEY]
        api_keys_dict = runtime.state.get("api_keys", {})
        if isinstance(api_keys_dict, dict):
            val = api_keys_dict.get(key_name)
            if val:
                safe_log_info(
                    logger,
                    "[_get_api_key_from_runtime] Found API key in runtime api_keys",
                    key_name=key_name,
                    api_key_masked=mask_api_key(str(val)),
                )
                return str(val)

    return None


def _request_json(
    *,
    url: str,
    params: Dict[str, Any],
    timeout: int = 30,
) -> Tuple[bool, str, Any]:
    """
    Make a GET request and return (ok, message, data).
    """
    try:
        resp = _SESSION.get(url, params=params, timeout=timeout)
        content_type = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
        safe_log_debug(
            logger,
            "[_request_json] Response received",
            url=url,
            status_code=resp.status_code,
            content_type=content_type,
            content_length=len(resp.content) if resp.content else 0,
        )

        # AbstractAPI typically returns JSON; handle non-JSON safely
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}

        if resp.status_code >= 400:
            return False, f"HTTP {resp.status_code}", data
        return True, "ok", data
    except requests.exceptions.Timeout as e:
        return False, f"timeout: {str(e)}", None
    except requests.exceptions.RequestException as e:
        return False, f"request_error: {str(e)}", None
    except Exception as e:
        return False, f"unexpected_error: {str(e)}", None


def _validate_required_fields(
    *,
    endpoint_name: str,
    data: Any,
    required: Dict[str, type],
    allow_empty: bool = False,
) -> Tuple[bool, str]:
    """
    Validate that a response contains required top-level fields with expected types.

    This is intentionally lightweight (not a full schema validator), but it prevents
    returning "junk" such as empty dicts, wrong types, or missing core fields.
    """
    if data is None:
        return False, f"{endpoint_name}: response is None"

    if isinstance(data, dict):
        if not data and not allow_empty:
            return False, f"{endpoint_name}: empty object response"
        for k, t in required.items():
            if k not in data:
                return False, f"{endpoint_name}: missing required field '{k}'"
            if not isinstance(data.get(k), t):
                return False, f"{endpoint_name}: field '{k}' expected {t.__name__}, got {type(data.get(k)).__name__}"
        return True, "ok"

    if isinstance(data, list):
        if not data and not allow_empty:
            return False, f"{endpoint_name}: empty list response"
        return True, "ok"

    return False, f"{endpoint_name}: unexpected response type {type(data).__name__}"


@tool
def abstract_phone_intelligence(
    runtime: ToolRuntime,
    phone: str,
    timeout: int = 30,
) -> str:
    """
    Phone Intelligence API (AbstractAPI).

    Endpoint:
      https://phoneintelligence.abstractapi.com/v1/

    Required key:
      PHONE_INTELLIGENCE_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_phone_intelligence] Starting", phone=phone, timeout=timeout)
        if not phone or not isinstance(phone, str):
            return json.dumps({"status": "error", "message": "phone must be a non-empty string"})

        key = _get_api_key_from_runtime(runtime, "PHONE_INTELLIGENCE_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "PHONE_INTELLIGENCE_API_KEY not found in ToolRuntime"})

        url = "https://phoneintelligence.abstractapi.com/v1/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "phone": phone}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_phone_intelligence] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        # Validate minimal expected structure
        is_ok, vmsg = _validate_required_fields(
            endpoint_name="phone_intelligence",
            data=data,
            required={"phone_number": str},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_phone_intelligence] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_phone_intelligence] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Phone intelligence failed: {str(e)}"})


@tool
def abstract_email_reputation(
    runtime: ToolRuntime,
    email: str,
    timeout: int = 30,
) -> str:
    """
    Email Reputation API (AbstractAPI).

    Endpoint:
      https://emailreputation.abstractapi.com/v1/

    Required key:
      EMAIL_REPUTATION_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_email_reputation] Starting", email=email, timeout=timeout)
        if not email or not isinstance(email, str):
            return json.dumps({"status": "error", "message": "email must be a non-empty string"})

        key = _get_api_key_from_runtime(runtime, "EMAIL_REPUTATION_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "EMAIL_REPUTATION_API_KEY not found in ToolRuntime"})

        url = "https://emailreputation.abstractapi.com/v1/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "email": email}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_email_reputation] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        is_ok, vmsg = _validate_required_fields(
            endpoint_name="email_reputation",
            data=data,
            required={"email_address": str},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_email_reputation] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_email_reputation] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Email reputation failed: {str(e)}"})


@tool
def abstract_iban_validation(
    runtime: ToolRuntime,
    iban: str,
    timeout: int = 30,
) -> str:
    """
    IBAN Validation API (AbstractAPI).

    Endpoint:
      https://ibanvalidation.abstractapi.com/v1/

    Required key:
      IBAN_VALIDATION_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_iban_validation] Starting", timeout=timeout)
        if not iban or not isinstance(iban, str):
            return json.dumps({"status": "error", "message": "iban must be a non-empty string"})

        key = _get_api_key_from_runtime(runtime, "IBAN_VALIDATION_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "IBAN_VALIDATION_API_KEY not found in ToolRuntime"})

        url = "https://ibanvalidation.abstractapi.com/v1/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "iban": iban}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_iban_validation] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        is_ok, vmsg = _validate_required_fields(
            endpoint_name="iban_validation",
            data=data,
            required={"iban": str, "is_valid": bool},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_iban_validation] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_iban_validation] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"IBAN validation failed: {str(e)}"})


@tool
def abstract_vat_validation(
    runtime: ToolRuntime,
    vat_number: str,
    timeout: int = 30,
) -> str:
    """
    VAT Validation API (AbstractAPI).

    Endpoint:
      https://vat.abstractapi.com/v1/validate/

    Required key:
      VAT_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_vat_validation] Starting", timeout=timeout)
        if not vat_number or not isinstance(vat_number, str):
            return json.dumps({"status": "error", "message": "vat_number must be a non-empty string"})

        key = _get_api_key_from_runtime(runtime, "VAT_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "VAT_API_KEY not found in ToolRuntime"})

        url = "https://vat.abstractapi.com/v1/validate/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "vat_number": vat_number}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_vat_validation] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        is_ok, vmsg = _validate_required_fields(
            endpoint_name="vat_validation",
            data=data,
            required={"vat_number": str, "valid": bool},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_vat_validation] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_vat_validation] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"VAT validation failed: {str(e)}"})


@tool
def abstract_ip_intelligence(
    runtime: ToolRuntime,
    ip_address: str,
    timeout: int = 30,
) -> str:
    """
    IP Intelligence API (AbstractAPI).

    Endpoint:
      https://ip-intelligence.abstractapi.com/v1/

    Required key:
      IP_INTELLIGENCE_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_ip_intelligence] Starting", ip_address=ip_address, timeout=timeout)
        if not ip_address or not isinstance(ip_address, str):
            return json.dumps({"status": "error", "message": "ip_address must be a non-empty string"})

        key = _get_api_key_from_runtime(runtime, "IP_INTELLIGENCE_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "IP_INTELLIGENCE_API_KEY not found in ToolRuntime"})

        url = "https://ip-intelligence.abstractapi.com/v1/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "ip_address": ip_address}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_ip_intelligence] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        is_ok, vmsg = _validate_required_fields(
            endpoint_name="ip_intelligence",
            data=data,
            required={"ip_address": str},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_ip_intelligence] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_ip_intelligence] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"IP intelligence failed: {str(e)}"})


@tool
def abstract_holidays(
    runtime: ToolRuntime,
    country: str,
    year: int,
    month: int,
    day: int,
    timeout: int = 30,
) -> str:
    """
    Holidays API (AbstractAPI).

    Endpoint:
      https://holidays.abstractapi.com/v1/

    Required key:
      HOLIDAYS_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_holidays] Starting", country=country, year=year, month=month, day=day, timeout=timeout)
        if not country or not isinstance(country, str):
            return json.dumps({"status": "error", "message": "country must be a non-empty string (ISO country code)"})
        if year < 1 or month < 1 or month > 12 or day < 1 or day > 31:
            return json.dumps({"status": "error", "message": "Invalid date parameters"})

        key = _get_api_key_from_runtime(runtime, "HOLIDAYS_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "HOLIDAYS_API_KEY not found in ToolRuntime"})

        url = "https://holidays.abstractapi.com/v1/"
        ok, msg, data = _request_json(
            url=url,
            params={"api_key": key, "country": country, "year": year, "month": month, "day": day},
            timeout=timeout,
        )
        if not ok:
            safe_log_error(logger, "[abstract_holidays] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        # Holidays returns a list of holiday objects (may be empty if no holiday)
        is_ok, vmsg = _validate_required_fields(
            endpoint_name="holidays",
            data=data,
            required={},
            allow_empty=True,
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_holidays] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_holidays] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Holidays lookup failed: {str(e)}"})


@tool
def abstract_exchange_rates_live(
    runtime: ToolRuntime,
    base: str,
    target: str,
    timeout: int = 30,
) -> str:
    """
    Exchange Rates API (AbstractAPI) - live rates.

    Endpoint:
      https://exchange-rates.abstractapi.com/v1/live/

    Required key:
      EXCHANGE_RATES_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_exchange_rates_live] Starting", base=base, target=target, timeout=timeout)
        if not base or not isinstance(base, str) or not target or not isinstance(target, str):
            return json.dumps({"status": "error", "message": "base and target must be non-empty currency codes"})

        key = _get_api_key_from_runtime(runtime, "EXCHANGE_RATES_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "EXCHANGE_RATES_API_KEY not found in ToolRuntime"})

        url = "https://exchange-rates.abstractapi.com/v1/live/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "base": base, "target": target}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_exchange_rates_live] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        is_ok, vmsg = _validate_required_fields(
            endpoint_name="exchange_rates_live",
            data=data,
            required={"base": str, "exchange_rates": dict},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_exchange_rates_live] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        # Ensure target is present in exchange_rates (best-effort)
        try:
            rates = data.get("exchange_rates", {}) if isinstance(data, dict) else {}
            if isinstance(rates, dict) and target not in rates:
                vmsg2 = f"exchange_rates_live: missing target rate for '{target}'"
                safe_log_error(logger, "[abstract_exchange_rates_live] Validation failed", exc_info=False, validation_message=vmsg2)
                return json.dumps({"status": "error", "message": vmsg2, "raw_response": data})
        except Exception:
            pass

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_exchange_rates_live] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Exchange rates failed: {str(e)}"})


@tool
def abstract_company_enrichment(
    runtime: ToolRuntime,
    domain: str,
    timeout: int = 30,
) -> str:
    """
    Company Enrichment API (AbstractAPI).

    Endpoint:
      https://companyenrichment.abstractapi.com/v2/

    Required key:
      COMPANY_ENRICHMENT_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_company_enrichment] Starting", domain=domain, timeout=timeout)
        if not domain or not isinstance(domain, str):
            return json.dumps({"status": "error", "message": "domain must be a non-empty string"})

        key = _get_api_key_from_runtime(runtime, "COMPANY_ENRICHMENT_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "COMPANY_ENRICHMENT_API_KEY not found in ToolRuntime"})

        url = "https://companyenrichment.abstractapi.com/v2/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "domain": domain}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_company_enrichment] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        is_ok, vmsg = _validate_required_fields(
            endpoint_name="company_enrichment",
            data=data,
            required={"domain": str},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_company_enrichment] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_company_enrichment] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Company enrichment failed: {str(e)}"})


@tool
def abstract_timezone_current_time(
    runtime: ToolRuntime,
    location: str,
    timeout: int = 30,
) -> str:
    """
    Timezone API (AbstractAPI) - current time for a location.

    Endpoint:
      https://timezone.abstractapi.com/v1/current_time/

    Required key:
      TIMEZONE_API_KEY
    """
    try:
        safe_log_info(logger, "[abstract_timezone_current_time] Starting", timeout=timeout)
        if not location or not isinstance(location, str):
            return json.dumps({"status": "error", "message": "location must be a non-empty string"})

        key = _get_api_key_from_runtime(runtime, "TIMEZONE_API_KEY")
        if not key:
            return json.dumps({"status": "error", "message": "TIMEZONE_API_KEY not found in ToolRuntime"})

        url = "https://timezone.abstractapi.com/v1/current_time/"
        ok, msg, data = _request_json(url=url, params={"api_key": key, "location": location}, timeout=timeout)
        if not ok:
            safe_log_error(logger, "[abstract_timezone_current_time] API error", exc_info=False, api_message=msg)
            return json.dumps({"status": "error", "message": msg, "raw_response": data})

        is_ok, vmsg = _validate_required_fields(
            endpoint_name="timezone_current_time",
            data=data,
            required={"datetime": str, "timezone_name": str},
        )
        if not is_ok:
            safe_log_error(logger, "[abstract_timezone_current_time] Validation failed", exc_info=False, validation_message=vmsg)
            return json.dumps({"status": "error", "message": vmsg, "raw_response": data})

        return json.dumps({"status": "success", "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abstract_timezone_current_time] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"Timezone lookup failed: {str(e)}"})


