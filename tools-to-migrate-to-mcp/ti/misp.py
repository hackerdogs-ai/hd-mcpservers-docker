"""
MISP (Malware Information Sharing Platform) Threat Intelligence Tools for LangChain Agents

This module provides LangChain tools for querying MISP threat intelligence platforms.
All tools use ToolRuntime to securely access API keys from agent state, following
LangChain v1.0 best practices for tools with state access.

Reference: https://docs.langchain.com/oss/python/langchain/tools

Key Features:
- Secure API key management via ToolRuntime (keys never exposed to LLM)
- Comprehensive threat analysis for files, URLs, domains, and IP addresses
- Tag-based threat classification and confidence scoring
- User tracking and audit logging via agent state

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.ti.misp import (
        misp_file_report,
        misp_url_report,
        misp_domain_report,
        misp_ip_report,
        misp_submit_url
    )
    
    agent = create_agent(
        model=llm,
        tools=[misp_file_report, misp_url_report, ...],
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
import requests
from typing import Optional, Dict, Any
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import (
    mask_api_key, mask_sensitive_data, safe_log_debug, 
    safe_log_info, safe_log_error
)

# Initialize logger
logger = setup_logger(__name__, log_file_path="logs/misp_tool.log")


class MISPSecurityAgentState(AgentState):
    """
    Extended agent state schema for MISP threat intelligence operations.
    
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
            "api_keys": {"API_KEY": "misp_api_key_here"},
            "threat_context": {"last_analysis": {...}}
        }
    """
    user_id: str = ""
    api_keys: Dict[str, str] = {}  # Store API keys securely in state, e.g., {"API_KEY": "your_api_key"}
    threat_context: Dict[str, Any] = {}  # Store threat intelligence context from MISP responses


def _calculate_threat_verdict(attributes: Dict[str, Any]) -> str:
    """
    Calculate threat verdict based on MISP response attributes.
    
    This helper function interprets MISP attribute data to provide a human-readable
    threat verdict. MISP uses tags and confidence levels to classify threats.
    
    Args:
        attributes: Dictionary containing MISP attribute data with keys:
            - tags: List of threat tags (e.g., ["malicious", "phishing", "malware"])
            - confidence: Confidence level from 0 to 100
            - value: The attribute value
            - first_analysis_date: Timestamp of first analysis
    
    Returns:
        String verdict: "MALICIOUS", "SUSPICIOUS", "CLEAN", or "UNKNOWN"
    
    Example:
        attributes = {"tags": ["malicious", "phishing"], "confidence": 95}
        verdict = _calculate_threat_verdict(attributes)
        # Returns: "MALICIOUS"
    """
    # Check for specific tags in the response (e.g., "malicious", "suspicious")
    tags = attributes.get("tags", [])
    confidence = attributes.get("confidence", 0)  # Confidence level from 0 to 100

    if "malicious" in tags or confidence > 90:
        return "MALICIOUS"
    elif "suspicious" in tags or confidence > 70:
        return "SUSPICIOUS"
    elif "clean" in tags or confidence <= 50:
        return "CLEAN"
    else:
        return "UNKNOWN"


@tool
def misp_file_report(runtime: ToolRuntime, file_hash: str) -> str:
    """
    Search MISP for a file by hash (MD5, SHA1, or SHA256).
    
    This tool queries your MISP instance for file hash analysis results. MISP is a
    threat intelligence sharing platform that allows organizations to share IOCs.
    Results include tags, confidence levels, and threat classifications.
    
    When to use:
        - User provides a file hash and asks about its threat status in MISP
        - Need to check if a file is associated with known malware campaigns
        - Checking for IOCs related to a specific file hash in your organization's MISP
        - Incident response: analyzing suspicious files against MISP database
        - Security research: investigating malware samples and their associations
    
    When NOT to use:
        - User provides a file path (use file upload/scan instead)
        - Need to scan a new file (MISP is primarily for querying existing IOCs)
        - Hash format is invalid (must be MD5, SHA1, or SHA256)
        - MISP instance URL is not configured (update endpoint in code)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            The 'runtime' parameter is automatically injected and hidden from the LLM.
            It provides secure access to API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        file_hash: The file hash to search for. Accepts MD5 (32 chars), SHA1 (40 chars), 
            or SHA256 (64 chars) hexadecimal strings. Examples:
            - MD5: "44d88612fea8a8f36de82e1278abb02f"
            - SHA1: "3395856ce81f2b7382dee72602f798b642f14140"
            - SHA256: "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "hash": str,
            "first_analysis_date": int (Unix timestamp, if available),
            "tags": list (threat tags from MISP),
            "value": str (attribute value),
            "threat_verdict": str ("MALICIOUS" | "SUSPICIOUS" | "CLEAN" | "UNKNOWN"),
            "user_id": str (for audit logging)
        }
    
    Errors:
        - "MISP API key not found in agent state" - API key missing from state
        - "Invalid MISP API key" - API key is invalid or expired
        - "File hash not found in MISP: {hash}" - Hash not in MISP database
        - "No attributes found" - Hash exists but no attributes returned
        - "Request timeout" - Network timeout after 30 seconds
        - "API error {code}" - Other API errors
    
    Note:
        Update the endpoint URL in the code to match your MISP instance URL.
        Replace "https://your-misp-instance" with your actual MISP server URL.
    
    Example:
        User: "Check if this file hash is in MISP: 44d88612fea8a8f36de82e1278abb02f"
        Tool call: misp_file_report(file_hash="44d88612fea8a8f36de82e1278abb02f")
        Returns: JSON with threat verdict, tags, and confidence level
    """
    try:
        safe_log_debug(logger, f"[misp_file_report] Starting execution", file_hash=file_hash)
        
        # Get API key from runtime state (ToolRuntime automatically hides this from LLM)
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[misp_file_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "MISP API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[misp_file_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        # MISP API endpoint for searching attributes (adjust based on your MISP instance)
        # TODO: Update this URL to match your MISP instance
        endpoint = f"https://your-misp-instance/api/attributes/search?value={file_hash}&type=File"
        headers = {
            "X-MISP-API-Key": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[misp_file_report] Querying MISP API", 
                     endpoint=endpoint, file_hash=file_hash, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[misp_file_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid MISP API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[misp_file_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"File hash not found in MISP: {file_hash}. The file may not have been reported to MISP yet."
            safe_log_info(logger, f"[misp_file_report] {error_msg}", file_hash=file_hash)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_text = response.text[:200] if hasattr(response, 'text') else 'Unknown error'
            error_msg = f"MISP API error {response.status_code}: {error_text}"
            safe_log_error(logger, f"[misp_file_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            misp_response = data.get("response", {})
            attributes = misp_response.get("attributes", [])
            
            safe_log_debug(logger, f"[misp_file_report] Parsing response data", 
                         attributes_count=len(attributes))

            if not attributes:
                error_msg = "No attributes found for this file hash in MISP."
                safe_log_info(logger, f"[misp_file_report] {error_msg}", file_hash=file_hash)
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })

            safe_log_info(logger, f"[misp_file_report] Successfully retrieved file report", hash=file_hash)
            # Return the exact MISP API response
            return json.dumps(data, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing MISP API response: {str(parse_error)}"
            safe_log_error(logger, f"[misp_file_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. MISP API may be slow or unavailable."
        safe_log_error(logger, f"[misp_file_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying MISP: {str(request_error)}"
        safe_log_error(logger, f"[misp_file_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying MISP: {str(e)}"
        safe_log_error(logger, f"[misp_file_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def misp_url_report(runtime: ToolRuntime, url: str) -> str:
    """
    Search MISP for a URL.
    
    This tool queries your MISP instance for URL analysis results. MISP is a
    threat intelligence sharing platform that allows organizations to share IOCs.
    Results include tags, confidence levels, and threat classifications.
    
    When to use:
        - User provides a URL and asks about its threat status in MISP
        - Need to check if a URL is associated with known phishing campaigns
        - Checking for IOCs related to a specific URL in your organization's MISP
        - Incident response: analyzing suspicious URLs against MISP database
        - Security research: investigating malicious URLs and their associations
    
    When NOT to use:
        - User provides a domain name only (use misp_domain_report instead)
        - Need to scan a new URL (MISP is primarily for querying existing IOCs)
        - URL format is invalid (must include http:// or https://)
        - MISP instance URL is not configured (update endpoint in code)
    
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
            "first_analysis_date": int (Unix timestamp, if available),
            "tags": list (threat tags from MISP),
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "MISP API key not found in agent state" - API key missing
        - "Invalid MISP API key" - API key invalid
        - "URL not found in MISP: {url}" - URL not in database
        - "No attributes found" - URL exists but no attributes returned
        - "Request timeout" - Network timeout
    
    Note:
        Update the endpoint URL in the code to match your MISP instance URL.
        Replace "https://your-misp-instance" with your actual MISP server URL.
    
    Example:
        User: "Check if this URL is in MISP: https://suspicious-site.com/download.exe"
        Tool call: misp_url_report(url="https://suspicious-site.com/download.exe")
        Returns: JSON with threat verdict, tags, and confidence level
    """
    try:
        safe_log_debug(logger, f"[misp_url_report] Starting execution", url=url)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[misp_url_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "MISP API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[misp_url_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        # TODO: Update this URL to match your MISP instance
        endpoint = f"https://your-misp-instance/api/attributes/search?value={url}&type=URL"
        headers = {
            "X-MISP-API-Key": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[misp_url_report] Querying MISP API", 
                     endpoint=endpoint, url=url, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[misp_url_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid MISP API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[misp_url_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"URL not found in MISP: {url}. The URL may not have been reported to MISP yet."
            safe_log_info(logger, f"[misp_url_report] {error_msg}", url=url)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_text = response.text[:200] if hasattr(response, 'text') else 'Unknown error'
            error_msg = f"MISP API error {response.status_code}: {error_text}"
            safe_log_error(logger, f"[misp_url_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            misp_response = data.get("response", {})
            attributes = misp_response.get("attributes", [])
            
            safe_log_debug(logger, f"[misp_url_report] Parsing response data", 
                         attributes_count=len(attributes))

            if not attributes:
                error_msg = "No attributes found for this URL in MISP."
                safe_log_info(logger, f"[misp_url_report] {error_msg}", url=url)
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })

            safe_log_info(logger, f"[misp_url_report] Successfully retrieved URL report", url=url)
            # Return the exact MISP API response
            return json.dumps(data, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing MISP API response: {str(parse_error)}"
            safe_log_error(logger, f"[misp_url_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. MISP API may be slow or unavailable."
        safe_log_error(logger, f"[misp_url_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying MISP: {str(request_error)}"
        safe_log_error(logger, f"[misp_url_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying MISP: {str(e)}"
        safe_log_error(logger, f"[misp_url_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def misp_domain_report(runtime: ToolRuntime, domain: str) -> str:
    """
    Search MISP for a domain.
    
    This tool queries your MISP instance for domain analysis results. MISP is a
    threat intelligence sharing platform that allows organizations to share IOCs.
    Results include tags, confidence levels, and threat classifications.
    
    When to use:
        - User provides a domain name and asks about its threat status in MISP
        - Need to check if a domain is associated with known malicious campaigns
        - Checking for IOCs related to a specific domain in your organization's MISP
        - Incident response: analyzing suspicious domains against MISP database
        - Security research: investigating malicious infrastructure
    
    When NOT to use:
        - User provides a full URL (use misp_url_report instead)
        - User provides an IP address (use misp_ip_report instead)
        - Domain format is invalid (must be valid domain name like 'example.com')
        - MISP instance URL is not configured (update endpoint in code)
    
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
            "first_analysis_date": int (Unix timestamp, if available),
            "tags": list (threat tags from MISP),
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "MISP API key not found in agent state" - API key missing
        - "Invalid MISP API key" - API key invalid
        - "Domain not found in MISP: {domain}" - Domain not in database
        - "No attributes found" - Domain exists but no attributes returned
        - "Request timeout" - Network timeout
    
    Note:
        Update the endpoint URL in the code to match your MISP instance URL.
        Replace "https://your-misp-instance" with your actual MISP server URL.
    
    Example:
        User: "Check if example.com is in MISP"
        Tool call: misp_domain_report(domain="example.com")
        Returns: JSON with threat verdict, tags, and confidence level
    """
    try:
        safe_log_debug(logger, f"[misp_domain_report] Starting execution", domain=domain)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[misp_domain_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "MISP API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[misp_domain_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        # TODO: Update this URL to match your MISP instance
        endpoint = f"https://your-misp-instance/api/attributes/search?value={domain}&type=Domain"
        headers = {
            "X-MISP-API-Key": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[misp_domain_report] Querying MISP API", 
                     endpoint=endpoint, domain=domain, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[misp_domain_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid MISP API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[misp_domain_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"Domain not found in MISP: {domain}. The domain may not have been reported to MISP yet."
            safe_log_info(logger, f"[misp_domain_report] {error_msg}", domain=domain)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_text = response.text[:200] if hasattr(response, 'text') else 'Unknown error'
            error_msg = f"MISP API error {response.status_code}: {error_text}"
            safe_log_error(logger, f"[misp_domain_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            misp_response = data.get("response", {})
            attributes = misp_response.get("attributes", [])
            
            safe_log_debug(logger, f"[misp_domain_report] Parsing response data", 
                         attributes_count=len(attributes))

            if not attributes:
                error_msg = "No attributes found for this domain in MISP."
                safe_log_info(logger, f"[misp_domain_report] {error_msg}", domain=domain)
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })

            safe_log_info(logger, f"[misp_domain_report] Successfully retrieved domain report", domain=domain)
            # Return the exact MISP API response
            return json.dumps(data, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing MISP API response: {str(parse_error)}"
            safe_log_error(logger, f"[misp_domain_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. MISP API may be slow or unavailable."
        safe_log_error(logger, f"[misp_domain_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying MISP: {str(request_error)}"
        safe_log_error(logger, f"[misp_domain_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying MISP: {str(e)}"
        safe_log_error(logger, f"[misp_domain_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def misp_ip_report(runtime: ToolRuntime, ip_address: str) -> str:
    """
    Search MISP for an IP address.
    
    This tool queries your MISP instance for IP address analysis results. MISP is a
    threat intelligence sharing platform that allows organizations to share IOCs.
    Results include tags, confidence levels, and threat classifications.
    
    When to use:
        - User provides an IP address and asks about its threat status in MISP
        - Need to check if an IP is associated with known malicious activity
        - Checking for IOCs related to a specific IP in your organization's MISP
        - Incident response: analyzing suspicious IPs against MISP database
        - Security research: investigating malicious infrastructure
        - Network forensics: checking firewall logs for malicious IPs
    
    When NOT to use:
        - User provides a domain name (use misp_domain_report instead)
        - User provides a URL (use misp_url_report instead)
        - IP format is invalid (must be valid IPv4 or IPv6 address)
        - MISP instance URL is not configured (update endpoint in code)
    
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
            "first_analysis_date": int (Unix timestamp, if available),
            "tags": list (threat tags from MISP),
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "MISP API key not found in agent state" - API key missing
        - "Invalid MISP API key" - API key invalid
        - "IP address not found in MISP: {ip}" - IP not in database
        - "No attributes found" - IP exists but no attributes returned
        - "Request timeout" - Network timeout
    
    Note:
        Update the endpoint URL in the code to match your MISP instance URL.
        Replace "https://your-misp-instance" with your actual MISP server URL.
    
    Example:
        User: "Check if IP 8.8.8.8 is in MISP"
        Tool call: misp_ip_report(ip_address="8.8.8.8")
        Returns: JSON with threat verdict, tags, and confidence level
    """
    try:
        safe_log_debug(logger, f"[misp_ip_report] Starting execution", ip_address=ip_address)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[misp_ip_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "MISP API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[misp_ip_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        # TODO: Update this URL to match your MISP instance
        endpoint = f"https://your-misp-instance/api/attributes/search?value={ip_address}&type=IP"
        headers = {
            "X-MISP-API-Key": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[misp_ip_report] Querying MISP API", 
                     endpoint=endpoint, ip_address=ip_address, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[misp_ip_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid MISP API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[misp_ip_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"IP address not found in MISP: {ip_address}. The IP may not have been reported to MISP yet."
            safe_log_info(logger, f"[misp_ip_report] {error_msg}", ip_address=ip_address)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_text = response.text[:200] if hasattr(response, 'text') else 'Unknown error'
            error_msg = f"MISP API error {response.status_code}: {error_text}"
            safe_log_error(logger, f"[misp_ip_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            misp_response = data.get("response", {})
            attributes = misp_response.get("attributes", [])
            
            safe_log_debug(logger, f"[misp_ip_report] Parsing response data", 
                         attributes_count=len(attributes))

            if not attributes:
                error_msg = "No attributes found for this IP address in MISP."
                safe_log_info(logger, f"[misp_ip_report] {error_msg}", ip_address=ip_address)
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })

            safe_log_info(logger, f"[misp_ip_report] Successfully retrieved IP report", ip_address=ip_address)
            # Return the exact MISP API response
            return json.dumps(data, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing MISP API response: {str(parse_error)}"
            safe_log_error(logger, f"[misp_ip_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. MISP API may be slow or unavailable."
        safe_log_error(logger, f"[misp_ip_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying MISP: {str(request_error)}"
        safe_log_error(logger, f"[misp_ip_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying MISP: {str(e)}"
        safe_log_error(logger, f"[misp_ip_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def misp_submit_url(runtime: ToolRuntime, url: str) -> str:
    """
    Submit a URL to MISP for analysis (if supported).
    
    This tool submits a URL to your MISP instance, creating a new attribute or event.
    MISP allows organizations to share threat intelligence, so this tool enables
    contributing IOCs to your organization's threat intelligence database.
    
    When to use:
        - User wants to contribute a suspicious URL to MISP
        - Need to create a new attribute in MISP for a URL
        - Sharing threat intelligence with your organization via MISP
    
    When NOT to use:
        - User just wants to check existing results (use misp_url_report instead)
        - MISP submission is not supported (check MISP API documentation)
        - URL format is invalid (must include http:// or https://)
        - MISP instance URL is not configured (update endpoint in code)
    
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
            "attribute_id": str (ID of created attribute, if available),
            "message": str,
            "user_id": str
        }
    
    Errors:
        - "MISP API key not found in agent state" - API key missing
        - "Invalid MISP API key" - API key invalid
        - "API error {code}" - Submission failed
        - "Request timeout" - Network timeout
    
    Note:
        MISP API may have specific endpoints for submission. Check MISP API documentation
        for actual submission endpoints and requirements. Update the endpoint URL in the
        code to match your MISP instance URL.
    
    Example:
        User: "Submit this URL to MISP: https://suspicious-site.com/file.exe"
        Tool call: misp_submit_url(url="https://suspicious-site.com/file.exe")
        Returns: JSON with attribute_id for tracking
    """
    try:
        safe_log_debug(logger, f"[misp_submit_url] Starting execution", url=url)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[misp_submit_url] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "MISP API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[misp_submit_url] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        # Note: MISP API may have specific endpoints for submission; check documentation
        # TODO: Update this URL to match your MISP instance and verify the submission endpoint
        endpoint = "https://your-misp-instance/api/attributes"  # Hypothetical endpoint for creating attributes
        headers = {
            "X-MISP-API-Key": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {
            "value": url,
            "type": "URL",
            "category": 2  # Example category, adjust based on MISP configuration
        }
        
        safe_log_info(logger, f"[misp_submit_url] Submitting URL to MISP", 
                     endpoint=endpoint, url=url, api_key_masked=masked_key)

        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        safe_log_debug(logger, f"[misp_submit_url] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid MISP API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[misp_submit_url] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_text = response.text[:200] if hasattr(response, 'text') else "Unknown error"
            error_msg = f"MISP API error {response.status_code}: {error_text}. Check MISP API documentation for correct submission endpoints."
            safe_log_error(logger, f"[misp_submit_url] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            safe_log_info(logger, f"[misp_submit_url] Successfully submitted URL to MISP", url=url)
            # Return the exact MISP API response
            return json.dumps(data, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing MISP API response: {str(parse_error)}"
            safe_log_error(logger, f"[misp_submit_url] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. MISP API may be slow or unavailable."
        safe_log_error(logger, f"[misp_submit_url] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error submitting URL to MISP: {str(request_error)}"
        safe_log_error(logger, f"[misp_submit_url] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error submitting URL to MISP: {str(e)}"
        safe_log_error(logger, f"[misp_submit_url] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


# Usage with LangChain Agent (example)

if __name__ == "__main__":
    from langchain.agents import create_agent

    # Initialize agent with MISP tools
    tools = [
        misp_file_report,
        misp_url_report,
        misp_domain_report,
        misp_ip_report,
        misp_submit_url  # Optional, if submission is supported
    ]

    # Create agent with custom state
    agent = create_agent(
        model="claude-sonnet-4-5-20250929",  # Use appropriate model
        tools=tools,
        system_prompt="""You are a cybersecurity threat intelligence analyst. 
        Use the MISP tools to analyze files, URLs, domains, and IP addresses 
        for security threats. Provide detailed threat assessments and recommendations based on MISP data.""",
        state_schema=MISPSecurityAgentState
    )

    # Initialize state with API key
    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": "Check if the domain 'example.com' has any security threats in MISP"
            }
        ],
        "user_id": "analyst_001",
        "api_keys": {
            "API_KEY": os.getenv("MISP_API_KEY", "your_api_key_here")
        },
        "threat_context": {}
    }
