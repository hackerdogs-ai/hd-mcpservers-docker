"""
Maigret Tool for LangChain Agents

Advanced username search with metadata extraction across 3000+ sites using Maigret.
This tool collects a dossier on a person by username only, checking for accounts on a huge
number of sites and gathering all available information from web pages. Supports profile
page parsing, extraction of personal info, links to other profiles, and recursive search.

Reference: https://github.com/soxoj/maigret

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following configuration:

1. Docker Environment (Required)
   - Description: Maigret requires Docker to execute
   - Setup:
     a) Pull official Docker image: docker pull soxoj/maigret:latest
     b) Ensure Docker is running
   - The tool uses the official soxoj/maigret Docker image
   - The tool will check Docker availability and log errors if not available

2. No Additional Environment Variables Required
   - This tool does not require API keys or external service URLs
   - All configuration is passed via function parameters
   - Optional proxy settings (proxy, tor_proxy, i2p_proxy) can be passed as parameters

Configuration Example:
    agent_state = {
        "user_id": "analyst_001"
        # No environment_variables needed for this tool
        # Optional: proxy settings can be passed as function parameters
    }

Security Notes:
- Usernames are logged for audit purposes (not sensitive, but logged)
- All scraping operations are logged with user_id for audit purposes
- Docker execution provides isolation for scraping operations
- Proxy settings (if provided) are logged (not sensitive, but logged for debugging)
- No sensitive credentials required

================================================================================
Key Features:
================================================================================
- Search across 3000+ websites and services
- Profile page parsing and metadata extraction
- Recursive search by additional data extracted from pages
- Multiple output formats (JSON, CSV, HTML, XMind, PDF, Graph, TXT)
- Configurable site filtering (tags, top sites, specific sites)
- Proxy support (HTTP, SOCKS5, Tor, I2P)
- Concurrent connections for fast scanning
- Username permutation for generating variations

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.osint.maigret_langchain import maigret_search
    
    agent = create_agent(
        model=llm,
        tools=[maigret_search],
        system_prompt="You are an OSINT specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Search for username 'johndoe' across all sites"}],
        "user_id": "analyst_001"
    })
"""

import json
import tempfile
import os
import shutil
import re
from typing import Optional, List, Literal
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/maigret_tool.log")


class MaigretSecurityAgentState(AgentState):
    """Extended agent state for Maigret operations."""
    user_id: str = ""


def _check_docker_available() -> bool:
    """
    Check if Docker is available.
    
    Returns:
        True if Docker is available and accessible, False otherwise.
    """
    docker_client = get_docker_client()
    if docker_client is None:
        safe_log_debug(logger, "[maigret_search] Docker client is None")
        return False
    is_available = docker_client.docker_available
    safe_log_debug(logger, "[maigret_search] Docker availability check", docker_available=is_available)
    return is_available


def _parse_maigret_stdout(stdout: str, usernames: List[str], logger) -> str:
    """
    Parse Maigret's default stdout output into structured JSON.
    
    Extracts:
    - Found accounts: lines starting with "[+]"
    - Summary: "Search by username X returned Y accounts"
    
    Args:
        stdout: Maigret's stdout output
        usernames: List of usernames that were searched
        logger: Logger instance
        
    Returns:
        JSON string with structured results
    """
    results = {}
    current_username = None
    accounts_by_username = {u: [] for u in usernames}
    summaries = {}
    
    # Parse stdout line by line, tracking which username section we're in
    for line in stdout.split('\n'):
        line = line.strip()
        
        # Track which username we're currently processing
        for username in usernames:
            if f"[*] Checking username {username} on:" in line:
                current_username = username
                break
        
        # Extract found accounts: [+] Site Name: URL
        if line.startswith('[+]') and current_username:
            # Format: [+] Site Name: URL or [+] Site: URL
            parts = line[3:].split(':', 1)  # Remove '[+]' and split on first ':'
            if len(parts) == 2:
                site_name = parts[0].strip()
                url = parts[1].strip()
                accounts_by_username[current_username].append({
                    "site": site_name,
                    "url": url
                })
        
        # Extract summary: "Search by username X returned Y accounts"
        for username in usernames:
            if f"Search by username {username} returned" in line:
                summaries[username] = line
                break
    
    # Build results for each username
    for username in usernames:
        accounts = accounts_by_username.get(username, [])
        summary = summaries.get(username)
        
        # If we have a summary, extract account count from it
        account_count = len(accounts)
        if summary:
            match = re.search(r'returned (\d+) accounts?', summary)
            if match:
                account_count = int(match.group(1))
        
        results[username] = {
            "username": username,
            "accounts_found": account_count,
            "sites": accounts,
            "summary": summary or f"Search by username {username} returned {account_count} accounts."
        }
    
    # Return structured JSON
    if len(results) == 1:
        # Single username - return just that result
        result_json = json.dumps(list(results.values())[0], indent=2)
    else:
        # Multiple usernames - return dict
        result_json = json.dumps(results, indent=2)
    
    safe_log_info(logger, "[maigret_search] Complete - returning parsed stdout results", 
                usernames=usernames,
                total_accounts=sum(r["accounts_found"] for r in results.values()),
                output_length=len(result_json))
    
    return result_json


@tool
def maigret_search(
    runtime: ToolRuntime,
    usernames: List[str],
    report_format: Optional[Literal["txt", "csv", "html", "xmind", "pdf", "graph", "json"]] = None,
    json_type: Literal["simple", "ndjson"] = "simple",
    timeout: int = 60,
    retries: int = 3,
    max_connections: int = 100,
    all_sites: bool = False,
    top_sites: Optional[int] = None,
    tags: Optional[str] = None,
    sites: Optional[List[str]] = None,
    use_disabled_sites: bool = False,
    no_recursion: bool = False,
    no_extracting: bool = False,
    with_domains: bool = False,
    permute: bool = False,
    proxy: Optional[str] = None,
    tor_proxy: Optional[str] = None,
    i2p_proxy: Optional[str] = None,
    print_not_found: bool = False,
    print_errors: bool = False,
    verbose: bool = False
) -> str:
    """
    Advanced username search with metadata extraction across 3000+ sites using Maigret.
    
    Maigret collects a dossier on a person by username only, checking for accounts on a huge
    number of sites and gathering all available information from web pages. Supports profile
    page parsing, extraction of personal info, links to other profiles, and recursive search.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        usernames: List of usernames to search (required).
        report_format: Report format - "txt", "csv", "html", "xmind", "pdf", "graph", or "json" (default: None, uses stdout).
            If None, parses Maigret's default stdout output into a structured summary (recommended for LLM consumption).
        json_type: JSON report type - "simple" (default) or "ndjson" (only used when report_format="json").
        
    Returns:
        - If report_format is None (default): Structured JSON with parsed stdout results:
          {
            "username": "example",
            "accounts_found": 5,
            "sites": [
              {"site": "GitHub", "url": "https://github.com/example"},
              ...
            ],
            "summary": "Search by username example returned 5 accounts."
          }
        - If report_format="csv": Raw CSV string (single username) or JSON dict (multiple usernames)
        - If report_format="json": JSON file content (may be large, 19KB-32KB per username)
        - If report_format="txt"/"html"/etc.: File content or stdout verbatim
        timeout: Time in seconds to wait for response to requests (default: 30, range: 1-300).
        retries: Attempts to restart temporarily failed requests (default: 3, range: 0-10).
        max_connections: Allowed number of concurrent connections (default: 100, range: 1-1000).
        all_sites: Use all available sites for scan (default: False). If True, ignores top_sites.
        top_sites: Count of sites for scan ranked by Alexa Top (default: 500, range: 1-3000). Ignored if all_sites=True.
        tags: Comma-separated tags of sites to filter by (e.g., "photo,dating" or "us").
        sites: Optional list of specific site names to limit analysis to (multiple sites).
        use_disabled_sites: Use disabled sites to search (may cause many false positives, default: False).
        no_recursion: Disable recursive search by additional data extracted from pages (default: False).
        no_extracting: Disable parsing pages for additional data and other usernames (default: False).
        with_domains: Enable experimental feature of checking domains on usernames (default: False).
        permute: Permute at least 2 usernames to generate more possible usernames (default: False).
        proxy: Make requests over a proxy (e.g., "socks5://127.0.0.1:1080").
        tor_proxy: Specify URL of your Tor gateway (default: "socks5://127.0.0.1:9050").
        i2p_proxy: Specify URL of your I2P gateway (default: "http://127.0.0.1:4444").
        print_not_found: Print sites where the username was not found (default: False).
        print_errors: Print error messages: connection, captcha, site country ban, etc. (default: False).
        verbose: Display extra information and metrics (default: False).
    
    Returns:
        JSON string with results including:
        - status: "success" or "error"
        - usernames: List of searched usernames
        - results: Dictionary mapping username to found sites with metadata
        - count: Total number of sites found
        - execution_method: "docker" or "official_docker_image"
    """
    temp_dir = None
    volumes = []
    
    try:
        safe_log_info(logger, "[maigret_search] Starting", 
                     usernames=usernames, 
                     report_format=report_format, 
                     timeout=timeout,
                     usernames_count=len(usernames) if usernames else 0)
        
        # Validate inputs
        if not usernames or not isinstance(usernames, list) or len(usernames) == 0:
            error_msg = "usernames must be a non-empty list"
            safe_log_error(logger, "[maigret_search] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        for username in usernames:
            if not isinstance(username, str) or len(username.strip()) == 0:
                error_msg = f"Invalid username in list: {username}"
                safe_log_error(logger, "[maigret_search] Validation failed", error_msg=error_msg, username=username)
                return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[maigret_search] Usernames validated", usernames_count=len(usernames))
        
        # Handle string "None" from LLM (LangChain may convert None to string "None")
        if report_format == "None" or report_format == "none":
            report_format = None
            safe_log_debug(logger, "[maigret_search] Converted string 'None' to actual None", report_format=report_format)
        
        # Validate report_format (None is valid - uses stdout parsing)
        if report_format is not None and report_format not in ["txt", "csv", "html", "xmind", "pdf", "graph", "json"]:
            error_msg = "report_format must be one of: txt, csv, html, xmind, pdf, graph, json (or None for stdout parsing)"
            safe_log_error(logger, "[maigret_search] Validation failed", error_msg=error_msg, report_format=report_format)
            return json.dumps({"status": "error", "message": error_msg})
        
        if json_type not in ["simple", "ndjson"]:
            error_msg = "json_type must be 'simple' or 'ndjson'"
            safe_log_error(logger, "[maigret_search] Validation failed", error_msg=error_msg, json_type=json_type)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not (1 <= timeout <= 300):
            error_msg = "timeout must be between 1 and 300 seconds"
            safe_log_error(logger, "[maigret_search] Validation failed", error_msg=error_msg, timeout=timeout)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not (0 <= retries <= 10):
            error_msg = "retries must be between 0 and 10"
            safe_log_error(logger, "[maigret_search] Validation failed", error_msg=error_msg, retries=retries)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not (1 <= max_connections <= 1000):
            error_msg = "max_connections must be between 1 and 1000"
            safe_log_error(logger, "[maigret_search] Validation failed", error_msg=error_msg, max_connections=max_connections)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[maigret_search] All parameters validated", 
                      report_format=report_format,
                      timeout=timeout,
                      retries=retries,
                      max_connections=max_connections)
        
        # Docker-only execution
        safe_log_debug(logger, "[maigret_search] Checking Docker availability")
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Pull Docker image: docker pull soxoj/maigret:latest\n"
                "2. Ensure Docker is running"
            )
            safe_log_error(logger, "[maigret_search] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_info(logger, "[maigret_search] Docker available, proceeding with execution", 
                     usernames=usernames,
                     report_format=report_format)
        
        # Build command arguments
        args = []
        
        # Timeout
        args.extend(["--timeout", str(timeout)])
        
        # Retries
        if retries > 0:
            args.extend(["--retries", str(retries)])
        
        # Max connections
        args.extend(["-n", str(max_connections)])
        
        # Recursion/extraction options
        if no_recursion:
            args.append("--no-recursion")
        
        if no_extracting:
            args.append("--no-extracting")
        
        # Domain checking
        if with_domains:
            args.append("--with-domains")
        
        # Permute
        if permute and len(usernames) >= 2:
            args.append("--permute")
        
        # Proxy options
        if proxy:
            args.extend(["--proxy", proxy])
        
        if tor_proxy:
            args.extend(["--tor-proxy", tor_proxy])
        
        if i2p_proxy:
            args.extend(["--i2p-proxy", i2p_proxy])
        
        # Site filtering
        if all_sites:
            args.append("-a")
        elif top_sites is not None:
            if not (1 <= top_sites <= 3000):
                error_msg = "top_sites must be between 1 and 3000"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            args.extend(["--top-sites", str(top_sites)])
        
        if tags:
            args.extend(["--tags", tags])
        
        if sites:
            for site in sites:
                args.extend(["--site", site])
        
        if use_disabled_sites:
            args.append("--use-disabled-sites")
        
        # Output options
        if print_not_found:
            args.append("--print-not-found")
        
        if print_errors:
            args.append("--print-errors")
        
        if verbose:
            args.append("--verbose")
        
        # Report formats (only add format flags if explicitly requested)
        # Default (None) uses stdout which is concise and LLM-friendly
        if report_format == "txt":
            args.append("-T")
        elif report_format == "csv":
            args.append("-C")
        elif report_format == "html":
            args.append("-H")
        elif report_format == "xmind":
            args.append("-X")
        elif report_format == "pdf":
            args.append("-P")
        elif report_format == "graph":
            args.append("-G")
        elif report_format == "json":
            args.extend(["-J", json_type])
        
        # Setup output directory for reports (only if format flag was used)
        if report_format and report_format in ["txt", "csv", "html", "xmind", "pdf", "graph", "json"]:
            temp_dir = tempfile.mkdtemp()
            container_output_path = "/app/reports"
            volumes.append(f"{temp_dir}:{container_output_path}")
            args.extend(["--folderoutput", container_output_path])
            safe_log_debug(logger, "[maigret_search] Created temporary output directory", 
                         temp_dir=temp_dir, 
                         container_path=container_output_path)
        
        # Add usernames (positional arguments)
        args.extend(usernames)
        
        # Execute in Docker using official soxoj/maigret image
        # Calculate timeout: (timeout per request * number of usernames * sites) + buffer
        # For top 500 sites with 30s timeout: 500 * 30 = 15000s worst case, but concurrent connections reduce this
        # Use a more reasonable timeout based on max_connections
        estimated_sites = top_sites if top_sites and not all_sites else 500
        if all_sites:
            estimated_sites = 3000  # Max sites in database
        execution_timeout = (timeout * estimated_sites / max_connections) + (retries * timeout) + 300  # Buffer
        execution_timeout = min(execution_timeout, 3600)  # Cap at 1 hour
        
        # Respect DOCKER_TOOL_EXECUTION_TIMEOUT environment variable as minimum
        # If set, ensures execution_timeout is at least this value (useful for long-running scans)
        import os
        env_min_timeout = os.getenv("DOCKER_TOOL_EXECUTION_TIMEOUT")
        if env_min_timeout:
            min_timeout = int(env_min_timeout)
            if min_timeout > 0:
                execution_timeout = max(execution_timeout, min_timeout)
        
        safe_log_info(logger, "[maigret_search] Executing in Docker", 
                     command="maigret",
                     args_count=len(args),
                     estimated_sites=estimated_sites,
                     execution_timeout=int(execution_timeout),
                     volumes_count=len(volumes))
        
        docker_result = execute_in_docker("maigret", args, timeout=int(execution_timeout), volumes=volumes if volumes else None)
        
        safe_log_debug(logger, "[maigret_search] Docker execution complete", 
                      status=docker_result.get("status"),
                      has_stdout=bool(docker_result.get("stdout")),
                      has_stderr=bool(docker_result.get("stderr")))
        
        if docker_result["status"] != "success":
            error_msg = f"Maigret failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, "[maigret_search] Docker execution failed", 
                         stderr=docker_result.get('stderr', ''),
                         docker_message=docker_result.get('message', ''),
                         error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Parse output
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        safe_log_debug(logger, "[maigret_search] Parsing output", 
                      stdout_length=len(stdout),
                      stderr_length=len(stderr),
                      temp_dir=temp_dir if temp_dir else None,
                      report_format=report_format)
        
        # DEFAULT: Parse stdout (when report_format is None) - concise and LLM-friendly
        if report_format is None:
            return _parse_maigret_stdout(stdout, usernames, logger)
        
        results = {username: [] for username in usernames}
        total_count = 0
        
        # For JSON format with single username: return the JSON file content directly, verbatim
        if report_format == "json" and temp_dir and len(usernames) == 1:
            try:
                username = usernames[0]
                json_file = None
                # Try Maigret's naming pattern: report_{username}_{type}.json
                if json_type == "simple":
                    json_file = os.path.join(temp_dir, f"report_{username}_simple.json")
                    # Fallback to old naming
                    if not os.path.exists(json_file):
                        json_file = os.path.join(temp_dir, f"{username}.json")
                else:  # ndjson
                    json_file = os.path.join(temp_dir, f"report_{username}_ndjson.json")
                    # Fallback to old naming
                    if not os.path.exists(json_file):
                        json_file = os.path.join(temp_dir, f"{username}.ndjson")
                
                if json_file and os.path.exists(json_file):
                    # Read raw JSON file and return directly, verbatim - no wrapper
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_content = f.read()
                    # Cleanup temp directory
                    if os.path.exists(temp_dir):
                        try:
                            shutil.rmtree(temp_dir)
                        except Exception:
                            pass
                    # Return JSON file content directly, verbatim - no wrapper
                    safe_log_info(logger, "[maigret_search] Complete - returning JSON file content verbatim", 
                                usernames=usernames,
                                json_file=json_file,
                                json_content_length=len(json_content))
                    return json_content
            except Exception as e:
                safe_log_error(logger, "[maigret_search] Error reading JSON file", 
                             exc_info=True, 
                             error=str(e),
                             json_file=json_file if 'json_file' in locals() else None)
                # Fall through to wrapper format
        
        # For multiple usernames: return JSON files directly as dictionary (no wrapper)
        if report_format == "json" and temp_dir:
            json_results = {}
            try:
                # Look for JSON files in the output directory
                # Maigret saves files as: report_{username}_{json_type}.json
                for username in usernames:
                    json_file = None
                    # Try Maigret's naming pattern: report_{username}_{type}.json
                    if json_type == "simple":
                        json_file = os.path.join(temp_dir, f"report_{username}_simple.json")
                        # Fallback to old naming
                        if not os.path.exists(json_file):
                            json_file = os.path.join(temp_dir, f"{username}.json")
                    else:  # ndjson
                        json_file = os.path.join(temp_dir, f"report_{username}_ndjson.json")
                        # Fallback to old naming
                        if not os.path.exists(json_file):
                            json_file = os.path.join(temp_dir, f"{username}.ndjson")
                    
                    if os.path.exists(json_file):
                        # Read raw JSON file and return as-is (verbatim, no parsing)
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_results[username] = f.read()  # Return as raw string, not parsed
            except Exception as e:
                safe_log_error(logger, f"[maigret_search] Error reading JSON files: {str(e)}", exc_info=True)
            
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            
            # Return JSON files as dictionary mapping username to JSON content - no wrapper
            if json_results:
                safe_log_info(logger, "[maigret_search] Complete - returning JSON files verbatim", 
                            usernames=usernames,
                            files_count=len(json_results))
                return json.dumps(json_results, indent=2)
        
        # For CSV format: check for CSV files in output directory
        if report_format == "csv" and temp_dir and os.path.exists(temp_dir):
            csv_results = {}
            try:
                # Look for CSV files in the output directory
                # Maigret saves files as: report_{username}.csv or {username}.csv
                for username in usernames:
                    csv_file = None
                    # Try Maigret's naming pattern: report_{username}.csv
                    csv_file = os.path.join(temp_dir, f"report_{username}.csv")
                    # Fallback to simple naming
                    if not os.path.exists(csv_file):
                        csv_file = os.path.join(temp_dir, f"{username}.csv")
                    
                    if os.path.exists(csv_file):
                        # Read raw CSV file and return as-is (verbatim)
                        with open(csv_file, 'r', encoding='utf-8') as f:
                            csv_results[username] = f.read()
            except Exception as e:
                safe_log_error(logger, f"[maigret_search] Error reading CSV files: {str(e)}", exc_info=True)
            
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            
            # Return CSV files as dictionary mapping username to CSV content - no wrapper
            if csv_results:
                if len(csv_results) == 1 and len(usernames) == 1:
                    # Single CSV file - return it verbatim
                    safe_log_info(logger, "[maigret_search] Complete - returning CSV file content verbatim", 
                                usernames=usernames)
                    return list(csv_results.values())[0]
                else:
                    # Multiple CSV files - return as dict
                    safe_log_info(logger, "[maigret_search] Complete - returning CSV files verbatim", 
                                usernames=usernames,
                                files_count=len(csv_results))
                    return json.dumps(csv_results, indent=2)
        
        # For other non-JSON formats (txt, html, xmind, pdf, graph) or if files not found: return stdout/stderr verbatim
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        
        # Return stdout/stderr verbatim - no wrapper
        safe_log_info(logger, "[maigret_search] Complete - returning stdout verbatim", 
                    usernames=usernames,
                    stdout_length=len(stdout) if stdout else 0,
                    stderr_length=len(stderr) if stderr else 0)
        return stdout if stdout else stderr
        
    except Exception as e:
        safe_log_error(logger, "[maigret_search] Error", 
                     exc_info=True, 
                     error=str(e),
                     usernames=usernames)
        return json.dumps({"status": "error", "message": f"Maigret search failed: {str(e)}"})
    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                safe_log_info(logger, "[maigret_search] Cleaned up temporary directory", temp_dir=temp_dir)
            except Exception as e:
                safe_log_error(logger, "[maigret_search] Error cleaning up temporary directory", 
                             exc_info=True,
                             temp_dir=temp_dir,
                             error=str(e))
