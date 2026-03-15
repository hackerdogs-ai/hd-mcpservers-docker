"""
BeVigil OSINT Tool - LangChain Integration for Domain Intelligence Gathering

This module provides a LangChain-compatible tool for performing OSINT (Open Source
Intelligence) lookups using the BeVigil API. It is inspired by theHarvester's BeVigil
integration and provides domain subdomain discovery and URL enumeration capabilities.

The tool queries the BeVigil OSINT API to discover:
- Subdomains (hostnames) associated with a target domain
- Interesting URLs found during reconnaissance

Key Features:
- Automatic domain normalization (handles URLs, removes protocols)
- API key management via ToolRuntime environment variables
- Configurable timeout settings
- Comprehensive error handling and logging
- JSON-formatted responses suitable for LLM consumption

API Endpoints Used:
- https://osint.bevigil.com/api/<domain>/subdomains/ - Returns list of subdomains
- https://osint.bevigil.com/api/<domain>/urls/ - Returns list of discovered URLs

Authentication:
- Requires BEVIGIL_API_KEY to be configured in the tool runtime environment
- API key is passed via X-Access-Token header

Reference Implementation:
- theHarvester/theHarvester/discovery/bevigil.py

Example Usage:
    The tool is automatically registered as a LangChain tool via the @tool decorator.
    When called by an LLM agent, it expects:
    - domain: The target domain to investigate (e.g., "example.com")
    - runtime: ToolRuntime object containing API keys and configuration
    
    Returns a JSON string with:
    - status: "success" or "error"
    - hostnames: List of discovered subdomains
    - interesting_urls: List of discovered URLs
    - Metadata: Counts, timing, HTTP status codes
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info, mask_api_key


logger = setup_logger(__name__, log_file_path="logs/bevigil_tool.log")
_SESSION = requests.Session()

_DEFAULT_TIMEOUT_S = 20


def _json_ok(payload: Dict[str, Any]) -> str:
    """
    Format a successful response as a JSON string.
    
    Creates a standardized success response by wrapping the payload with a "status": "success"
    field. The response is formatted as pretty-printed JSON for readability.
    
    Args:
        payload: Dictionary containing the response data to include in the success response.
                 This will be merged with {"status": "success"}.
    
    Returns:
        A JSON-formatted string with status "success" and the provided payload data.
        The JSON is indented with 2 spaces for readability.
    
    Example:
        >>> _json_ok({"domain": "example.com", "hostnames": ["www.example.com"]})
        '{\\n  "status": "success",\\n  "domain": "example.com",\\n  "hostnames": ["www.example.com"]\\n}'
    """
    return json.dumps({"status": "success", **payload}, ensure_ascii=False, indent=2, default=str)


def _json_error(
    message: str,
    *,
    error_type: str = "error",
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format an error response as a JSON string.
    
    Creates a standardized error response with status "error", an error message,
    error type classification, and optional additional details. This provides
    consistent error formatting for LLM consumption.
    
    Args:
        message: Human-readable error message describing what went wrong.
        error_type: Classification of the error type (e.g., "validation_error",
                   "missing_key", "timeout", "request_error"). Defaults to "error".
        details: Optional dictionary containing additional error context such as
                domain, elapsed time, or other debugging information.
    
    Returns:
        A JSON-formatted string with status "error", the error message, error type,
        and optional details. The JSON is indented with 2 spaces for readability.
    
    Example:
        >>> _json_error("Missing API key", error_type="missing_key", 
        ...            details={"key": "BEVIGIL_API_KEY"})
        '{\\n  "status": "error",\\n  "message": "Missing API key",\\n  "error_type": "missing_key",\\n  "details": {"key": "BEVIGIL_API_KEY"}\\n}'
    """
    out: Dict[str, Any] = {"status": "error", "message": message, "error_type": error_type}
    if details:
        out["details"] = details
    return json.dumps(out, ensure_ascii=False, indent=2, default=str)


def _normalize_domain(domain: str) -> str:
    """
    Normalize a domain string for BeVigil API consumption.
    
    Processes the input domain to ensure it's in the format expected by the BeVigil API.
    This includes:
    - Converting to lowercase
    - Removing HTTP/HTTPS protocols if present
    - Removing trailing slashes
    - Truncating to 256 characters maximum
    
    The BeVigil API expects bare domains without protocols or paths, so this function
    ensures the domain is properly formatted before making API requests.
    
    Args:
        domain: The domain string to normalize. Can be a bare domain (e.g., "example.com"),
               a URL with protocol (e.g., "https://example.com"), or a URL with path
               (e.g., "https://example.com/path").
    
    Returns:
        A normalized domain string in lowercase, without protocol or trailing slashes,
        truncated to 256 characters if necessary. Returns empty string if input is None
        or empty after stripping.
    
    Example:
        >>> _normalize_domain("https://EXAMPLE.COM/path/")
        'example.com'
        >>> _normalize_domain("subdomain.example.com")
        'subdomain.example.com'
        >>> _normalize_domain("  HTTP://TEST.COM  ")
        'test.com'
    """
    d = (domain or "").strip().lower()
    if d.startswith("http://") or d.startswith("https://"):
        # BeVigil expects a bare domain
        d = d.split("://", 1)[1]
    d = d.strip("/").strip()
    if len(d) > 256:
        d = d[:256]
    return d


def _coerce_int(value: Any, default: int, *, min_v: int, max_v: int) -> int:
    """
    Safely convert a value to an integer with bounds checking.
    
    Attempts to convert the input value to an integer and ensures it falls within
    the specified minimum and maximum bounds. If conversion fails or the value
    is out of bounds, it is clamped to the valid range or the default is returned.
    
    This is useful for parsing configuration values (like timeouts) from environment
    variables or user input where the value might be invalid or out of range.
    
    Args:
        value: The value to convert to an integer. Can be any type that can be
              converted to int (string, float, int, etc.).
        default: The default value to return if conversion fails entirely.
        min_v: The minimum allowed value. Values below this will be clamped to min_v.
        max_v: The maximum allowed value. Values above this will be clamped to max_v.
    
    Returns:
        An integer value within the range [min_v, max_v]. If conversion fails,
        returns the default value. If conversion succeeds but value is out of bounds,
        returns the clamped value (min_v or max_v).
    
    Example:
        >>> _coerce_int("30", default=20, min_v=3, max_v=120)
        30
        >>> _coerce_int("200", default=20, min_v=3, max_v=120)
        120
        >>> _coerce_int("invalid", default=20, min_v=3, max_v=120)
        20
    """
    try:
        v = int(value)
        return max(min_v, min(max_v, v))
    except Exception:
        return default


def _get_runtime_env(runtime: ToolRuntime, key: str) -> Optional[str]:
    """
    Retrieve an environment variable value from the ToolRuntime state.
    
    Searches for the specified key in the runtime's environment variables dictionary.
    The function checks both instance-specific environment variables (nested under
    instance names) and top-level environment variables.
    
    This function is used to retrieve configuration values like timeouts that may
    be set per-instance or globally in the tool runtime configuration.
    
    Args:
        runtime: The ToolRuntime object containing the tool's runtime state and
                configuration. Must have a 'state' attribute with 'environment_variables'.
        key: The environment variable key to look up (e.g., "BEVIGIL_TIMEOUT").
    
    Returns:
        The value of the environment variable as a string if found, None otherwise.
        The function returns None if:
        - runtime is None or doesn't have a state attribute
        - environment_variables is not a dictionary
        - The key is not found in any location
    
    Note:
        The function checks instance-specific environment variables first (nested dicts),
        then falls back to top-level environment variables. This allows per-instance
        configuration while maintaining backward compatibility with global settings.
    """
    try:
        if not runtime or not getattr(runtime, "state", None):
            return None
        env_vars = runtime.state.get("environment_variables", {})
        if isinstance(env_vars, dict):
            for _, inst_env in env_vars.items():
                if isinstance(inst_env, dict) and inst_env.get(key):
                    return str(inst_env.get(key))
            if env_vars.get(key):
                return str(env_vars.get(key))
    except Exception:
        return None
    return None


def _get_api_key_from_runtime(runtime: ToolRuntime, key_name: str) -> Optional[str]:
    """
    Retrieve an API key from the ToolRuntime state using a two-tier lookup strategy.
    
    This function implements a secure API key retrieval mechanism that checks multiple
    locations in the runtime state. It uses a primary and secondary lookup strategy:
    
    Primary (instance-specific):
    - Checks runtime.state.environment_variables[<instance_name>][key_name]
    - Allows different API keys per tool instance
    
    Secondary (global):
    - Checks runtime.state.api_keys[key_name]
    - Provides a fallback for globally configured API keys
    
    The function logs when an API key is found (with masked value for security) to
    aid in debugging and audit trails.
    
    Args:
        runtime: The ToolRuntime object containing the tool's runtime state.
                Must have a 'state' attribute with environment_variables and/or api_keys.
        key_name: The name of the API key to retrieve (e.g., "BEVIGIL_API_KEY").
    
    Returns:
        The API key value as a string if found in either location, None otherwise.
        The function returns None if:
        - runtime is None or doesn't have a state attribute
        - The key is not found in either location
        - The state structure is invalid
    
    Note:
        API keys are logged with masking (only first/last few characters visible)
        for security purposes. The function prioritizes instance-specific keys over
        global keys to support multi-tenant scenarios.
    
    Example:
        If runtime.state contains:
        {
            "environment_variables": {
                "instance1": {"BEVIGIL_API_KEY": "abc123..."}
            },
            "api_keys": {"BEVIGIL_API_KEY": "fallback_key"}
        }
        
        The function will return "abc123..." (from instance1) and log the discovery.
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


def _request_json(url: str, *, headers: Dict[str, str], timeout_s: int) -> tuple[bool, str, Any, int]:
    """
    Make an HTTP GET request and return the response as structured data.
    
    Performs a GET request using a persistent session and returns a tuple indicating
    success/failure, message, parsed data, and HTTP status code. Handles various error
    conditions including timeouts, network errors, and HTTP error status codes.
    
    The function attempts to parse the response as JSON, but falls back to a dictionary
    containing the raw text if JSON parsing fails. This ensures the function always
    returns usable data even for non-JSON responses.
    
    Args:
        url: The full URL to request (e.g., "https://osint.bevigil.com/api/example.com/subdomains/").
        headers: Dictionary of HTTP headers to include in the request.
                Typically includes authentication headers like {"X-Access-Token": "..."}.
        timeout_s: Request timeout in seconds. The request will raise Timeout exception
                  if not completed within this time.
    
    Returns:
        A tuple of (success: bool, message: str, data: Any, status_code: int):
        - success: True if request succeeded (status < 400), False otherwise
        - message: Human-readable status message ("ok" for success, error description for failure)
        - data: Parsed JSON response as dict if successful, or {"raw_text": ...} if JSON parse fails,
               or None for network/timeout errors
        - status_code: HTTP status code (200-599) for HTTP responses, 0 for network/timeout errors
    
    Raises:
        This function catches all exceptions and returns them as error tuples, so it
        never raises exceptions. Network errors, timeouts, and HTTP errors are all
        converted to (False, error_message, None/error_data, status_code) tuples.
    
    Example:
        >>> ok, msg, data, status = _request_json(
        ...     "https://api.example.com/data",
        ...     headers={"Authorization": "Bearer token"},
        ...     timeout_s=20
        ... )
        >>> if ok:
        ...     print(f"Success: {data}")
        ... else:
        ...     print(f"Error {status}: {msg}")
    """
    try:
        resp = _SESSION.get(url, headers=headers, timeout=timeout_s)
        status = resp.status_code
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}
        if status >= 400:
            return False, f"HTTP {status}", data, status
        return True, "ok", data, status
    except requests.exceptions.Timeout as e:
        return False, f"timeout: {e}", None, 0
    except requests.exceptions.RequestException as e:
        return False, f"request_error: {e}", None, 0
    except Exception as e:
        return False, f"unexpected_error: {e}", None, 0


@tool
def bevigil_domain_osint(
    runtime: ToolRuntime,
    domain: str,
) -> str:
    """
    Perform OSINT (Open Source Intelligence) lookup for a domain using BeVigil API.
    
    This is the main tool function that queries the BeVigil OSINT API to discover
    subdomains and interesting URLs associated with a target domain. It is designed
    to be called by LLM agents as part of reconnaissance and threat intelligence
    gathering workflows.
    
    The function makes two parallel API calls:
    1. Subdomain discovery: Queries /api/<domain>/subdomains/ to find all known subdomains
    2. URL enumeration: Queries /api/<domain>/urls/ to find interesting URLs discovered
    
    Both calls are made with the same API key and timeout settings. The results are
    combined, deduplicated, and sorted before being returned in a structured JSON format.
    
    Args:
        runtime: ToolRuntime object containing the tool's runtime state. Must contain
                BEVIGIL_API_KEY in either:
                - runtime.state.environment_variables[<instance>]["BEVIGIL_API_KEY"]
                - runtime.state.api_keys["BEVIGIL_API_KEY"]
                Optional: BEVIGIL_TIMEOUT in environment_variables (default: 20 seconds).
        domain: The target domain to investigate. Can be:
               - Bare domain: "example.com"
               - URL with protocol: "https://example.com"
               - URL with path: "https://example.com/path"
               The function automatically normalizes the input to extract just the domain.
    
    Returns:
        A JSON-formatted string containing the OSINT results. On success, returns:
        {
            "status": "success",
            "domain": "normalized_domain",
            "hostnames": ["sub1.example.com", "sub2.example.com", ...],
            "interesting_urls": ["https://example.com/path1", ...],
            "hostname_count": 5,
            "interesting_url_count": 10,
            "elapsed_ms": 1234,
            "http": {
                "subdomains": {"ok": true, "message": "ok", "status_code": 200},
                "urls": {"ok": true, "message": "ok", "status_code": 200}
            }
        }
        
        On error, returns:
        {
            "status": "error",
            "message": "Error description",
            "error_type": "validation_error" | "missing_key" | "timeout" | "request_error" | "unexpected_error",
            "details": {...}  // Optional additional context
        }
    
    Error Types:
        - validation_error: Domain input is invalid or empty
        - missing_key: BEVIGIL_API_KEY is not configured in runtime
        - timeout: API request exceeded timeout (configurable via BEVIGIL_TIMEOUT)
        - request_error: Network or HTTP error occurred
        - unexpected_error: Unexpected exception during processing
    
    Example Usage:
        When called by an LLM agent:
        ```
        result = bevigil_domain_osint(
            runtime=tool_runtime,
            domain="example.com"
        )
        # Returns JSON string with discovered subdomains and URLs
        ```
    
    Note:
        - The function uses a persistent HTTP session for connection pooling
        - API key is passed via X-Access-Token header
        - Timeout is configurable (3-120 seconds) via BEVIGIL_TIMEOUT env var
        - Results are deduplicated and sorted alphabetically
        - All operations are logged for audit and debugging purposes
        - The function handles partial failures gracefully (one endpoint may fail while the other succeeds)
    
    Reference:
        Inspired by theHarvester's BeVigil integration:
        https://github.com/laramies/theHarvester/blob/master/theHarvester/discovery/bevigil.py
    """
    started = time.time()
    d = _normalize_domain(domain)
    if not d:
        return _json_error("domain must be a non-empty string", error_type="validation_error")

    timeout_s = _coerce_int(_get_runtime_env(runtime, "BEVIGIL_TIMEOUT"), _DEFAULT_TIMEOUT_S, min_v=3, max_v=120)
    api_key = _get_api_key_from_runtime(runtime, "BEVIGIL_API_KEY")
    if not api_key:
        return _json_error("Missing BEVIGIL_API_KEY", error_type="missing_key", details={"key": "BEVIGIL_API_KEY"})

    try:
        safe_log_info(logger, "[bevigil_domain_osint] Starting", domain=d, timeout_s=timeout_s)

        headers = {"X-Access-Token": api_key}
        subdomain_endpoint = f"https://osint.bevigil.com/api/{d}/subdomains/"
        url_endpoint = f"https://osint.bevigil.com/api/{d}/urls/"

        ok1, msg1, data1, status1 = _request_json(subdomain_endpoint, headers=headers, timeout_s=timeout_s)
        ok2, msg2, data2, status2 = _request_json(url_endpoint, headers=headers, timeout_s=timeout_s)

        hostnames: List[str] = []
        interesting_urls: List[str] = []

        if ok1 and isinstance(data1, dict) and isinstance(data1.get("subdomains"), list):
            hostnames = sorted({str(x).strip().lower() for x in data1.get("subdomains", []) if x})
        if ok2 and isinstance(data2, dict) and isinstance(data2.get("urls"), list):
            interesting_urls = sorted({str(x).strip() for x in data2.get("urls", []) if x})

        elapsed_ms = int((time.time() - started) * 1000)
        safe_log_info(
            logger,
            "[bevigil_domain_osint] Completed",
            domain=d,
            elapsed_ms=elapsed_ms,
            hostnames_count=len(hostnames),
            interesting_urls_count=len(interesting_urls),
            subdomains_status=status1,
            urls_status=status2,
        )

        return _json_ok(
            {
                "domain": d,
                "hostnames": hostnames,
                "interesting_urls": interesting_urls,
                "hostname_count": len(hostnames),
                "interesting_url_count": len(interesting_urls),
                "elapsed_ms": elapsed_ms,
                "http": {
                    "subdomains": {"ok": ok1, "message": msg1, "status_code": status1},
                    "urls": {"ok": ok2, "message": msg2, "status_code": status2},
                },
            }
        )
    except Exception as e:
        elapsed_ms = int((time.time() - started) * 1000)
        safe_log_error(logger, "[bevigil_domain_osint] Unexpected error", exc_info=True, error=str(e), domain=d)
        return _json_error(
            f"BeVigil lookup failed: {e}",
            error_type="unexpected_error",
            details={"domain": d, "elapsed_ms": elapsed_ms},
        )


