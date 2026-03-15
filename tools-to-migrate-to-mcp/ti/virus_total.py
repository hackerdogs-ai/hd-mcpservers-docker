"""
VirusTotal Threat Intelligence Tools for LangChain Agents

This module provides LangChain tools for querying VirusTotal's threat intelligence API.
All tools use ToolRuntime to securely access API keys from agent state, following
LangChain v1.0 best practices for tools with state access.

Reference: https://docs.langchain.com/oss/python/langchain/tools

Key Features:
- Secure API key management via ToolRuntime (keys never exposed to LLM)
- Comprehensive threat analysis for files, URLs, domains, and IP addresses
- Automatic threat verdict calculation based on detection statistics
- User tracking and audit logging via agent state

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.ti.virus_total import (
        virustotal_file_report,
        virustotal_url_report,
        virustotal_domain_report,
        virustotal_ip_report,
        scan_url,
        get_analysis
    )
    
    agent = create_agent(
        model=llm,
        tools=[virustotal_file_report, virustotal_url_report, ...],
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
import base64
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
logger = setup_logger(__name__, log_file_path="logs/virustotal_tool.log")


class VirusTotalSecurityAgentState(AgentState):
    """
    Extended agent state schema for VirusTotal threat intelligence operations.
    
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
            "api_keys": {"API_KEY": "vt_api_key_here"},
            "threat_context": {"last_analysis": {...}}
        }
    """
    user_id: str = ""
    api_keys: Dict[str, str] = {}  # Store API keys securely in state
    threat_context: Dict[str, Any] = {}  # Store threat intelligence context


def _calculate_threat_verdict(stats: Dict[str, int]) -> str:
    """
    Calculate threat verdict based on VirusTotal analysis statistics.
    
    This helper function interprets the detection statistics from VirusTotal's
    last_analysis_stats to provide a human-readable threat verdict.
    
    Args:
        stats: Dictionary containing detection statistics with keys:
            - malicious: Number of engines detecting the sample as malicious
            - suspicious: Number of engines flagging as suspicious
            - undetected: Number of engines with no detection
            - harmless: Number of engines marking as harmless
    
    Returns:
        String verdict: "MALICIOUS (N detections)", "SUSPICIOUS (N detections)",
        "UNDETECTED", or "CLEAN"
    
    Example:
        stats = {"malicious": 5, "suspicious": 2, "undetected": 50}
        verdict = _calculate_threat_verdict(stats)
        # Returns: "MALICIOUS (5 detections)"
    """
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    undetected = stats.get("undetected", 0)

    if malicious > 0:
        return f"MALICIOUS ({malicious} detections)"
    elif suspicious > 0:
        return f"SUSPICIOUS ({suspicious} detections)"
    elif undetected > 0:
        return "UNDETECTED"
    else:
        return "CLEAN"


@tool
def virustotal_file_report(runtime: ToolRuntime, file_hash: str, details: bool = False) -> str:
    """
    Get VirusTotal analysis report for a file by hash (MD5, SHA1, or SHA256).
    
    This tool queries VirusTotal's database for file analysis results from multiple
    antivirus engines. It provides comprehensive threat intelligence including:
    - Detection statistics (malicious, suspicious, undetected counts)
    - File metadata (size, type, meaningful name)
    - Last analysis timestamp
    - Calculated threat verdict
    
    When to use:
        - User provides a file hash and asks about its safety
        - Need to verify if a downloaded file is malicious
        - Checking threat status of a file before execution
        - Incident response: analyzing suspicious files
        - Security research: investigating malware samples
    
    When NOT to use:
        - User provides a file path (use file upload/scan instead)
        - Need to scan a new file (use scan_url or file upload tools)
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
        details: If True, returns the complete raw VirusTotal API response with all engine results,
            full metadata, and complete dataset. If False (default), returns a summary with
            threat verdict, key stats, and essential information. Set to True when:
            - User explicitly asks for "full details", "complete data", "all information", "raw data"
            - User wants to see all engine results or comprehensive analysis
            - User asks for "everything" or "the entire response"
            - Detailed forensic analysis is needed
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "hash": str,
            "last_analysis_date": int (Unix timestamp),
            "last_analysis_stats": {
                "malicious": int,
                "suspicious": int,
                "undetected": int,
                "harmless": int
            },
            "meaningful_name": str (if available),
            "size": int (bytes),
            "type_description": str,
            "threat_verdict": str ("MALICIOUS (N detections)" | "SUSPICIOUS" | "UNDETECTED" | "CLEAN"),
            "user_id": str (for audit logging)
        }
    
    Errors:
        - "VirusTotal API key not found in agent state" - API key missing from state
        - "Invalid VirusTotal API key" - API key is invalid or expired
        - "File hash not found: {hash}" - Hash not in VirusTotal database
        - "Request timeout" - Network timeout after 30 seconds
        - "API error {code}" - Other API errors
    
    Example:
        User: "Check if this file hash is safe: 44d88612fea8a8f36de82e1278abb02f"
        Tool call: virustotal_file_report(file_hash="44d88612fea8a8f36de82e1278abb02f")
        Returns: JSON with threat verdict and detection statistics
    """
    try:
        safe_log_debug(logger, f"[virustotal_file_report] Starting execution", file_hash=file_hash)
        
        # Debug: Log what's in runtime.state
        state_keys = list(runtime.state.keys()) if hasattr(runtime.state, 'keys') else []
        safe_log_debug(logger, f"[virustotal_file_report] Runtime state keys: {state_keys}")
        safe_log_debug(logger, f"[virustotal_file_report] Runtime state type: {type(runtime.state)}")
        
        # Get API key from runtime state (ToolRuntime automatically hides this from LLM)
        api_keys_dict = runtime.state.get("api_keys", {})
        safe_log_debug(logger, f"[virustotal_file_report] api_keys dict: {type(api_keys_dict)}, keys: {list(api_keys_dict.keys()) if isinstance(api_keys_dict, dict) else 'N/A'}")
        
        api_key = api_keys_dict.get("API_KEY") if isinstance(api_keys_dict, dict) else None
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[virustotal_file_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "VirusTotal API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[virustotal_file_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        endpoint = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        headers = {
            "x-apikey": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[virustotal_file_report] Querying VirusTotal API", 
                     endpoint=endpoint, file_hash=file_hash, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[virustotal_file_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid VirusTotal API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[virustotal_file_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"File hash not found in VirusTotal database: {file_hash}. The file may not have been analyzed yet."
            safe_log_info(logger, f"[virustotal_file_report] {error_msg}", file_hash=file_hash)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_msg = f"VirusTotal API error {response.status_code}: {response.text[:200]}"
            safe_log_error(logger, f"[virustotal_file_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            file_data = data.get("data", {})
            attributes = file_data.get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            
            safe_log_info(logger, f"[virustotal_file_report] Successfully retrieved file report", hash=file_hash)
            
            # If details=True, return the complete raw API response
            if details:
                return json.dumps(data, indent=2)
            
            # Otherwise return summary format
            threat_verdict = _calculate_threat_verdict(stats)
            result = {
                "status": "success",
                "hash": file_hash,
                "last_analysis_date": attributes.get("last_analysis_date"),
                "last_analysis_stats": stats,
                "meaningful_name": attributes.get("meaningful_name"),
                "size": attributes.get("size"),
                "type_description": attributes.get("type_description"),
                "threat_verdict": threat_verdict,
                "user_id": runtime.state.get("user_id")
            }
            return json.dumps(result, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing VirusTotal API response: {str(parse_error)}"
            safe_log_error(logger, f"[virustotal_file_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. VirusTotal API may be slow or unavailable."
        safe_log_error(logger, f"[virustotal_file_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying VirusTotal: {str(request_error)}"
        safe_log_error(logger, f"[virustotal_file_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying VirusTotal: {str(e)}"
        safe_log_error(logger, f"[virustotal_file_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def virustotal_url_report(runtime: ToolRuntime, url: str, details: bool = False) -> str:
    """
    Get VirusTotal analysis report for a URL.
    
    This tool queries VirusTotal's database for URL analysis results from multiple
    security engines. It provides comprehensive threat intelligence including:
    - Detection statistics (malicious, suspicious, undetected counts)
    - URL metadata (title, last analysis timestamp)
    - Calculated threat verdict
    
    When to use:
        - User provides a URL and asks about its safety
        - Need to verify if a link is malicious before clicking
        - Checking threat status of a suspicious URL
        - Incident response: analyzing phishing URLs
        - Security research: investigating malicious domains
    
    When NOT to use:
        - User provides a domain name only (use virustotal_domain_report instead)
        - Need to scan a new URL (use scan_url tool instead)
        - URL format is invalid (must include http:// or https://)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        url: The complete URL to analyze. Must include protocol (http:// or https://).
            Examples:
            - "https://example.com/path"
            - "http://suspicious-site.com/download.exe"
            - "https://malware.example.com"
        details: If True, returns the complete raw VirusTotal API response with all engine results,
            full metadata, and complete dataset. If False (default), returns a summary with
            threat verdict, key stats, and essential information. Set to True when:
            - User explicitly asks for "full details", "complete data", "all information", "raw data"
            - User wants to see all engine results or comprehensive analysis
            - User asks for "everything" or "the entire response"
            - Detailed forensic analysis is needed
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "url": str,
            "last_analysis_date": int (Unix timestamp),
            "last_analysis_stats": {
                "malicious": int,
                "suspicious": int,
                "undetected": int,
                "harmless": int
            },
            "title": str (page title if available),
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "VirusTotal API key not found in agent state" - API key missing
        - "Invalid VirusTotal API key" - API key invalid
        - "URL not found in VirusTotal database: {url}" - URL not analyzed yet
        - "Request timeout" - Network timeout
    
    Example:
        User: "Is this URL safe: https://suspicious-site.com/download.exe"
        Tool call: virustotal_url_report(url="https://suspicious-site.com/download.exe")
        Returns: JSON with threat verdict and detection statistics
    """
    try:
        safe_log_debug(logger, f"[virustotal_url_report] Starting execution", url=url)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[virustotal_url_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "VirusTotal API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[virustotal_url_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        # URL needs to be encoded as base64 for the VirusTotal API
        url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        headers = {
            "x-apikey": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[virustotal_url_report] Querying VirusTotal API", 
                     endpoint=endpoint, url=url, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[virustotal_url_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid VirusTotal API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[virustotal_url_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"URL not found in VirusTotal database: {url}. The URL may not have been analyzed yet."
            safe_log_info(logger, f"[virustotal_url_report] {error_msg}", url=url)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_msg = f"VirusTotal API error {response.status_code}: {response.text[:200]}"
            safe_log_error(logger, f"[virustotal_url_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            url_data = data.get("data", {})
            attributes = url_data.get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            
            safe_log_info(logger, f"[virustotal_url_report] Successfully retrieved URL report", url=url)
            
            # If details=True, return the complete raw API response
            if details:
                return json.dumps(data, indent=2)
            
            # Otherwise return summary format
            threat_verdict = _calculate_threat_verdict(stats)
            result = {
                "status": "success",
                "url": url,
                "last_analysis_date": attributes.get("last_analysis_date"),
                "last_analysis_stats": stats,
                "title": attributes.get("title"),
                "threat_verdict": threat_verdict,
                "user_id": runtime.state.get("user_id")
            }
            return json.dumps(result, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing VirusTotal API response: {str(parse_error)}"
            safe_log_error(logger, f"[virustotal_url_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. VirusTotal API may be slow or unavailable."
        safe_log_error(logger, f"[virustotal_url_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying VirusTotal: {str(request_error)}"
        safe_log_error(logger, f"[virustotal_url_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying VirusTotal: {str(e)}"
        safe_log_error(logger, f"[virustotal_url_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def virustotal_domain_report(runtime: ToolRuntime, domain: str, details: bool = False) -> str:
    """
    Get VirusTotal analysis report for a domain.
    
    This tool queries VirusTotal's database for domain analysis results, providing
    threat intelligence about domains associated with malicious activity, phishing,
    malware distribution, or other security threats.
    
    When to use:
        - User provides a domain name and asks about its safety
        - Need to verify if a domain is associated with malicious activity
        - Checking threat status of a suspicious domain
        - Incident response: analyzing command & control domains
        - Security research: investigating malicious infrastructure
    
    When NOT to use:
        - User provides a full URL (use virustotal_url_report instead)
        - User provides an IP address (use virustotal_ip_report instead)
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
        details: If True, returns the complete raw VirusTotal API response with all engine results,
            full metadata, and complete dataset. If False (default), returns a summary with
            threat verdict, key stats, and essential information. Set to True when:
            - User explicitly asks for "full details", "complete data", "all information", "raw data"
            - User wants to see all engine results or comprehensive analysis
            - User asks for "everything" or "the entire response"
            - Detailed forensic analysis is needed
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "domain": str,
            "last_analysis_date": int (Unix timestamp),
            "last_analysis_stats": {
                "malicious": int,
                "suspicious": int,
                "undetected": int,
                "harmless": int
            },
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "VirusTotal API key not found in agent state" - API key missing
        - "Invalid VirusTotal API key" - API key invalid
        - "Domain not found: {domain}" - Domain not in database
        - "Request timeout" - Network timeout
    
    Example:
        User: "Check if example.com is safe"
        Tool call: virustotal_domain_report(domain="example.com")
        Returns: JSON with threat verdict and detection statistics
    """
    try:
        safe_log_debug(logger, f"[virustotal_domain_report] Starting execution", domain=domain)
        
        # Debug: Log what's in runtime.state
        state_keys = list(runtime.state.keys()) if hasattr(runtime.state, 'keys') else []
        safe_log_debug(logger, f"[virustotal_domain_report] Runtime state keys: {state_keys}")
        
        # Get API key from runtime state (ToolRuntime automatically hides this from LLM)
        api_keys_dict = runtime.state.get("api_keys", {})
        safe_log_debug(logger, f"[virustotal_domain_report] api_keys dict: {type(api_keys_dict)}, keys: {list(api_keys_dict.keys()) if isinstance(api_keys_dict, dict) else 'N/A'}")
        
        api_key = api_keys_dict.get("API_KEY") if isinstance(api_keys_dict, dict) else None
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[virustotal_domain_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "VirusTotal API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[virustotal_domain_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        endpoint = f"https://www.virustotal.com/api/v3/domains/{domain}"
        headers = {
            "x-apikey": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[virustotal_domain_report] Querying VirusTotal API", 
                     endpoint=endpoint, domain=domain, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[virustotal_domain_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid VirusTotal API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[virustotal_domain_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"Domain not found in VirusTotal database: {domain}. The domain may not have been analyzed yet."
            safe_log_info(logger, f"[virustotal_domain_report] {error_msg}", domain=domain)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_msg = f"VirusTotal API error {response.status_code}: {response.text[:200]}"
            safe_log_error(logger, f"[virustotal_domain_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            safe_log_info(logger, f"[virustotal_domain_report] Successfully retrieved domain report", domain=domain)
            
            domain_data = data.get("data", {})
            attributes = domain_data.get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            
            # If details=True, return the complete raw API response
            if details:
                return json.dumps(data, indent=2)
            
            # Otherwise return summary format
            threat_verdict = _calculate_threat_verdict(stats)
            result = {
                "status": "success",
                "domain": domain,
                "last_analysis_date": attributes.get("last_analysis_date"),
                "last_analysis_stats": stats,
                "threat_verdict": threat_verdict,
                "user_id": runtime.state.get("user_id")
            }
            return json.dumps(result, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing VirusTotal API response: {str(parse_error)}"
            safe_log_error(logger, f"[virustotal_domain_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. VirusTotal API may be slow or unavailable."
        safe_log_error(logger, f"[virustotal_domain_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying VirusTotal: {str(request_error)}"
        safe_log_error(logger, f"[virustotal_domain_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying VirusTotal: {str(e)}"
        safe_log_error(logger, f"[virustotal_domain_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def virustotal_ip_report(runtime: ToolRuntime, ip_address: str, details: bool = False) -> str:
    """
    Get VirusTotal analysis report for an IP address.
    
    This tool queries VirusTotal's database for IP address analysis results, providing
    threat intelligence about IPs associated with malicious activity, command & control
    servers, botnets, DDoS attacks, or other security threats.
    
    When to use:
        - User provides an IP address and asks about its safety
        - Need to verify if an IP is associated with malicious activity
        - Checking threat status of a suspicious IP
        - Incident response: analyzing C2 server IPs
        - Security research: investigating malicious infrastructure
        - Network forensics: checking firewall logs for malicious IPs
    
    When NOT to use:
        - User provides a domain name (use virustotal_domain_report instead)
        - User provides a URL (use virustotal_url_report instead)
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
        details: If True, returns the complete raw VirusTotal API response with all engine results,
            full metadata, and complete dataset. If False (default), returns a summary with
            threat verdict, key stats, and essential information. Set to True when:
            - User explicitly asks for "full details", "complete data", "all information", "raw data"
            - User wants to see all engine results or comprehensive analysis
            - User asks for "everything" or "the entire response"
            - Detailed forensic analysis is needed
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "ip_address": str,
            "country": str (ISO country code),
            "asn": int (Autonomous System Number),
            "last_analysis_date": int (Unix timestamp),
            "last_analysis_stats": {
                "malicious": int,
                "suspicious": int,
                "undetected": int,
                "harmless": int
            },
            "threat_verdict": str,
            "user_id": str
        }
    
    Errors:
        - "VirusTotal API key not found in agent state" - API key missing
        - "Invalid VirusTotal API key" - API key invalid
        - "IP address not found: {ip}" - IP not in database
        - "Request timeout" - Network timeout
    
    Example:
        User: "Check if IP 8.8.8.8 is safe"
        Tool call: virustotal_ip_report(ip_address="8.8.8.8")
        Returns: JSON with threat verdict, country, ASN, and detection statistics
    """
    try:
        safe_log_debug(logger, f"[virustotal_ip_report] Starting execution", ip_address=ip_address)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[virustotal_ip_report] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "VirusTotal API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[virustotal_ip_report] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        endpoint = f"https://www.virustotal.com/api/v3/ip_addresses/{ip_address}"
        headers = {
            "x-apikey": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[virustotal_ip_report] Querying VirusTotal API", 
                     endpoint=endpoint, ip_address=ip_address, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[virustotal_ip_report] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid VirusTotal API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[virustotal_ip_report] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"IP address not found in VirusTotal database: {ip_address}. The IP may not have been analyzed yet."
            safe_log_info(logger, f"[virustotal_ip_report] {error_msg}", ip_address=ip_address)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_msg = f"VirusTotal API error {response.status_code}: {response.text[:200]}"
            safe_log_error(logger, f"[virustotal_ip_report] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            safe_log_info(logger, f"[virustotal_ip_report] Successfully retrieved IP report", ip_address=ip_address)
            
            ip_data = data.get("data", {})
            attributes = ip_data.get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            
            # If details=True, return the complete raw API response
            if details:
                return json.dumps(data, indent=2)
            
            # Otherwise return summary format
            threat_verdict = _calculate_threat_verdict(stats)
            result = {
                "status": "success",
                "ip_address": ip_address,
                "country": attributes.get("country"),
                "asn": attributes.get("asn"),
                "last_analysis_date": attributes.get("last_analysis_date"),
                "last_analysis_stats": stats,
                "threat_verdict": threat_verdict,
                "user_id": runtime.state.get("user_id")
            }
            return json.dumps(result, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing VirusTotal API response: {str(parse_error)}"
            safe_log_error(logger, f"[virustotal_ip_report] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. VirusTotal API may be slow or unavailable."
        safe_log_error(logger, f"[virustotal_ip_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying VirusTotal: {str(request_error)}"
        safe_log_error(logger, f"[virustotal_ip_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying VirusTotal: {str(e)}"
        safe_log_error(logger, f"[virustotal_ip_report] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def scan_url(runtime: ToolRuntime, url: str, details: bool = False) -> str:
    """
    Submit a URL to VirusTotal for scanning and analysis.
    
    This tool submits a URL to VirusTotal's scanning queue for analysis by multiple
    security engines. Unlike the report tools, this tool initiates a new scan rather
    than querying existing results. Use this when you need fresh analysis or when
    a URL hasn't been analyzed yet.
    
    When to use:
        - User provides a URL that needs to be scanned for the first time
        - Need to trigger a fresh analysis of an existing URL
        - User asks to "scan" or "analyze" a URL (not just check existing results)
        - Incident response: submitting suspicious URLs for immediate analysis
    
    When NOT to use:
        - User just wants to check existing results (use virustotal_url_report instead)
        - URL has already been analyzed recently (use virustotal_url_report for faster results)
        - URL format is invalid (must include http:// or https://)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        url: The complete URL to scan. Must include protocol (http:// or https://).
            Examples:
            - "https://example.com/path"
            - "http://suspicious-site.com/download.exe"
        details: If True, returns the complete raw VirusTotal API response with all submission
            details and metadata. If False (default), returns a summary with analysis_id and
            essential information. Set to True when:
            - User explicitly asks for "full details", "complete data", "all information"
            - User wants to see all submission metadata
            - Detailed tracking information is needed
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "url": str,
            "analysis_id": str (ID to check scan results later),
            "message": str ("URL submitted for scanning"),
            "user_id": str
        }
    
    Errors:
        - "VirusTotal API key not found in agent state" - API key missing
        - "Invalid VirusTotal API key" - API key invalid
        - "API error {code}" - Submission failed
        - "Request timeout" - Network timeout
    
    Note:
        After submission, use virustotal_url_report to check results once scanning completes.
        Scanning may take several minutes. The analysis_id can be used to track progress.
    
    Example:
        User: "Scan this URL for malware: https://suspicious-site.com/file.exe"
        Tool call: scan_url(url="https://suspicious-site.com/file.exe")
        Returns: JSON with analysis_id for tracking the scan
    """
    try:
        safe_log_debug(logger, f"[scan_url] Starting execution", url=url)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[scan_url] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "VirusTotal API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[scan_url] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        endpoint = "https://www.virustotal.com/api/v3/urls"
        headers = {
            "x-apikey": api_key,
            "Accept": "application/json"
        }
        data = {"url": url}
        
        safe_log_info(logger, f"[scan_url] Submitting URL to VirusTotal for scanning", 
                     endpoint=endpoint, url=url, api_key_masked=masked_key)

        response = requests.post(endpoint, headers=headers, data=data, timeout=30)
        safe_log_debug(logger, f"[scan_url] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid VirusTotal API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[scan_url] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_text = response.text[:200] if hasattr(response, 'text') else "Unknown error"
            error_msg = f"VirusTotal API error {response.status_code}: {error_text}"
            safe_log_error(logger, f"[scan_url] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            safe_log_info(logger, f"[scan_url] Successfully submitted URL for scanning", url=url)
            
            scan_data = data.get("data", {})
            analysis_id = scan_data.get("id")
            
            # If details=True, return the complete raw API response
            if details:
                return json.dumps(data, indent=2)
            
            # Otherwise return summary format
            result = {
                "status": "success",
                "url": url,
                "analysis_id": analysis_id,
                "message": "URL submitted for scanning. Use get_analysis() with the analysis_id to check results once scanning completes.",
                "user_id": runtime.state.get("user_id")
            }
            return json.dumps(result, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing VirusTotal API response: {str(parse_error)}"
            safe_log_error(logger, f"[scan_url] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. VirusTotal API may be slow or unavailable."
        safe_log_error(logger, f"[scan_url] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error submitting URL to VirusTotal: {str(request_error)}"
        safe_log_error(logger, f"[scan_url] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error submitting URL to VirusTotal: {str(e)}"
        safe_log_error(logger, f"[scan_url] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def get_analysis(runtime: ToolRuntime, analysis_id: str, details: bool = False) -> str:
    """
    Get the results of a VirusTotal analysis by its analysis ID.
    
    This tool retrieves the status and results of a previously submitted analysis.
    Use this after submitting a URL or file for scanning to check if the analysis
    has completed and retrieve the detection results.
    
    When to use:
        - After calling scan_url() - use the returned analysis_id to check scan status
        - User asks "check the status of analysis {id}" or "get results for analysis {id}"
        - Need to poll for scan completion after submitting a URL/file
        - Incident response: checking if submitted IOCs have been analyzed yet
    
    When NOT to use:
        - User wants to check a URL/domain/IP directly (use virustotal_url_report, etc.)
        - Analysis ID is invalid or not found
        - Analysis is still queued (status will indicate "queued" - may need to wait)
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY")
        analysis_id: The analysis ID returned from scan_url() or file upload.
            Format: Typically a base64-encoded string or UUID.
            Example: "u-1234567890abcdef" or similar ID format
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "analysis_id": str,
            "analysis_status": str ("completed" | "queued" | "in-progress"),
            "stats": {
                "malicious": int,
                "suspicious": int,
                "undetected": int,
                "harmless": int
            },
            "threat_verdict": str,
            "scan_date": str (ISO format),
            "message": str,
            "user_id": str
        }
    
    Errors:
        - "VirusTotal API key not found in agent state" - API key missing
        - "Invalid VirusTotal API key" - API key invalid
        - "Analysis not found" - Invalid analysis_id
        - "API error {code}" - Other API errors
        - "Request timeout" - Network timeout
    
    Note:
        Analysis status can be:
        - "queued": Analysis is waiting to be processed
        - "in-progress": Analysis is currently running
        - "completed": Analysis finished, results available
    
        If status is "queued" or "in-progress", you may need to wait and check again later.
    
    Example:
        User: "Check the status of analysis u-1234567890abcdef"
        Tool call: get_analysis(analysis_id="u-1234567890abcdef")
        Returns: JSON with analysis status and detection results
    """
    try:
        safe_log_debug(logger, f"[get_analysis] Starting execution", analysis_id=analysis_id)
        
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[get_analysis] API key retrieved", api_key_masked=masked_key)
        
        if not api_key:
            error_msg = "VirusTotal API key not found in agent state. Ensure 'api_keys.API_KEY' is set in agent state."
            safe_log_error(logger, f"[get_analysis] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        endpoint = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
        headers = {
            "x-apikey": api_key,
            "Accept": "application/json"
        }
        
        safe_log_info(logger, f"[get_analysis] Querying VirusTotal analysis API", 
                     endpoint=endpoint, analysis_id=analysis_id, api_key_masked=masked_key)

        response = requests.get(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[get_analysis] API response received", 
                      status_code=response.status_code)

        if response.status_code == 401:
            error_msg = "Invalid VirusTotal API key. Please verify the API key is correct and active."
            safe_log_error(logger, f"[get_analysis] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code == 404:
            error_msg = f"Analysis not found: {analysis_id}. The analysis ID may be invalid or the analysis may have expired."
            safe_log_info(logger, f"[get_analysis] {error_msg}", analysis_id=analysis_id)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        elif response.status_code >= 400:
            error_text = response.text[:200] if hasattr(response, 'text') else "Unknown error"
            error_msg = f"VirusTotal API error {response.status_code}: {error_text}"
            safe_log_error(logger, f"[get_analysis] {error_msg}", 
                         status_code=response.status_code)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        try:
            data = response.json()
            safe_log_info(logger, f"[get_analysis] Successfully retrieved analysis results", analysis_id=analysis_id)
            
            analysis_data = data.get("data", {})
            attributes = analysis_data.get("attributes", {})
            stats = attributes.get("stats", {})
            analysis_status = attributes.get("status", "unknown")
            
            # If details=True, return the complete raw API response
            if details:
                return json.dumps(data, indent=2)
            
            # Otherwise return summary format
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            if malicious > 0:
                threat_verdict = f"MALICIOUS ({malicious} detections)"
            elif suspicious > 0:
                threat_verdict = f"SUSPICIOUS ({suspicious} detections)"
            elif stats.get("undetected", 0) > 0:
                threat_verdict = "UNDETECTED"
            else:
                threat_verdict = "CLEAN"
            
            result = {
                "status": "success",
                "analysis_id": analysis_id,
                "analysis_status": analysis_status,
                "stats": stats,
                "threat_verdict": threat_verdict,
                "scan_date": attributes.get("date"),
                "message": f"Analysis {analysis_status}. {threat_verdict}",
                "user_id": runtime.state.get("user_id")
            }
            return json.dumps(result, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing VirusTotal API response: {str(parse_error)}"
            safe_log_error(logger, f"[get_analysis] {error_msg}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout after 30 seconds. VirusTotal API may be slow or unavailable."
        safe_log_error(logger, f"[get_analysis] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error querying VirusTotal analysis: {str(request_error)}"
        safe_log_error(logger, f"[get_analysis] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error querying VirusTotal analysis: {str(e)}"
        safe_log_error(logger, f"[get_analysis] {error_msg}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


# Usage with LangChain Agent

if __name__ == "__main__":
    from langchain.agents import create_agent

    # Initialize agent with VirusTotal tools
    tools = [
        virustotal_file_report,
        virustotal_url_report,
        virustotal_domain_report,
        virustotal_ip_report,
        scan_url,
        get_analysis
    ]

    # Create agent with custom state
    agent = create_agent(
        model="claude-sonnet-4-5-20250929",
        tools=tools,
        system_prompt="""You are a cybersecurity threat intelligence analyst. 
        Use the VirusTotal tools to analyze files, URLs, domains, and IP addresses 
        for security threats. Provide detailed threat assessments and recommendations.""",
        state_schema=VirusTotalSecurityAgentState
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
            "API_KEY": os.getenv("VT_API_KEY", "your_api_key_here")
        },
        "threat_context": {}
    }
