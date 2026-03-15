"""
DNSDumpster Tools for LangChain Agents

This module provides LangChain tools for comprehensive DNS reconnaissance using DNSDumpster.
DNSDumpster performs passive DNS enumeration by querying multiple data sources including:
- DNSDumpster.com
- Netcraft
- VirusTotal
- SSL Certificate Transparency (crt.sh)
- PassiveDNS

The tool discovers subdomains, DNS records (A, MX, NS, TXT), ASN information, geolocation data,
and server types for both the main domain and discovered subdomains.

Reference: shared/modules/tools/osint/dnsdumpster-master/dnsdumpster.py

Key Features:
- Multi-source subdomain enumeration
- Comprehensive DNS record collection (A, MX, NS, TXT)
- ASN and geolocation intelligence
- Server type detection
- Passive reconnaissance (no direct queries to target)

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.osint.dnsdumpster_langchain import dnsdumpster_search
    
    agent = create_agent(
        model=llm,
        tools=[dnsdumpster_search],
        system_prompt="You are a DNS reconnaissance specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Perform DNS reconnaissance on example.com"}],
        "user_id": "analyst_001"
    })
"""

import json
import sys
import os
import re
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/dnsdumpster_tool.log")


class DNSDumpsterSecurityAgentState(AgentState):
    """Extended agent state for DNSDumpster operations."""
    user_id: str = ""


def _get_dnsdumpster_module_path() -> str:
    """Get the path to the dnsdumpster-master module."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dnsdumpster_path = os.path.join(current_dir, "dnsdumpster-master")
    return dnsdumpster_path


def _import_dnsdumpster_module():
    """Import the dnsdumpster module by adding it to sys.path."""
    dnsdumpster_path = _get_dnsdumpster_module_path()
    if dnsdumpster_path not in sys.path:
        sys.path.insert(0, dnsdumpster_path)
    
    try:
        # NOTE: `dnsdumpster` is a vendored module under `dnsdumpster-master/` and is
        # imported via a runtime sys.path insert above. Static analyzers (pyright)
        # can't resolve this dynamic import, so we use importlib here.
        import importlib
        return importlib.import_module("dnsdumpster")
    except ImportError as e:
        safe_log_error(logger, "[_import_dnsdumpster_module] Import failed", 
                      error=str(e), dnsdumpster_path=dnsdumpster_path)
        raise


@tool
def dnsdumpster_search(
    runtime: ToolRuntime,
    domain: str
) -> str:
    """
    Perform comprehensive DNS reconnaissance on a target domain.
    
    This tool performs passive DNS enumeration by querying multiple data sources to discover
    subdomains, DNS records, ASN information, geolocation data, and server types. It uses
    multiple enumeration engines including DNSDumpster, Netcraft, VirusTotal, and SSL
    Certificate Transparency logs.
    
    What it does:
        - Discovers subdomains using multiple passive data sources
        - Resolves A records for discovered subdomains
        - Collects MX (mail exchange) records for the domain
        - Collects NS (name server) records for the domain
        - Collects TXT records for the domain
        - Retrieves ASN (Autonomous System Number) information for IPs
        - Performs geolocation lookup for IP addresses
        - Detects server types (web server software) for domain and subdomains
        - Returns comprehensive DNS intelligence in structured format
    
    When to use:
        - User asks to "enumerate subdomains" or "find subdomains for a domain"
        - Need comprehensive DNS reconnaissance on a target domain
        - Performing passive reconnaissance (no direct queries to target)
        - Need to discover DNS infrastructure (MX, NS, TXT records)
        - Want to identify ASN and geolocation of domain infrastructure
        - Need to map out all DNS records for a domain
        - Performing initial reconnaissance before active scanning
    
    When NOT to use:
        - Need real-time DNS queries (use webc_resolve_domain_ips instead - faster)
        - Only need basic A record resolution (use webc_resolve_domain_ips instead)
        - Need active DNS enumeration (use amass_enum instead)
        - Domain requires authentication or is behind firewall
        - Need immediate results (this tool can take 30-120 seconds)
        - Only need WHOIS information (use webc_get_domain_whois instead - faster)
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        domain: Target domain name to perform DNS reconnaissance on.
            Must be a valid domain name (e.g., "example.com", "subdomain.example.com").
            Can include or exclude protocol (http://, https://) - will be stripped.
            Examples: "example.com", "https://example.com", "subdomain.example.com"
    
    Returns:
        JSON string with status and comprehensive DNS reconnaissance results.
        All fields have defaults (empty strings, empty arrays, or null) for consistent parsing.
        
        Success response structure:
        {
            "status": "success",
            "host": "example.com",  // Target domain (always present)
            "server": "nginx/1.18.0",  // Web server type (empty string if unknown)
            "mx": [  // Mail exchange records (empty array if none)
                {
                    "preference": 10,  // Priority (0 if not specified)
                    "exchange": "mail.example.com"  // Mail server hostname
                }
            ],
            "ns": [  // Name server records (empty array if none)
                {
                    "target": "ns1.example.com"  // Name server hostname
                }
            ],
            "txt": [  // TXT records (empty array if none)
                "v=spf1 include:_spf.example.com ~all"
            ],
            "asn": {  // ASN information for main domain IP (null if unavailable)
                "asn": "13335",  // Autonomous System Number
                "asn_cidr": "104.27.160.0/20",  // CIDR block
                "asn_country_code": "US",  // Country code
                "asn_date": "2014-03-28",  // Registration date
                "asn_description": "CLOUDFLARENET - Cloudflare, Inc., US",  // ASN description
                "asn_registry": "arin"  // Registry (arin, ripencc, etc.)
            } | null,
            "subdomains": [  // Discovered subdomains (empty array if none)
                {
                    "subdomain": "www.example.com",  // Subdomain name
                    "subdomain_ip": "192.0.2.1",  // IP address (empty string if unresolved)
                    "server": "cloudflare",  // Web server type (empty string if unknown)
                    "asn": {  // ASN info for subdomain IP (null if unavailable)
                        "asn": "13335",
                        "asn_cidr": "104.27.160.0/20",
                        "asn_country_code": "US",
                        "asn_date": "2014-03-28",
                        "asn_description": "CLOUDFLARENET - Cloudflare, Inc., US",
                        "asn_registry": "arin"
                    } | null
                }
            ],
            "subdomain_count": 15,  // Total subdomains discovered (always present, 0 if none)
            "mx_count": 2,  // Number of MX records (always present)
            "ns_count": 4,  // Number of NS records (always present)
            "txt_count": 1  // Number of TXT records (always present)
        }
        
        Error response structure:
        {
            "status": "error",
            "message": "Error description here"
        }
    
    Examples:
        Basic domain reconnaissance:
            domain="example.com"
            Returns: All subdomains, DNS records, ASN info, and server types
        
        Domain with protocol:
            domain="https://example.com"
            Returns: Same as above (protocol is stripped automatically)
        
        Subdomain enumeration:
            domain="target-company.com"
            Returns: Comprehensive list of all discovered subdomains with IPs and metadata
    
    Related tools:
        - webc_resolve_domain_ips: Faster if you only need A record resolution
        - webc_get_domain_whois: Faster if you only need WHOIS information
        - webc_analyze_domain: Faster if you only need basic domain/IP/WHOIS info
        - amass_enum: For active subdomain enumeration (more comprehensive but slower)
    
    Performance notes:
        - Processing time: 30-120 seconds depending on domain size and data sources
        - Uses multiple enumeration engines in parallel (DNSDumpster, Netcraft, VirusTotal, crt.sh)
        - Results are cached by data sources (may vary between runs)
        - Large domains with many subdomains may take longer
        - Network timeouts may occur if data sources are slow or unreachable
    
    Security notes:
        - This is passive reconnaissance - no direct queries to target domain
        - Uses public data sources and certificate transparency logs
        - Safe for use in penetration testing and security assessments
        - Does not perform active DNS queries that could be logged by target
    """
    try:
        safe_log_info(logger, "[dnsdumpster_search] Starting DNS reconnaissance", domain=domain)
        
        # Validate inputs
        if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
            error_msg = "domain must be a non-empty string"
            safe_log_error(logger, "[dnsdumpster_search] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        domain = domain.strip()
        
        # Remove protocol if present
        if domain.startswith(("http://", "https://")):
            from urllib.parse import urlparse
            parsed = urlparse(domain)
            domain = parsed.netloc or parsed.path
        
        # Remove trailing slashes and whitespace
        domain = domain.rstrip('/').strip()
        
        # Validate domain format (simpler regex after protocol removal)
        # Matches: example.com, subdomain.example.com, example.co.uk
        domain_validator = re.compile(
            r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
        )
        if not domain_validator.match(domain):
            error_msg = f"Invalid domain format: {domain}. Expected format: example.com or subdomain.example.com"
            safe_log_error(logger, "[dnsdumpster_search] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[dnsdumpster_search] Domain validated", domain=domain)
        
        # Import dnsdumpster module
        try:
            dnsdumpster = _import_dnsdumpster_module()
        except ImportError as e:
            error_msg = f"Failed to import dnsdumpster module: {str(e)}. Ensure dnsdumpster-master is available."
            safe_log_error(logger, "[dnsdumpster_search] Import failed", error=str(e))
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[dnsdumpster_search] Module imported, starting enumeration")
        
        # Call dnsdumpster via subprocess using its CLI interface
        # Note: dnsdumpster uses multiprocessing.Manager() which requires __main__ context
        # Using the CLI interface ensures it runs as __main__
        try:
            import subprocess
            import json as json_module
            
            dnsdumpster_script = os.path.join(_get_dnsdumpster_module_path(), "dnsdumpster.py")
            dnsdumpster_dir = _get_dnsdumpster_module_path()
            
            # Use venv Python if available, otherwise use sys.executable
            # Check if we're in a venv
            venv_python = None
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                # We're in a venv
                venv_python = os.path.join(sys.prefix, 'bin', 'python3')
                if not os.path.exists(venv_python):
                    venv_python = sys.executable
            else:
                venv_python = sys.executable
            
            # Calculate project root path (go up from shared/modules/tools/osint/ to project root)
            # dnsdumpster_langchain.py is at: shared/modules/tools/osint/dnsdumpster_langchain.py
            # Project root is 5 levels up
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_file_dir, "..", "..", "..", "..", ".."))
            
            # Set PYTHONPATH to include project root so geolocator/geo.py can import shared.modules.tools.ip2geotools
            # geolocator/geo.py imports: from shared.modules.tools.ip2geotools.databases.noncommercial import DbIpCity
            env = os.environ.copy()
            existing_pythonpath = env.get("PYTHONPATH", "")
            if existing_pythonpath:
                env["PYTHONPATH"] = f"{project_root}{os.pathsep}{existing_pythonpath}"
            else:
                env["PYTHONPATH"] = project_root
            
            # Run dnsdumpster as a script with -d argument (it outputs JSON)
            safe_log_debug(logger, "[dnsdumpster_search] Running subprocess", 
                         script=dnsdumpster_script, python=venv_python, domain=domain, 
                         project_root=project_root, pythonpath=env.get("PYTHONPATH"))
            
            result = subprocess.run(
                [venv_python, dnsdumpster_script, "-d", domain],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=dnsdumpster_dir,  # Run from dnsdumpster directory
                env=env  # Pass environment with PYTHONPATH set
            )
            
            safe_log_debug(logger, "[dnsdumpster_search] Subprocess completed", 
                         returncode=result.returncode, 
                         stdout_len=len(result.stdout), 
                         stderr_len=len(result.stderr))
            
            if result.returncode != 0:
                error_msg = f"DNS enumeration failed: {result.stderr[:200] if result.stderr else 'Unknown error'}"
                safe_log_error(logger, "[dnsdumpster_search] Subprocess failed", 
                             error=result.stderr[:500] if result.stderr else "No error output",
                             stdout_preview=result.stdout[:500])
                return json.dumps({"status": "error", "message": error_msg})
            
            # Parse JSON output from dnsdumpster
            # dnsdumpster outputs JSON to stdout, but may have warnings mixed in
            # Extract JSON by finding the first { and last }
            output = result.stdout.strip()
            if not output:
                error_msg = "DNS enumeration returned empty output"
                safe_log_error(logger, "[dnsdumpster_search] Empty output", 
                             stderr=result.stderr[:500])
                return json.dumps({"status": "error", "message": error_msg})
            
            # Find JSON object in output (warnings may come before JSON)
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                error_msg = "No JSON found in dnsdumpster output"
                safe_log_error(logger, "[dnsdumpster_search] No JSON found", 
                             output_preview=output[:500],
                             stderr_preview=result.stderr[:500] if result.stderr else None)
                return json.dumps({"status": "error", "message": error_msg})
            
            json_output = output[json_start:json_end]
            
            try:
                dns_records = json_module.loads(json_output)
            except json_module.JSONDecodeError as je:
                error_msg = f"Failed to parse dnsdumpster JSON: {str(je)}"
                safe_log_error(logger, "[dnsdumpster_search] JSON parse failed", 
                             error=str(je), 
                             json_preview=json_output[:500],
                             stderr_preview=result.stderr[:500] if result.stderr else None)
                return json.dumps({"status": "error", "message": error_msg})
        except ValueError as ve:
            error_msg = f"Invalid domain: {str(ve)}"
            safe_log_error(logger, "[dnsdumpster_search] Domain validation failed", error=str(ve))
            return json.dumps({"status": "error", "message": error_msg})
        except Exception as e:
            error_msg = f"DNS enumeration failed: {str(e)}"
            safe_log_error(logger, "[dnsdumpster_search] Enumeration failed", 
                         exc_info=True,
                         error=str(e))
            return json.dumps({"status": "error", "message": error_msg})
        
        # Convert result to JSON-serializable format with proper defaults
        # Ensure all fields have defaults for better LLM consumption
        result = {
            "status": "success",
            "host": dns_records.get("host", domain) if dns_records else domain,
            "server": dns_records.get("server", "") if dns_records else "",
            "mx": [],
            "ns": [],
            "txt": [],
            "asn": None,
            "subdomains": [],
            "subdomain_count": 0,
            "mx_count": 0,
            "ns_count": 0,
            "txt_count": 0
        }
        
        # Handle case where dns_records might be None or empty
        if not dns_records:
            safe_log_info(logger, "[dnsdumpster_search] No DNS records returned", domain=domain)
            return json.dumps(result, default=str)
        
        # Process MX records with better error handling
        mx_records = dns_records.get("mx", []) or []
        if mx_records and isinstance(mx_records, list):
            for mx in mx_records:
                try:
                    if hasattr(mx, 'preference') and hasattr(mx, 'exchange'):
                        result["mx"].append({
                            "preference": int(mx.preference) if mx.preference is not None else 0,
                            "exchange": str(mx.exchange).rstrip('.') if mx.exchange else ""
                        })
                    elif isinstance(mx, dict):
                        result["mx"].append({
                            "preference": int(mx.get("preference", 0)) if mx.get("preference") is not None else 0,
                            "exchange": str(mx.get("exchange", "")).rstrip('.')
                        })
                    elif isinstance(mx, str):
                        result["mx"].append({
                            "preference": 0,
                            "exchange": str(mx).rstrip('.')
                        })
                except (AttributeError, ValueError, TypeError) as e:
                    safe_log_debug(logger, "[dnsdumpster_search] Error processing MX record", 
                                 error=str(e), mx_record=str(mx))
                    continue
        
        # Process NS records with better error handling
        ns_records = dns_records.get("ns", []) or []
        if ns_records and isinstance(ns_records, list):
            for ns in ns_records:
                try:
                    if hasattr(ns, 'target'):
                        result["ns"].append({
                            "target": str(ns.target).rstrip('.') if ns.target else ""
                        })
                    elif isinstance(ns, dict):
                        # dnsdumpster-master may return NS entries as {"ns": "...", "ip": "..."} (see geolocator/mxfinder.py)
                        target = ns.get("target") or ns.get("ns") or ""
                        entry = {"target": str(target).rstrip('.')}
                        if ns.get("ip") is not None:
                            entry["ip"] = str(ns.get("ip")).strip()
                        result["ns"].append(entry)
                    elif isinstance(ns, str):
                        result["ns"].append({
                            "target": str(ns).rstrip('.')
                        })
                except (AttributeError, ValueError, TypeError) as e:
                    safe_log_debug(logger, "[dnsdumpster_search] Error processing NS record", 
                                 error=str(e), ns_record=str(ns))
                    continue
        
        # Process TXT records (handle both list and single string)
        txt_records = dns_records.get("txt", []) or []
        if txt_records:
            if isinstance(txt_records, list):
                result["txt"] = [str(txt).strip() for txt in txt_records if txt]
            elif isinstance(txt_records, str):
                result["txt"] = [txt_records.strip()] if txt_records.strip() else []
        result["txt_count"] = len(result["txt"])
        
        # Process ASN information for main domain with better error handling
        asn_info = dns_records.get("asn")
        if asn_info:
            try:
                if isinstance(asn_info, dict):
                    result["asn"] = {
                        "asn": str(asn_info.get("asn", "")) if asn_info.get("asn") else "",
                        "asn_cidr": str(asn_info.get("asn_cidr", "")) if asn_info.get("asn_cidr") else "",
                        "asn_country_code": str(asn_info.get("asn_country_code", "")) if asn_info.get("asn_country_code") else "",
                        "asn_date": str(asn_info.get("asn_date", "")) if asn_info.get("asn_date") else "",
                        "asn_description": str(asn_info.get("asn_description", "")) if asn_info.get("asn_description") else "",
                        "asn_registry": str(asn_info.get("asn_registry", "")) if asn_info.get("asn_registry") else ""
                    }
                elif hasattr(asn_info, '__dict__'):
                    result["asn"] = {
                        "asn": str(getattr(asn_info, 'asn', '')) if getattr(asn_info, 'asn', None) else "",
                        "asn_cidr": str(getattr(asn_info, 'asn_cidr', '')) if getattr(asn_info, 'asn_cidr', None) else "",
                        "asn_country_code": str(getattr(asn_info, 'asn_country_code', '')) if getattr(asn_info, 'asn_country_code', None) else "",
                        "asn_date": str(getattr(asn_info, 'asn_date', '')) if getattr(asn_info, 'asn_date', None) else "",
                        "asn_description": str(getattr(asn_info, 'asn_description', '')) if getattr(asn_info, 'asn_description', None) else "",
                        "asn_registry": str(getattr(asn_info, 'asn_registry', '')) if getattr(asn_info, 'asn_registry', None) else ""
                    }
            except Exception as e:
                safe_log_debug(logger, "[dnsdumpster_search] Error processing ASN info", error=str(e))
                result["asn"] = None
        
        # Process subdomains with better error handling and defaults
        subdomains = dns_records.get("subdomains", []) or []
        if subdomains:
            for sub in subdomains:
                try:
                    if isinstance(sub, dict):
                        subdomain_name = str(sub.get("subdomain", "")).strip()
                        subdomain_ip = str(sub.get("subdomain_ip", "")).strip()
                        subdomain_server = str(sub.get("server", "")).strip()
                        sub_asn = sub.get("asn")
                    else:
                        subdomain_name = str(getattr(sub, 'subdomain', '')).strip()
                        subdomain_ip = str(getattr(sub, 'subdomain_ip', '')).strip()
                        subdomain_server = str(getattr(sub, 'server', '')).strip()
                        sub_asn = getattr(sub, 'asn', None)
                    
                    # Skip empty subdomains
                    if not subdomain_name:
                        continue
                    
                    subdomain_data = {
                        "subdomain": subdomain_name,
                        "subdomain_ip": subdomain_ip,
                        "server": subdomain_server,
                        "asn": None
                    }
                    
                    # Process ASN for subdomain with better error handling
                    if sub_asn:
                        try:
                            if isinstance(sub_asn, dict):
                                subdomain_data["asn"] = {
                                    "asn": str(sub_asn.get("asn", "")) if sub_asn.get("asn") else "",
                                    "asn_cidr": str(sub_asn.get("asn_cidr", "")) if sub_asn.get("asn_cidr") else "",
                                    "asn_country_code": str(sub_asn.get("asn_country_code", "")) if sub_asn.get("asn_country_code") else "",
                                    "asn_date": str(sub_asn.get("asn_date", "")) if sub_asn.get("asn_date") else "",
                                    "asn_description": str(sub_asn.get("asn_description", "")) if sub_asn.get("asn_description") else "",
                                    "asn_registry": str(sub_asn.get("asn_registry", "")) if sub_asn.get("asn_registry") else ""
                                }
                            elif hasattr(sub_asn, '__dict__'):
                                subdomain_data["asn"] = {
                                    "asn": str(getattr(sub_asn, 'asn', '')) if getattr(sub_asn, 'asn', None) else "",
                                    "asn_cidr": str(getattr(sub_asn, 'asn_cidr', '')) if getattr(sub_asn, 'asn_cidr', None) else "",
                                    "asn_country_code": str(getattr(sub_asn, 'asn_country_code', '')) if getattr(sub_asn, 'asn_country_code', None) else "",
                                    "asn_date": str(getattr(sub_asn, 'asn_date', '')) if getattr(sub_asn, 'asn_date', None) else "",
                                    "asn_description": str(getattr(sub_asn, 'asn_description', '')) if getattr(sub_asn, 'asn_description', None) else "",
                                    "asn_registry": str(getattr(sub_asn, 'asn_registry', '')) if getattr(sub_asn, 'asn_registry', None) else ""
                                }
                        except Exception as e:
                            safe_log_debug(logger, "[dnsdumpster_search] Error processing subdomain ASN", 
                                         error=str(e), subdomain=subdomain_name)
                            subdomain_data["asn"] = None
                    
                    result["subdomains"].append(subdomain_data)
                except Exception as e:
                    safe_log_debug(logger, "[dnsdumpster_search] Error processing subdomain", 
                                 error=str(e), subdomain=str(sub))
                    continue
        
        # Set counts for easier LLM consumption
        result["subdomain_count"] = len(result["subdomains"])
        result["mx_count"] = len(result["mx"])
        result["ns_count"] = len(result["ns"])
        
        safe_log_info(logger, "[dnsdumpster_search] DNS reconnaissance complete", 
                     domain=domain,
                     subdomain_count=result["subdomain_count"],
                     mx_count=result["mx_count"],
                     ns_count=result["ns_count"],
                     txt_count=result["txt_count"])
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"DNSDumpster search failed: {str(e)}"
        safe_log_error(logger, "[dnsdumpster_search] Error", 
                     exc_info=True,
                     error=str(e),
                     domain=domain if 'domain' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})
