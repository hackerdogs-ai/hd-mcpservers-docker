"""
AlienVault OTX (Open Threat Exchange) Threat Intelligence Tools for LangChain Agents

This module provides LangChain tools for querying AlienVault OTX's threat intelligence API.
All tools use ToolRuntime to securely access API keys from agent state, following
LangChain v1.0 best practices for tools with state access.

Reference: https://docs.langchain.com/oss/python/langchain/tools

Key Features:
- Secure API key management via ToolRuntime (keys never exposed to LLM)
- Comprehensive threat analysis for files, URLs, domains, and IP addresses
- IOC (Indicators of Compromise) extraction and analysis
- User tracking and audit logging via agent state
- Automatic OTX SDK installation if not present
- Uses OTXv2Cached for improved performance

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.ti.otx import (
        otx_file_report,
        otx_url_report,
        otx_domain_report,
        otx_ip_report,
        otx_submit_url
    )
    
    agent = create_agent(
        model=llm,
        tools=[otx_file_report, otx_url_report, ...],
        system_prompt="You are a threat intelligence analyst..."
    )
    
    # Initialize state with API key
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Check domain example.com"}],
        "api_keys": {"API_KEY": "your_api_key"},
        "user_id": "analyst_001"
    })
"""

import os
import json
import subprocess
import sys
from typing import Optional, Dict, Any
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import (
    mask_api_key, mask_sensitive_data, safe_log_debug, 
    safe_log_info, safe_log_error
)
import logging

# Initialize logger
logger = setup_logger(__name__, log_file_path="logs/otx_tool.log")

# Global variable to cache OTX client instances
_otx_client_cache: Dict[str, Any] = {}


def _ensure_otx_sdk_installed():
    """
    Ensure OTXv2 package is installed. Install it at runtime if not present.
    
    Returns:
        bool: True if SDK is available, False otherwise
    """
    try:
        import OTXv2  # type: ignore
        import IndicatorTypes  # type: ignore  # type: ignore
        return True
    except ImportError:
        logger.info("OTXv2 SDK not found. Attempting to install...")
        try:
            # Try installing from PyPI first
            subprocess.check_call([sys.executable, "-m", "pip", "install", "OTXv2", "--quiet"])
            logger.info("Successfully installed OTXv2 from PyPI")
            import OTXv2  # type: ignore
            import IndicatorTypes  # type: ignore  # type: ignore
            return True
        except subprocess.CalledProcessError:
            logger.warning("Failed to install OTXv2 from PyPI. Package may need manual installation.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error installing OTXv2: {str(e)}", exc_info=True)
            return False


def _get_otx_client(api_key: str, use_cache: bool = True):
    """
    Get or create an OTX client instance. Uses OTXv2Cached for better performance.
    
    Args:
        api_key: OTX API key
        use_cache: Whether to use cached client instances (default: True)
    
    Returns:
        OTXv2Cached or OTXv2 instance
    """
    if not _ensure_otx_sdk_installed():
        raise ImportError("OTXv2 SDK is not available. Please install it manually: pip install OTXv2")
    
    from OTXv2 import OTXv2Cached, OTXv2, InvalidAPIKey, NotFound, BadRequest  # type: ignore
    
    # Use cache key based on API key (masked for logging)
    cache_key = mask_api_key(api_key) if use_cache else None
    
    if use_cache and cache_key in _otx_client_cache:
        logger.debug(f"Using cached OTX client for API key: {cache_key}")
        return _otx_client_cache[cache_key]
    
    try:
        # Prefer OTXv2Cached for better performance
        logger.info(f"Creating new OTXv2Cached client for API key: {mask_api_key(api_key)}")
        otx_client = OTXv2Cached(api_key, server="https://otx.alienvault.com")
        
        # Cache the client instance
        if use_cache and cache_key:
            _otx_client_cache[cache_key] = otx_client
        
        return otx_client
    except Exception as e:
        logger.warning(f"Failed to create OTXv2Cached, falling back to OTXv2: {str(e)}")
        # Fallback to regular OTXv2 if cached version fails
        otx_client = OTXv2(api_key, server="https://otx.alienvault.com")
        if use_cache and cache_key:
            _otx_client_cache[cache_key] = otx_client
        return otx_client


def _get_nested_value(data: Any, keys: list) -> Any:
    """
    Get a nested key from a dict/list structure without having to do loads of ifs.
    Based on get_malicious.py example.
    
    Args:
        data: Dictionary or list to traverse
        keys: List of keys to navigate through
    
    Returns:
        The value at the nested path, or None if not found
    """
    if not keys or len(keys) == 0:
        return data
    
    if isinstance(data, dict):
        key = keys[0]
        if key in data:
            return _get_nested_value(data[key], keys[1:])
        else:
            return None
    elif isinstance(data, list) and len(data) > 0:
        return _get_nested_value(data[0], keys)
    else:
        return None


def _calculate_threat_verdict_from_pulses(result: Dict[str, Any]) -> str:
    """
    Calculate threat verdict based on OTX pulse information.
    
    If an indicator is in pulses (threat intelligence reports), it's considered malicious.
    Based on get_malicious.py logic.
    
    Args:
        result: OTX API response containing pulse_info
    
    Returns:
        String verdict: "MALICIOUS", "SUSPICIOUS", or "CLEAN"
    """
    # Check if indicator is in whitelist (validation field)
    validation = _get_nested_value(result, ['validation'])
    if validation:
        return "CLEAN"
    
    # Check for pulses (threat intelligence reports)
    pulses = _get_nested_value(result, ['pulse_info', 'pulses'])
    if pulses and len(pulses) > 0:
        return "MALICIOUS"
    
    return "CLEAN"


def _extract_pulse_names(result: Dict[str, Any]) -> list:
    """
    Extract pulse names from OTX result.
    
    Args:
        result: OTX API response
    
    Returns:
        List of pulse names
    """
    pulses = _get_nested_value(result, ['pulse_info', 'pulses'])
    if not pulses:
        return []
    
    pulse_names = []
    for pulse in pulses if isinstance(pulses, list) else [pulses]:
        if isinstance(pulse, dict) and 'name' in pulse:
            pulse_names.append(pulse['name'])
    
    return pulse_names


class OTXSecurityAgentState(AgentState):
    """
    Extended agent state schema for AlienVault OTX threat intelligence operations.
    
    This state schema extends the base AgentState to include:
    - Security credentials (API keys stored securely in state)
    - User identification for audit trails
    - Threat context for maintaining analysis history
    
    Attributes:
        user_id: Identifier for the user running the analysis (for audit logging)
        api_keys: Dictionary mapping service names to API keys, e.g., {"API_KEY": "key123"}
        threat_context: Dictionary storing threat intelligence context and analysis history
    
    Example:
        state = {
            "messages": [...],
            "user_id": "analyst_001",
            "api_keys": {"API_KEY": "otx_api_key_here"},
            "threat_context": {"last_analysis": {...}}
        }
    """
    user_id: str = ""
    api_keys: Dict[str, str] = {}  # Store API keys securely in state
    threat_context: Dict[str, Any] = {}  # Store threat intelligence context


@tool
def otx_file_report(runtime: ToolRuntime, file_hash: str) -> str:
    """
    Get AlienVault OTX analysis report for a file by hash (MD5, SHA1, or SHA256).
    
    This tool queries AlienVault OTX's threat intelligence database for file analysis
    results. OTX is a collaborative threat intelligence platform that aggregates
    indicators of compromise (IOCs) from security researchers and organizations.
    
    When to use:
        - User provides a file hash and asks about its threat status
        - Need to check if a file is associated with known malware campaigns
        - Checking for IOCs related to a specific file hash
        - Incident response: analyzing suspicious files against OTX database
        - Security research: investigating malware samples and their associations
    
    When NOT to use:
        - User provides a file path (use file upload/scan instead)
        - Need to scan a new file (OTX is primarily for querying existing IOCs)
        - Hash format is invalid (must be MD5, SHA1, or SHA256)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            The 'runtime' parameter is automatically injected and hidden from the LLM.
            It provides secure access to API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        file_hash: The file hash to look up. Accepts MD5 (32 chars), SHA1 (40 chars), 
            or SHA256 (64 chars) hexadecimal strings. Examples:
            - MD5: "44d88612fea8a8f36de82e1278abb02f"
            - SHA1: "3395856ce81f2b7382dee72602f798b642f14140"
            - SHA256: "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "hash": str,
            "analysis_date": int (Unix timestamp, if available),
            "threat_verdict": str ("MALICIOUS" | "SUSPICIOUS" | "CLEAN"),
            "pulses": list (List of pulse names if indicator is in pulses),
            "ioc": dict (Indicators of Compromise data),
            "user_id": str (for audit logging)
        }
    
    Errors:
        - "OTX API key not found in agent state" - API key missing from state
        - "Invalid OTX API key" - API key is invalid or expired
        - "File hash not found: {hash}" - Hash not in OTX database
        - "Request timeout" - Network timeout after 30 seconds
        - "API error {code}" - Other API errors
    
    Example:
        User: "Check if this file hash is in OTX: 44d88612fea8a8f36de82e1278abb02f"
        Tool call: otx_file_report(file_hash="44d88612fea8a8f36de82e1278abb02f")
        Returns: JSON with threat verdict and IOC data
    """
    # Get API key from runtime state (ToolRuntime automatically hides this from LLM)
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    if not api_key:
        logger.error("OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state.", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": "OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
        })
    else:
        logger.info(f"OTX API key found in agent state: {mask_api_key(api_key)}")
    
    try:
        # Import IndicatorTypes
        if not _ensure_otx_sdk_installed():
            return json.dumps({
                "status": "error",
                "message": "OTXv2 SDK is not available. Please install it: pip install OTXv2"
            })
        
        import IndicatorTypes  # type: ignore
        
        # Determine hash type based on length
        hash_type = IndicatorTypes.FILE_HASH_MD5
        if len(file_hash) == 64:
            hash_type = IndicatorTypes.FILE_HASH_SHA256
        elif len(file_hash) == 40:
            hash_type = IndicatorTypes.FILE_HASH_SHA1
        
        logger.info(f"Querying OTX for file hash: {file_hash[:8]}... (type: {hash_type.name})")
        
        # Get OTX client
        otx = _get_otx_client(api_key)
        
        # Get full indicator details
        result = otx.get_indicator_details_full(hash_type, file_hash)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"OTX API response for file hash {file_hash[:8]}...: {json.dumps(result, indent=2)[:500]}")
        
        # Extract general section for pulse info
        general_section = result.get('general', {})
        pulse_names = _extract_pulse_names(general_section)
        threat_verdict = _calculate_threat_verdict_from_pulses(general_section)
        
        # Build response
        response_data = {
            "status": "success",
            "hash": file_hash,
            "threat_verdict": threat_verdict,
            "pulses": pulse_names,
            "data": result,
            "user_id": runtime.state.get("user_id", "")
        }
        
        logger.info(f"File hash {file_hash[:8]}... verdict: {threat_verdict}, pulses: {len(pulse_names)}")
        
        return json.dumps(response_data, indent=2)
    
    except ImportError as e:
        logger.error(f"Failed to import OTX SDK: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"OTX SDK import failed: {str(e)}. Please install OTXv2: pip install OTXv2"
        })
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"Error querying OTX for file hash {file_hash[:8]}...: {error_type}: {error_msg}", exc_info=True)
        
        # Handle specific OTX SDK exceptions
        if "InvalidAPIKey" in error_type or "403" in error_msg:
            return json.dumps({
                "status": "error",
                "message": "Invalid OTX API key. Please verify the API key is correct and active."
            })
        elif "NotFound" in error_type or "404" in error_msg:
            return json.dumps({
                "status": "error",
                "message": f"File hash not found in OTX database: {file_hash}. The file may not have been reported to OTX yet."
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unexpected error querying OTX: {error_msg}"
            })


@tool
def otx_url_report(runtime: ToolRuntime, url: str) -> str:
    """
    Get AlienVault OTX analysis report for a URL.
    
    This tool queries AlienVault OTX's threat intelligence database for URL analysis
    results. OTX aggregates IOCs from security researchers, making it valuable for
    detecting URLs associated with phishing, malware distribution, or other threats.
    
    When to use:
        - User provides a URL and asks about its threat status
        - Need to check if a URL is associated with known phishing campaigns
        - Checking for IOCs related to a specific URL
        - Incident response: analyzing suspicious URLs against OTX database
        - Security research: investigating malicious URLs and their associations
    
    When NOT to use:
        - User provides a domain name only (use otx_domain_report instead)
        - Need to scan a new URL (OTX is primarily for querying existing IOCs)
        - URL format is invalid (must include http:// or https://)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        url: The complete URL to analyze. Must include protocol (http:// or https://).
            Examples:
            - "https://example.com/path"
            - "http://suspicious-site.com/download.exe"
            - "https://phishing.example.com"
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "url": str,
            "analysis_date": int (Unix timestamp, if available),
            "ioc": dict (Indicators of Compromise data),
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "OTX API key not found in agent state" - API key missing
        - "Invalid OTX API key" - API key invalid
        - "URL not found in OTX database: {url}" - URL not in database
        - "Request timeout" - Network timeout
    
    Example:
        User: "Check if this URL is in OTX: https://suspicious-site.com/download.exe"
        Tool call: otx_url_report(url="https://suspicious-site.com/download.exe")
        Returns: JSON with threat verdict and IOC data
    """
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    if not api_key:
        logger.error("OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state.", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": "OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
        })
    else:
        logger.info(f"OTX API key found in agent state: {mask_api_key(api_key)}")
    
    try:
        if not _ensure_otx_sdk_installed():
            return json.dumps({
                "status": "error",
                "message": "OTXv2 SDK is not available. Please install it: pip install OTXv2"
            })
        
        import IndicatorTypes  # type: ignore
        
        logger.info(f"Querying OTX for URL: {url[:50]}...")
        
        # Get OTX client
        otx = _get_otx_client(api_key)
        
        # Get full indicator details
        result = otx.get_indicator_details_full(IndicatorTypes.URL, url)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"OTX API response for URL {url[:50]}...: {json.dumps(result, indent=2)[:500]}")
        
        # Extract general section for pulse info
        general_section = result.get('general', {})
        pulse_names = _extract_pulse_names(general_section)
        threat_verdict = _calculate_threat_verdict_from_pulses(general_section)
        
        # Check for additional threat indicators in url_list section
        url_list_section = result.get('url_list', {})
        google_safebrowsing = _get_nested_value(url_list_section, ['url_list', 'result', 'safebrowsing'])
        if google_safebrowsing and 'response_code' in str(google_safebrowsing):
            threat_verdict = "MALICIOUS"
        
        # Build response
        response_data = {
            "status": "success",
            "url": url,
            "threat_verdict": threat_verdict,
            "pulses": pulse_names,
            "data": result,
            "user_id": runtime.state.get("user_id", "")
        }
        
        logger.info(f"URL {url[:50]}... verdict: {threat_verdict}, pulses: {len(pulse_names)}")
        
        return json.dumps(response_data, indent=2)
    
    except ImportError as e:
        logger.error(f"Failed to import OTX SDK: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"OTX SDK import failed: {str(e)}. Please install OTXv2: pip install OTXv2"
        })
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"Error querying OTX for URL {url[:50]}...: {error_type}: {error_msg}", exc_info=True)
        
        if "InvalidAPIKey" in error_type or "403" in error_msg:
            return json.dumps({
                "status": "error",
                "message": "Invalid OTX API key. Please verify the API key is correct and active."
            })
        elif "NotFound" in error_type or "404" in error_msg:
            return json.dumps({
                "status": "error",
                "message": f"URL not found in OTX database: {url}. The URL may not have been reported to OTX yet."
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unexpected error querying OTX: {error_msg}"
            })


@tool
def otx_domain_report(runtime: ToolRuntime, domain: str) -> str:
    """
    Get AlienVault OTX analysis report for a domain.
    
    This tool queries AlienVault OTX's threat intelligence database for domain analysis
    results. OTX aggregates IOCs from security researchers, making it valuable for
    detecting domains associated with malware, phishing, C2 servers, or other threats.
    
    When to use:
        - User provides a domain name and asks about its threat status
        - Need to check if a domain is associated with known malicious campaigns
        - Checking for IOCs related to a specific domain
        - Incident response: analyzing suspicious domains against OTX database
        - Security research: investigating malicious infrastructure
    
    When NOT to use:
        - User provides a full URL (use otx_url_report instead)
        - User provides an IP address (use otx_ip_report instead)
        - Domain format is invalid (must be valid domain name like 'example.com')
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        domain: The domain name to analyze. Should be just the domain without protocol.
            Examples:
            - "example.com"
            - "suspicious-domain.net"
            - "malware-distribution.org"
            Do NOT include http://, https://, or paths.
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "domain": str,
            "analysis_date": int (Unix timestamp, if available),
            "ioc": dict (Indicators of Compromise data),
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "OTX API key not found in agent state" - API key missing
        - "Invalid OTX API key" - API key invalid
        - "Domain not found: {domain}" - Domain not in database
        - "Request timeout" - Network timeout
    
    Example:
        User: "Check if example.com is in OTX"
        Tool call: otx_domain_report(domain="example.com")
        Returns: JSON with threat verdict and IOC data
    """
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    if not api_key:
        logger.error("OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state.", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": "OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
        })
    else:
        logger.info(f"OTX API key found in agent state: {mask_api_key(api_key)}")
    
    try:
        if not _ensure_otx_sdk_installed():
            return json.dumps({
                "status": "error",
                "message": "OTXv2 SDK is not available. Please install it: pip install OTXv2"
            })
        
        import IndicatorTypes  # type: ignore
        
        logger.info(f"Querying OTX for domain: {domain}")
        
        # Get OTX client
        otx = _get_otx_client(api_key)
        
        # Get full indicator details
        result = otx.get_indicator_details_full(IndicatorTypes.DOMAIN, domain)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"OTX API response for domain {domain}: {json.dumps(result, indent=2)[:500]}")
        
        # Extract general section for pulse info
        general_section = result.get('general', {})
        pulse_names = _extract_pulse_names(general_section)
        threat_verdict = _calculate_threat_verdict_from_pulses(general_section)
        
        # Build response
        response_data = {
            "status": "success",
            "domain": domain,
            "threat_verdict": threat_verdict,
            "pulses": pulse_names,
            "data": result,
            "user_id": runtime.state.get("user_id", "")
        }
        
        logger.info(f"Domain {domain} verdict: {threat_verdict}, pulses: {len(pulse_names)}")
        
        return json.dumps(response_data, indent=2)
    
    except ImportError as e:
        logger.error(f"Failed to import OTX SDK: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"OTX SDK import failed: {str(e)}. Please install OTXv2: pip install OTXv2"
        })
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"Error querying OTX for domain {domain}: {error_type}: {error_msg}", exc_info=True)
        
        if "InvalidAPIKey" in error_type or "403" in error_msg:
            return json.dumps({
                "status": "error",
                "message": "Invalid OTX API key. Please verify the API key is correct and active."
            })
        elif "NotFound" in error_type or "404" in error_msg:
            return json.dumps({
                "status": "error",
                "message": f"Domain not found in OTX database: {domain}. The domain may not have been reported to OTX yet."
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unexpected error querying OTX: {error_msg}"
            })


@tool
def otx_ip_report(runtime: ToolRuntime, ip_address: str) -> str:
    """
    Get AlienVault OTX analysis report for an IP address.
    
    This tool queries AlienVault OTX's threat intelligence database for IP address
    analysis results. OTX aggregates IOCs from security researchers, making it valuable
    for detecting IPs associated with C2 servers, botnets, DDoS attacks, or other threats.
    
    When to use:
        - User provides an IP address and asks about its threat status
        - Need to check if an IP is associated with known malicious activity
        - Checking for IOCs related to a specific IP
        - Incident response: analyzing suspicious IPs against OTX database
        - Security research: investigating malicious infrastructure
        - Network forensics: checking firewall logs for malicious IPs
    
    When NOT to use:
        - User provides a domain name (use otx_domain_report instead)
        - User provides a URL (use otx_url_report instead)
        - IP format is invalid (must be valid IPv4 or IPv6 address)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        ip_address: The IP address to analyze. Accepts IPv4 (e.g., "192.168.1.1") or
            IPv6 (e.g., "2001:0db8:85a3:0000:0000:8a2e:0370:7334") addresses.
            Examples:
            - "192.168.1.1"
            - "8.8.8.8"
            - "2001:0db8::1"
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "ip_address": str,
            "ioc": dict (Indicators of Compromise data),
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "OTX API key not found in agent state" - API key missing
        - "Invalid OTX API key" - API key invalid
        - "IP address not found: {ip}" - IP not in database
        - "Request timeout" - Network timeout
    
    Example:
        User: "Check if IP 8.8.8.8 is in OTX"
        Tool call: otx_ip_report(ip_address="8.8.8.8")
        Returns: JSON with threat verdict and IOC data
    """
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    if not api_key:
        logger.error("OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state.", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": "OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
        })
    else:
        logger.info(f"OTX API key found in agent state: {mask_api_key(api_key)}")
    
    try:
        if not _ensure_otx_sdk_installed():
            return json.dumps({
                "status": "error",
                "message": "OTXv2 SDK is not available. Please install it: pip install OTXv2"
            })
        
        import IndicatorTypes  # type: ignore
        
        # Determine if IPv4 or IPv6
        if ':' in ip_address:
            indicator_type = IndicatorTypes.IPv6
        else:
            indicator_type = IndicatorTypes.IPv4
        
        logger.info(f"Querying OTX for IP address: {ip_address} (type: {indicator_type.name})")
        
        # Get OTX client
        otx = _get_otx_client(api_key)
        
        # Get full indicator details
        result = otx.get_indicator_details_full(indicator_type, ip_address)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"OTX API response for IP {ip_address}: {json.dumps(result, indent=2)[:500]}")
        
        # Extract general section for pulse info
        general_section = result.get('general', {})
        pulse_names = _extract_pulse_names(general_section)
        threat_verdict = _calculate_threat_verdict_from_pulses(general_section)
        
        # Build response
        response_data = {
            "status": "success",
            "ip_address": ip_address,
            "threat_verdict": threat_verdict,
            "pulses": pulse_names,
            "data": result,
            "user_id": runtime.state.get("user_id", "")
        }
        
        logger.info(f"IP address {ip_address} verdict: {threat_verdict}, pulses: {len(pulse_names)}")
        
        return json.dumps(response_data, indent=2)
    
    except ImportError as e:
        logger.error(f"Failed to import OTX SDK: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"OTX SDK import failed: {str(e)}. Please install OTXv2: pip install OTXv2"
        })
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"Error querying OTX for IP {ip_address}: {error_type}: {error_msg}", exc_info=True)
        
        if "InvalidAPIKey" in error_type or "403" in error_msg:
            return json.dumps({
                "status": "error",
                "message": "Invalid OTX API key. Please verify the API key is correct and active."
            })
        elif "NotFound" in error_type or "404" in error_msg:
            return json.dumps({
                "status": "error",
                "message": f"IP address not found in OTX database: {ip_address}. The IP may not have been reported to OTX yet."
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unexpected error querying OTX: {error_msg}"
            })


@tool
def otx_submit_url(runtime: ToolRuntime, url: str) -> str:
    """
    Submit a URL to AlienVault OTX for analysis.
    
    This tool submits a URL to AlienVault OTX for analysis and sharing with the
    threat intelligence community. Uses the OTX SDK's submit_url method.
    
    When to use:
        - User wants to contribute a suspicious URL to OTX
        - Need to trigger analysis of a new URL in OTX
        - Sharing threat intelligence with the OTX community
    
    When NOT to use:
        - User just wants to check existing results (use otx_url_report instead)
        - URL format is invalid (must include http:// or https://)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        url: The complete URL to submit. Must include protocol (http:// or https://).
            Examples:
            - "https://example.com/path"
            - "http://suspicious-site.com/download.exe"
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "url": str,
            "analysis_id": str (ID to track submission, if available),
            "message": str,
            "user_id": str
        }
    
    Errors:
        - "OTX API key not found in agent state" - API key missing
        - "Invalid OTX API key" - API key invalid
        - "API error {code}" - Submission failed
        - "Request timeout" - Network timeout
    
    Example:
        User: "Submit this URL to OTX: https://suspicious-site.com/file.exe"
        Tool call: otx_submit_url(url="https://suspicious-site.com/file.exe")
        Returns: JSON with analysis_id for tracking
    """
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    if not api_key:
        logger.error("OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state.", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": "OTX API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
        })
    else:
        logger.info(f"OTX API key found in agent state: {mask_api_key(api_key)}")
    
    try:
        if not _ensure_otx_sdk_installed():
            return json.dumps({
                "status": "error",
                "message": "OTXv2 SDK is not available. Please install it: pip install OTXv2"
            })
        
        logger.info(f"Submitting URL to OTX for analysis: {url[:50]}...")
        
        # Get OTX client
        otx = _get_otx_client(api_key)
        
        # Submit URL using SDK method
        result = otx.submit_url(url)
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"OTX URL submission response: {json.dumps(result, indent=2)}")
        
        # Build response
        response_data = {
            "status": "success",
            "url": url,
            "submission_result": result,
            "message": "URL submitted successfully to OTX for analysis",
            "user_id": runtime.state.get("user_id", "")
        }
        
        logger.info(f"Successfully submitted URL {url[:50]}... to OTX")
        
        return json.dumps(response_data, indent=2)
    
    except ImportError as e:
        logger.error(f"Failed to import OTX SDK: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"OTX SDK import failed: {str(e)}. Please install OTXv2: pip install OTXv2"
        })
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        logger.error(f"Error submitting URL to OTX {url[:50]}...: {error_type}: {error_msg}", exc_info=True)
        
        if "InvalidAPIKey" in error_type or "403" in error_msg:
            return json.dumps({
                "status": "error",
                "message": "Invalid OTX API key. Please verify the API key is correct and active."
            })
        elif "BadRequest" in error_type or "400" in error_msg:
            return json.dumps({
                "status": "error",
                "message": f"Bad request: {error_msg}. Please check the URL format."
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unexpected error submitting URL to OTX: {error_msg}"
            })


# Usage with LangChain Agent (example)

if __name__ == "__main__":
    from langchain.agents import create_agent

    # Initialize agent with OTX tools
    tools = [
        otx_file_report,
        otx_url_report,
        otx_domain_report,
        otx_ip_report,
        otx_submit_url
    ]

    # Create agent with custom state
    agent = create_agent(
        model="claude-sonnet-4-5-20250929",  # Use appropriate model
        tools=tools,
        system_prompt="""You are a cybersecurity threat intelligence analyst. 
        Use the OTX tools to analyze files, URLs, domains, and IP addresses 
        for security threats. Provide detailed threat assessments and recommendations based on OTX data.""",
        state_schema=OTXSecurityAgentState
    )

    # Initialize state with API key
    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": "Check if the domain 'example.com' has any security threats"
            }
        ],
        "user_id": "analyst_001",
        "api_keys": {
            "API_KEY": os.getenv("OTX_API_KEY", "your_api_key_here")
        },
        "threat_context": {}
    }
