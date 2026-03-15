"""
Browserless Tool for LangChain Agents

Web scraping and browser automation using Browserless REST API service.
This tool provides comprehensive browser capabilities including content extraction,
screenshots, PDF generation, JavaScript execution, and bot detection bypass.

Reference: https://docs.browserless.io/rest-apis/intro

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following environment variables/API keys to be configured:

1. BROWSERLESS_URL (Required)
   - Description: Base URL for the Browserless API service
   - Example: "http://localhost:3000" or "https://browserless.example.com"
   - Retrieval Priority (in order):
     a) runtime.state.environment_variables[<tool_instance>]["BROWSERLESS_URL"]
        - Searches through all tool instances in environment_variables dict
        - Preferred method: ensures per-tool-instance configuration
     b) runtime.state.environment_variables[<tool_instance>]["BROWSERLESS_BASE_URL"]
        - Alternative key name (also searched)
     c) os.getenv("BROWSERLESS_URL") [FALLBACK - with warning log]
        - Only used if not found in runtime state
        - Default: "http://localhost:3000"
        - WARNING logged when fallback is used

2. BROWSERLESS_API_KEY or BROWSERLESS_TOKEN (Required)
   - Description: API token for authenticating with Browserless service
   - Retrieval Priority (in order):
     a) runtime.state.environment_variables[<tool_instance>]["BROWSERLESS_API_KEY"]
        - Searches through all tool instances in environment_variables dict
        - Preferred method: ensures per-tool-instance configuration
     b) runtime.state.environment_variables[<tool_instance>]["BROWSERLESS_TOKEN"]
        - Alternative key name (also searched)
     c) runtime.state.api_keys["BROWSERLESS_API_KEY"]
        - Secondary source: checks api_keys dict in runtime state
     d) runtime.state.api_keys["API_KEY"] or runtime.state.api_keys["api_key"]
        - Generic API key fallback in api_keys dict
     e) os.getenv("BROWSERLESS_API_KEY") or os.getenv("BROWSERLESS_TOKEN") [FALLBACK - with warning log]
        - Only used if not found in runtime state
        - WARNING logged when fallback is used

Configuration Example:
    agent_state = {
        "environment_variables": {
            "browserless_instance_1": {
                "BROWSERLESS_URL": "https://browserless.example.com",
                "BROWSERLESS_API_KEY": "your_api_key_here"
            }
        },
        "api_keys": {
            # Alternative: can also use api_keys dict
            "BROWSERLESS_API_KEY": "your_api_key_here"
        }
    }

Security Notes:
- API keys are automatically masked in logs using mask_api_key()
- Never log raw API keys or tokens
- Prefer runtime.state.environment_variables over os.getenv() for security

================================================================================
Key Features:
================================================================================
- Content extraction from web pages
- Screenshot capture
- PDF generation
- JavaScript function execution
- Structured data scraping
- Bot detection bypass (/unblock)
- Performance metrics
- File downloads
- Session exports

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.browserless_langchain import (
        browserless_content,
        browserless_scrape,
        browserless_screenshot,
        browserless_pdf
    )
    
    agent = create_agent(
        model=llm,
        tools=[browserless_content, browserless_scrape, browserless_screenshot, browserless_pdf],
        system_prompt="You are a web scraping specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Extract content from https://example.com"}],
        "user_id": "analyst_001",
        "environment_variables": {
            "browserless_instance": {
                "BROWSERLESS_URL": "https://browserless.example.com",
                "BROWSERLESS_API_KEY": "your_api_key_here"
            }
        }
    })
"""

import os
import json
import base64
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal, Tuple
from dotenv import load_dotenv
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key

# Load environment variables - same pattern as test_utils.py
# This will search from current working directory and parent directories
load_dotenv(override=True)

logger = setup_logger(__name__, log_file_path="logs/browserless_tool.log")

# Reuse connections where possible (especially helpful under Celery worker load)
_BROWSERLESS_SESSION = requests.Session()


class BrowserlessSecurityAgentState(AgentState):
    """Extended agent state for Browserless operations."""
    user_id: str = ""


def _get_browserless_config_from_runtime(runtime: ToolRuntime) -> Tuple[Optional[str], Optional[str]]:
    """
    Get Browserless URL and API token from runtime state environment variables.
    
    Standard approach: Search through all tool instances in environment_variables
    to find the one containing BROWSERLESS_URL and BROWSERLESS_API_KEY.
    
    This function implements the PRIMARY method for configuration retrieval:
    1. Searches runtime.state.environment_variables dictionary
    2. Iterates through all tool instances (e.g., "browserless_instance_1", "browserless_instance_2")
    3. Looks for BROWSERLESS_URL (or BROWSERLESS_BASE_URL as alternative)
    4. Looks for BROWSERLESS_API_KEY (or BROWSERLESS_TOKEN as alternative)
    5. Returns first matching instance with both URL and token
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Expected structure:
            runtime.state.environment_variables = {
                "browserless_instance_1": {
                    "BROWSERLESS_URL": "https://browserless.example.com",
                    "BROWSERLESS_API_KEY": "your_api_key"
                }
            }
    
    Returns:
        Tuple of (url, token) or (None, None) if not found.
        - url: Browserless base URL (trailing slashes removed)
        - token: Browserless API token/key
    """
    safe_log_debug(logger, "[_get_browserless_config_from_runtime] Starting config retrieval from runtime state")
    
    # Get environment_variables dict from runtime state
    # This dict contains per-tool-instance configurations
    env_vars_dict = runtime.state.get("environment_variables", {})
    instances_count = len(env_vars_dict) if isinstance(env_vars_dict, dict) else 0
    safe_log_debug(logger, "[_get_browserless_config_from_runtime] Environment variables dict", 
                   instances_count=instances_count, 
                   instance_names=list(env_vars_dict.keys()) if isinstance(env_vars_dict, dict) else [])
    
    # Search through all tool instances to find Browserless config
    # Each instance represents a separate tool configuration (allows multiple Browserless instances)
    for instance_name, env_vars in env_vars_dict.items():
        if isinstance(env_vars, dict):
            # Try multiple key names for URL (BROWSERLESS_URL or BROWSERLESS_BASE_URL)
            url = env_vars.get("BROWSERLESS_URL") or env_vars.get("BROWSERLESS_BASE_URL")
            # Try multiple key names for token (BROWSERLESS_API_KEY or BROWSERLESS_TOKEN)
            token = env_vars.get("BROWSERLESS_API_KEY") or env_vars.get("BROWSERLESS_TOKEN")
            
            # Return first instance that has both URL and token configured
            if url and token:
                masked_token = mask_api_key(token)
                safe_log_info(logger, "[_get_browserless_config_from_runtime] Found Browserless config", 
                            instance_name=instance_name, 
                            url=url, 
                            token_masked=masked_token)
                return (url.rstrip("/"), token)
            else:
                # Log which config is missing for debugging
                safe_log_debug(logger, "[_get_browserless_config_from_runtime] Instance missing config", 
                             instance_name=instance_name, 
                             has_url=bool(url), 
                             has_token=bool(token))
    
    # No matching instance found - will trigger fallback to os.getenv() in calling function
    safe_log_error(logger, "[_get_browserless_config_from_runtime] Browserless config not found in any tool instance", 
                  instances_searched=instances_count)
    return (None, None)


def _get_browserless_url(runtime: ToolRuntime) -> str:
    """
    Get Browserless API base URL from runtime state or environment variable (fallback).
    
    Retrieval Priority:
    1. PRIMARY: runtime.state.environment_variables[<instance>]["BROWSERLESS_URL"]
    2. FALLBACK: os.getenv("BROWSERLESS_URL") with WARNING log
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
    
    Returns:
        Browserless base URL string (protocol + hostname + port, no path/query/fragment).
        Example: "https://browserless.example.com" or "http://localhost:3000"
    """
    from urllib.parse import urlparse, urlunparse
    
    safe_log_debug(logger, "[_get_browserless_url] Starting URL retrieval")
    
    # PRIMARY METHOD: Try to get from runtime state environment_variables
    # This searches through all tool instances for BROWSERLESS_URL
    url, _ = _get_browserless_config_from_runtime(runtime)
    
    if url:
        # Successfully found URL in runtime state - preferred method
        safe_log_info(logger, "[_get_browserless_url] Using URL from runtime state", url=url)
        # Parse and normalize URL (remove path, query, fragment - keep only base)
        parsed = urlparse(url)
        base_url = urlunparse((
            parsed.scheme,    # http or https
            parsed.netloc,    # hostname:port
            "", "", "", ""    # No path, params, query, fragment
        ))
        return base_url.rstrip("/")
    
    # FALLBACK METHOD: Use os.getenv() - this is NOT preferred
    # Log warning to indicate fallback is being used
    fallback_url = os.getenv("BROWSERLESS_URL", "http://localhost:3000")
    safe_log_error(logger, "[_get_browserless_url] WARNING: Using fallback URL from os.getenv()", 
                   fallback_url=fallback_url,
                   note="BROWSERLESS_URL should be provided via runtime.state.environment_variables")
    
    # Parse and normalize fallback URL
    parsed = urlparse(fallback_url)
    base_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        "", "", "", ""
    ))
    return base_url.rstrip("/")


def _get_browserless_token(runtime: ToolRuntime) -> Optional[str]:
    """
    Get Browserless API token from runtime state or environment variable (fallback).
    
    Retrieval Priority (in order):
    1. PRIMARY: runtime.state.environment_variables[<instance>]["BROWSERLESS_API_KEY"]
    2. SECONDARY: runtime.state.api_keys["BROWSERLESS_API_KEY"]
    3. SECONDARY: runtime.state.api_keys["API_KEY"] or ["api_key"]
    4. FALLBACK: os.getenv("BROWSERLESS_API_KEY") or os.getenv("BROWSERLESS_TOKEN") with WARNING log
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
    
    Returns:
        Browserless API token string or None if not found.
        Token is automatically masked in logs for security.
    """
    safe_log_debug(logger, "[_get_browserless_token] Starting token retrieval")
    
    # PRIMARY METHOD: Try to get from runtime state environment_variables
    # This searches through all tool instances for BROWSERLESS_API_KEY or BROWSERLESS_TOKEN
    _, token = _get_browserless_config_from_runtime(runtime)
    
    if token:
        # Successfully found token in runtime state - preferred method
        masked_token = mask_api_key(token)
        safe_log_info(logger, "[_get_browserless_token] Using token from runtime state", token_masked=masked_token)
        return token
    
    # SECONDARY METHOD: Try api_keys dict in runtime state
    # This is an alternative location for API keys (used by some tools like VirusTotal)
    if runtime and runtime.state:
        api_keys_dict = runtime.state.get("api_keys", {})
        if isinstance(api_keys_dict, dict):
            # Try specific Browserless key first
            token = api_keys_dict.get("BROWSERLESS_API_KEY")
            # Fallback to generic API_KEY or api_key
            if not token:
                token = api_keys_dict.get("API_KEY") or api_keys_dict.get("api_key")
            if token:
                masked_token = mask_api_key(token)
                safe_log_info(logger, "[_get_browserless_token] Using token from api_keys dict", token_masked=masked_token)
                return token
    
    # FALLBACK METHOD: Use os.getenv() - this is NOT preferred
    # Log warning to indicate fallback is being used
    fallback_token = os.getenv("BROWSERLESS_API_KEY") or os.getenv("BROWSERLESS_TOKEN")
    if fallback_token:
        masked_token = mask_api_key(fallback_token)
        safe_log_error(logger, "[_get_browserless_token] WARNING: Using fallback token from os.getenv()", 
                       token_masked=masked_token,
                       note="BROWSERLESS_API_KEY should be provided via runtime.state.environment_variables or api_keys")
        return fallback_token
    
    # No token found in any location
    safe_log_error(logger, "[_get_browserless_token] No token found in runtime state or environment", 
                   note="BROWSERLESS_API_KEY must be provided via runtime.state")
    return None


def _build_headers() -> Dict[str, str]:
    """Build HTTP headers for Browserless API requests."""
    headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
    return headers


def _get_float_env(name: str, default: float) -> float:
    """Parse a float env var safely with fallback."""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(str(raw).strip())
    except Exception:
        return default


def _get_int_env(name: str, default: int) -> int:
    """Parse an int env var safely with fallback."""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except Exception:
        return default


def _make_request(endpoint: str, payload: Dict[str, Any], runtime: ToolRuntime, timeout: int = 30) -> Dict[str, Any]:
    """
    Make HTTP request to Browserless API.
    
    Args:
        endpoint: API endpoint path (e.g., "/content", "/scrape").
        payload: Request payload dictionary.
        runtime: ToolRuntime instance providing access to agent state.
        timeout: Request timeout in seconds (default: 30).
    
    Returns:
        Response data as dictionary.
    """
    safe_log_info(logger, "[_make_request] Starting request", endpoint=endpoint, timeout=timeout)
    
    base_url = _get_browserless_url(runtime)
    api_token = _get_browserless_token(runtime)
    
    # Build full endpoint URL
    # Endpoint should start with / (e.g., /content, /scrape)
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    
    url = f"{base_url}{endpoint}"
    
    # Add token as query parameter (Browserless REST API uses ?token=...)
    if api_token:
        if "?" in url:
            url = f"{url}&token={api_token}"
        else:
            url = f"{url}?token={api_token}"
    
    headers = _build_headers()
    
    masked_token = mask_api_key(api_token) if api_token else None
    safe_log_info(logger, "[_make_request] Request details", 
                 url=url, 
                 endpoint=endpoint, 
                 has_token=bool(api_token),
                 token_masked=masked_token,
                 payload_keys=list(payload.keys()) if isinstance(payload, dict) else [])

    # Requests timeout semantics:
    # - timeout=float applies to both connect+read, which is too strict for heavy pages.
    # - Use timeout=(connect, read) so we can keep connect tight while allowing longer reads.
    connect_timeout = _get_float_env("BROWSERLESS_CONNECT_TIMEOUT_SECS", 10.0)
    # Add a small buffer to the read timeout for JSON decode / response overhead.
    read_timeout = float(timeout) + _get_float_env("BROWSERLESS_READ_TIMEOUT_BUFFER_SECS", 5.0)
    request_timeout = (connect_timeout, read_timeout)

    max_retries = _get_int_env("BROWSERLESS_MAX_RETRIES", 2)
    backoff_base = _get_float_env("BROWSERLESS_RETRY_BACKOFF_SECS", 0.8)

    last_exc: Optional[Exception] = None
    for attempt in range(0, max_retries + 1):
        started = time.monotonic()
        try:
            response = _BROWSERLESS_SESSION.post(url, json=payload, headers=headers, timeout=request_timeout)

            elapsed_s = round(time.monotonic() - started, 3)
            safe_log_debug(
                logger,
                "[_make_request] Response received",
                status_code=response.status_code,
                elapsed_s=elapsed_s,
                content_length=len(response.content) if response.content else 0,
            )

            if response.status_code == 403:
                error_msg = "API token is invalid or missing"
                safe_log_error(
                    logger,
                    f"[_make_request] {error_msg}",
                    status_code=403,
                    token_masked=masked_token,
                )
                raise ValueError(error_msg)

            response.raise_for_status()

            # Handle empty responses or non-JSON responses
            if not response.content:
                safe_log_debug(logger, "[_make_request] Empty response content", elapsed_s=elapsed_s)
                return {}

            try:
                result = response.json()
                safe_log_info(
                    logger,
                    "[_make_request] Request successful",
                    status_code=response.status_code,
                    elapsed_s=elapsed_s,
                    result_type=type(result).__name__,
                )
                return result
            except (ValueError, requests.exceptions.JSONDecodeError):
                # If response is not JSON:
                # - For binary payloads (image/pdf), return base64 of bytes (safe for JSON transport)
                # - Otherwise, fall back to text
                content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
                if content_type.startswith("image/") or content_type == "application/pdf":
                    b64 = base64.b64encode(response.content).decode("utf-8")
                    safe_log_debug(
                        logger,
                        "[_make_request] Non-JSON binary response, returning base64",
                        content_type=content_type,
                        bytes_len=len(response.content) if response.content else 0,
                        b64_len=len(b64),
                        elapsed_s=elapsed_s,
                    )
                    return {"base64": b64, "mime_type": content_type}

                safe_log_debug(
                    logger,
                    "[_make_request] Non-JSON response, returning as text",
                    content_type=content_type,
                    text_length=len(response.text),
                    elapsed_s=elapsed_s,
                )
                return {"raw_text": response.text, "mime_type": content_type or "text/plain"}

        except requests.exceptions.Timeout as e:
            last_exc = e
            elapsed_s = round(time.monotonic() - started, 3)
            is_last = attempt >= max_retries
            error_msg = (
                f"Request timeout after {timeout} seconds "
                f"(attempt {attempt + 1}/{max_retries + 1}, elapsed={elapsed_s}s, "
                f"connect_timeout={connect_timeout}s, read_timeout={read_timeout}s)"
            )
            safe_log_error(
                logger,
                f"[_make_request] {error_msg}",
                endpoint=endpoint,
                timeout=timeout,
                attempt=attempt + 1,
                max_retries=max_retries,
                elapsed_s=elapsed_s,
            )
            if is_last:
                raise TimeoutError(error_msg) from e
            time.sleep(backoff_base * (2 ** attempt))

        except requests.exceptions.HTTPError as e:
            last_exc = e
            if hasattr(e, "response") and e.response is not None:
                error_text = e.response.text[:200] if e.response.text else "No error details"
                error_msg = f"HTTP error {e.response.status_code}: {error_text}"
            else:
                error_msg = f"HTTP error: {str(e)}"
            safe_log_error(
                logger,
                f"[_make_request] {error_msg}",
                endpoint=endpoint,
                status_code=e.response.status_code if hasattr(e, "response") and e.response else None,
            )
            raise ValueError(error_msg) from e

        except requests.exceptions.RequestException as e:
            last_exc = e
            error_msg = f"Connection error: {str(e)}"
            safe_log_error(logger, f"[_make_request] {error_msg}", endpoint=endpoint, exc_info=True)
            raise ConnectionError(error_msg) from e

    # Should be unreachable, but keep a safe guard
    raise ConnectionError(f"Browserless request failed unexpectedly: {str(last_exc)}")


@tool
def browserless_content(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Extract content from a web page using Browserless /content endpoint.
    
    This tool fetches HTML content from a URL and returns it as text.
    Perfect for simple content extraction without JavaScript execution.
    
    Configuration Requirements:
        - BROWSERLESS_URL: Base URL for Browserless API
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_URL"]
          Fallback: os.getenv("BROWSERLESS_URL") (with warning)
        - BROWSERLESS_API_KEY: API token for authentication
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_API_KEY"]
          Fallback: runtime.state.api_keys["BROWSERLESS_API_KEY"] or os.getenv() (with warning)
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Must contain environment_variables or api_keys with Browserless configuration.
        url: The URL to extract content from. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for before extracting content.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with extracted content containing:
        - status: "success" or "error"
        - url: The requested URL
        - endpoint: "/content"
        - raw_response: Raw API response from Browserless
        - user_id: User ID from runtime state
        - note: Processing notes
    
    Raises:
        ValueError: If URL is invalid or API configuration is missing
        TimeoutError: If request exceeds timeout
        ConnectionError: If connection to Browserless service fails
    """
    try:
        safe_log_info(logger, f"[browserless_content] Starting", url=url)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip()}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/content", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/content",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_content] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_content: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_scrape(
    runtime: ToolRuntime,
    url: str,
    selector: Optional[str] = None,
    wait_for: Optional[str] = None,
    timeout: int = 60,
    **kwargs: Any
) -> str:
    """
    Scrape structured data from a web page using Browserless /scrape endpoint.
    
    This tool extracts structured data from web pages using CSS selectors.
    Returns JSON data matching the specified selectors.
    
    Configuration Requirements:
        - BROWSERLESS_URL: Base URL for Browserless API
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_URL"]
          Fallback: os.getenv("BROWSERLESS_URL") (with warning)
        - BROWSERLESS_API_KEY: API token for authentication
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_API_KEY"]
          Fallback: runtime.state.api_keys["BROWSERLESS_API_KEY"] or os.getenv() (with warning)
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Must contain environment_variables or api_keys with Browserless configuration.
        url: The URL to scrape. Must include protocol (http:// or https://).
        selector: Optional CSS selector to extract specific elements.
            Can be comma-separated (e.g., "h1, h2, h3") for multiple selectors.
        wait_for: Optional CSS selector to wait for before scraping.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with scraped data containing:
        - status: "success" or "error"
        - url: The requested URL
        - endpoint: "/scrape"
        - raw_response: Raw API response from Browserless with extracted elements
        - user_id: User ID from runtime state
        - note: Processing notes
    
    Raises:
        ValueError: If URL is invalid or API configuration is missing
        TimeoutError: If request exceeds timeout
        ConnectionError: If connection to Browserless service fails
    """
    try:
        safe_log_info(logger, f"[browserless_scrape] Starting", url=url, selector=selector)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip()}
        # Browserless API expects "elements" array, not "selector" string
        if selector:
            # Convert selector string to elements array format
            # e.g., "h1, h2, h3" -> [{"selector": "h1"}, {"selector": "h2"}, {"selector": "h3"}]
            selectors = [s.strip() for s in selector.split(",")]
            payload["elements"] = [{"selector": s} for s in selectors if s]
        if wait_for:
            payload["waitFor"] = wait_for

        # Browserless-side navigation settings (prevents server-side default timeouts on heavy pages)
        # See: https://docs.browserless.io/rest-apis/scrape
        # Allow caller overrides via kwargs; otherwise, set reasonable defaults.
        wait_until = kwargs.get("wait_until") or kwargs.get("waitUntil") or "networkidle2"
        goto_timeout_ms = kwargs.get("goto_timeout_ms") or kwargs.get("gotoTimeoutMs")
        if goto_timeout_ms is None:
            # Align Browserless navigation timeout with requested tool timeout.
            goto_timeout_ms = int(max(5, int(timeout)) * 1000)
        payload["gotoOptions"] = {"timeout": int(goto_timeout_ms), "waitUntil": str(wait_until)}
        
        result = _make_request("/scrape", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/scrape",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_scrape] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_scrape: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_screenshot(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    full_page: bool = False,
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Capture a screenshot of a web page using Browserless /screenshot endpoint.
    
    This tool takes a screenshot of the specified URL and returns it as base64-encoded image.
    
    Configuration Requirements:
        - BROWSERLESS_URL: Base URL for Browserless API
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_URL"]
          Fallback: os.getenv("BROWSERLESS_URL") (with warning)
        - BROWSERLESS_API_KEY: API token for authentication
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_API_KEY"]
          Fallback: runtime.state.api_keys["BROWSERLESS_API_KEY"] or os.getenv() (with warning)
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Must contain environment_variables or api_keys with Browserless configuration.
        url: The URL to screenshot. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for before taking screenshot.
        full_page: If True, capture full page screenshot (default: False).
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with base64-encoded screenshot containing:
        - status: "success" or "error"
        - url: The requested URL
        - endpoint: "/screenshot"
        - raw_response: Raw API response from Browserless with base64 image data
        - user_id: User ID from runtime state
        - note: Processing notes
    
    Raises:
        ValueError: If URL is invalid or API configuration is missing
        TimeoutError: If request exceeds timeout
        ConnectionError: If connection to Browserless service fails
    """
    try:
        safe_log_info(logger, f"[browserless_screenshot] Starting", url=url, full_page=full_page)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip(), "options": {"fullPage": full_page}}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/screenshot", payload, runtime, timeout)

        # Normalize screenshot payload for visualization:
        # Browserless may return JSON with base64, or plain base64 as text. Store at a stable key.
        screenshot_b64 = None
        if isinstance(result, dict):
            # Common patterns: { "raw_text": "<base64>" } or { "data": "<base64>" } or similar
            for k in ["base64", "data", "content", "raw_text", "image", "screenshot"]:
                v = result.get(k)
                if isinstance(v, str) and v.strip():
                    screenshot_b64 = v.strip()
                    break
        elif isinstance(result, str) and result.strip():
            screenshot_b64 = result.strip()

        # Strip data URL prefix if present
        if isinstance(screenshot_b64, str) and screenshot_b64.startswith("data:") and "," in screenshot_b64:
            screenshot_b64 = screenshot_b64.split(",", 1)[1].strip()
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/screenshot",
            "raw_response": result,
            "image_base64": screenshot_b64,
            "mime_type": "image/png",
            "user_id": runtime.state.get("user_id", ""),
            "note": "Includes image_base64 for UI visualization (VISUALIZATION=image). raw_response preserved verbatim."
        }
        
        safe_log_info(logger, f"[browserless_screenshot] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_screenshot: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_pdf(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    format: str = "A4",
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Generate a PDF from a web page using Browserless /pdf endpoint.
    
    This tool converts a web page to PDF format and returns it as base64-encoded data.
    
    Configuration Requirements:
        - BROWSERLESS_URL: Base URL for Browserless API
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_URL"]
          Fallback: os.getenv("BROWSERLESS_URL") (with warning)
        - BROWSERLESS_API_KEY: API token for authentication
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_API_KEY"]
          Fallback: runtime.state.api_keys["BROWSERLESS_API_KEY"] or os.getenv() (with warning)
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Must contain environment_variables or api_keys with Browserless configuration.
        url: The URL to convert to PDF. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for before generating PDF.
        format: PDF format (default: "A4"). Options: "A4", "Letter", etc.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with base64-encoded PDF containing:
        - status: "success" or "error"
        - url: The requested URL
        - endpoint: "/pdf"
        - raw_response: Raw API response from Browserless with base64 PDF data
        - user_id: User ID from runtime state
        - note: Processing notes
    
    Raises:
        ValueError: If URL is invalid or API configuration is missing
        TimeoutError: If request exceeds timeout
        ConnectionError: If connection to Browserless service fails
    """
    try:
        safe_log_info(logger, f"[browserless_pdf] Starting", url=url, format=format)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip(), "options": {"format": format}}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/pdf", payload, runtime, timeout)

        # Normalize PDF payload for visualization:
        pdf_b64 = None
        if isinstance(result, dict):
            for k in ["base64", "data", "content", "raw_text", "pdf", "document"]:
                v = result.get(k)
                if isinstance(v, str) and v.strip():
                    pdf_b64 = v.strip()
                    break
        elif isinstance(result, str) and result.strip():
            pdf_b64 = result.strip()

        # Strip data URL prefix if present
        if isinstance(pdf_b64, str) and pdf_b64.startswith("data:") and "," in pdf_b64:
            pdf_b64 = pdf_b64.split(",", 1)[1].strip()
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/pdf",
            "raw_response": result,
            "pdf_base64": pdf_b64,
            "mime_type": "application/pdf",
            "user_id": runtime.state.get("user_id", ""),
            "note": "Includes pdf_base64 for UI visualization (VISUALIZATION=pdf). raw_response preserved verbatim."
        }
        
        safe_log_info(logger, f"[browserless_pdf] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_pdf: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_function(
    runtime: ToolRuntime,
    url: str,
    function: str,
    wait_for: Optional[str] = None,
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Execute a JavaScript function on a web page using Browserless /function endpoint.
    
    This tool allows you to run custom JavaScript code on a page and return the result.
    
    Configuration Requirements:
        - BROWSERLESS_URL: Base URL for Browserless API
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_URL"]
          Fallback: os.getenv("BROWSERLESS_URL") (with warning)
        - BROWSERLESS_API_KEY: API token for authentication
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_API_KEY"]
          Fallback: runtime.state.api_keys["BROWSERLESS_API_KEY"] or os.getenv() (with warning)
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Must contain environment_variables or api_keys with Browserless configuration.
        url: The URL to execute function on. Must include protocol (http:// or https://).
        function: JavaScript function code to execute. Should return a value.
            Example: "() => document.title" or "() => { return { title: document.title, links: Array.from(document.links).map(l => l.href) }; }"
        wait_for: Optional CSS selector to wait for before executing function.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with function execution result containing:
        - status: "success" or "error"
        - url: The requested URL
        - endpoint: "/function"
        - raw_response: Raw API response from Browserless with function result
        - user_id: User ID from runtime state
        - note: Processing notes
    
    Raises:
        ValueError: If URL is invalid, function is missing, or API configuration is missing
        TimeoutError: If request exceeds timeout
        ConnectionError: If connection to Browserless service fails
    """
    try:
        safe_log_info(logger, f"[browserless_function] Starting", url=url)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not function:
            error_msg = "function parameter is required"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip(), "function": function}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/function", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/function",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_function] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_function: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_unblock(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    timeout: int = 60,
    **kwargs: Any
) -> str:
    """
    Bypass bot detection and unblock a website using Browserless /unblock endpoint.
    
    This tool uses advanced techniques to bypass Cloudflare and other bot detection systems.
    Use this when regular scraping fails due to bot detection.
    
    Configuration Requirements:
        - BROWSERLESS_URL: Base URL for Browserless API
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_URL"]
          Fallback: os.getenv("BROWSERLESS_URL") (with warning)
        - BROWSERLESS_API_KEY: API token for authentication
          Source: runtime.state.environment_variables[<instance>]["BROWSERLESS_API_KEY"]
          Fallback: runtime.state.api_keys["BROWSERLESS_API_KEY"] or os.getenv() (with warning)
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Must contain environment_variables or api_keys with Browserless configuration.
        url: The URL to unblock. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for after unblocking.
        timeout: Maximum time to wait in seconds (default: 60, longer for unblock operations).
    
    Returns:
        JSON string with unblocked content containing:
        - status: "success" or "error"
        - url: The requested URL
        - endpoint: "/unblock"
        - raw_response: Raw API response from Browserless with unblocked content
        - user_id: User ID from runtime state
        - note: Processing notes
    
    Raises:
        ValueError: If URL is invalid or API configuration is missing
        TimeoutError: If request exceeds timeout
        ConnectionError: If connection to Browserless service fails
    
    Note:
        This endpoint may take longer than regular endpoints due to bot detection bypass
        mechanisms. The default timeout is set to 60 seconds to accommodate this.
    """
    try:
        safe_log_info(logger, f"[browserless_unblock] Starting", url=url)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip()}
        if wait_for:
            payload["waitFor"] = wait_for
        
        try:
            result = _make_request("/unblock", payload, runtime, timeout)
        except ValueError as e:
            # Common case in self-hosted Browserless deployments:
            # /unblock isn't available (it's present in certain Browserless offerings / configs),
            # so the API returns 404 Not Found.
            msg = str(e)
            if "HTTP error 404" in msg or "404" in msg:
                base_url = _get_browserless_url(runtime)
                error_msg = (
                    "Browserless returned 404 for /unblock. This usually means your Browserless instance "
                    "does not support the /unblock API.\n\n"
                    f"- Browserless base_url: {base_url}\n"
                    "- Fix: point BROWSERLESS_URL to a Browserless deployment that supports /unblock "
                    "(or enable that feature on your Browserless service).\n"
                    "- Workaround: use browserless_content or browserless_scrape instead."
                )
                safe_log_error(logger, f"[browserless_unblock] {error_msg}", url=url)
                return json.dumps({"status": "error", "message": error_msg})
            raise
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/unblock",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_unblock] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_unblock: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})

