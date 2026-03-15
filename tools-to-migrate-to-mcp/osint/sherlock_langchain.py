"""
Sherlock Tool for LangChain Agents

Username enumeration across 300+ sites using Sherlock.
This tool searches for usernames across social networks, forums, and other websites
to find where a username is registered. It checks hundreds of sites simultaneously
and returns results in various formats (CSV, JSON, XLSX).

Reference: https://github.com/sherlock-project/sherlock

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following configuration:

1. Docker Environment (Required)
   - Description: Sherlock requires Docker to execute
   - Setup:
     a) Pull official Docker image: docker pull sherlock/sherlock:latest
     b) Ensure Docker is running
   - The tool uses the official sherlock/sherlock Docker image
   - The tool will check Docker availability and log errors if not available

2. No Additional Environment Variables Required
   - This tool does not require API keys or external service URLs
   - All configuration is passed via function parameters
   - Optional site filtering can be passed as parameters

Configuration Example:
    agent_state = {
        "user_id": "analyst_001"
        # No environment_variables needed for this tool
    }

Security Notes:
- Usernames are logged for audit purposes (not sensitive, but logged)
- All scraping operations are logged with user_id for audit purposes
- Docker execution provides isolation for scraping operations
- No sensitive credentials required

================================================================================
Key Features:
================================================================================
- Search across 300+ social networks and websites
- Multiple output formats (CSV, JSON, XLSX)
- Configurable timeout per request
- Site filtering (specific sites or all sites)
- NSFW site filtering option
- Fast parallel checking across multiple sites
- Docker-based execution for isolation

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.osint.sherlock_langchain import sherlock_enum
    
    agent = create_agent(
        model=llm,
        tools=[sherlock_enum],
        system_prompt="You are an OSINT specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Find where username 'johndoe' is registered"}],
        "user_id": "analyst_001"
    })
"""

import json
import csv
import io
import tempfile
import os
import shutil
import re
from pathlib import Path
from typing import Optional, List, Literal
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/sherlock_tool.log")


class SherlockSecurityAgentState(AgentState):
    """Extended agent state for Sherlock operations."""
    user_id: str = ""


def _check_docker_available() -> bool:
    """
    Check if Docker is available.
    
    Returns:
        True if Docker is available and accessible, False otherwise.
    """
    docker_client = get_docker_client()
    if docker_client is None:
        safe_log_debug(logger, "[sherlock_enum] Docker client is None")
        return False
    is_available = docker_client.docker_available
    safe_log_debug(logger, "[sherlock_enum] Docker availability check", docker_available=is_available)
    return is_available


def _parse_sherlock_stdout(stdout: str, usernames: List[str], logger) -> str:
    """
    Parse Sherlock's default stdout output into structured JSON.
    
    Extracts:
    - Found accounts: lines starting with "[+]"
    - Summary: "[*] Search completed with X results"
    
    Args:
        stdout: Sherlock's stdout output
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
            # Format: [+] Site Name: URL
            parts = line[3:].split(':', 1)  # Remove '[+]' and split on first ':'
            if len(parts) == 2:
                site_name = parts[0].strip()
                url = parts[1].strip()
                accounts_by_username[current_username].append({
                    "site": site_name,
                    "url": url
                })
        
        # Extract summary: "[*] Search completed with X results"
        if "[*] Search completed with" in line:
            match = re.search(r'Search completed with (\d+) results?', line)
            if match:
                total_results = int(match.group(1))
                summaries['total'] = total_results
                summaries['summary'] = line
    
    # Build results for each username
    for username in usernames:
        accounts = accounts_by_username.get(username, [])
        
        # Use summary if available, otherwise generate one
        summary = summaries.get('summary', f"Search completed with {len(accounts)} results.")
        # For single username, use the summary directly; for multiple, include total if available
        if len(usernames) == 1 and summaries.get('total'):
            # Single username: use the actual summary from stdout
            summary = summaries['summary']
        
        results[username] = {
            "username": username,
            "accounts_found": len(accounts),
            "sites": accounts,
            "summary": summary
        }
    
    # Add total summary if available and multiple usernames
    if summaries.get('total') and len(usernames) > 1:
        results['_summary'] = {
            "total_results": summaries['total'],
            "summary": summaries['summary']
        }
    
    # Return structured JSON
    if len(results) == 1 and '_summary' not in results:
        # Single username - return just that result
        result_json = json.dumps(list(results.values())[0], indent=2)
    else:
        # Multiple usernames or with summary - return dict
        result_json = json.dumps(results, indent=2)
    
    safe_log_info(logger, "[sherlock_enum] Complete - returning parsed stdout results", 
                usernames=usernames,
                total_accounts=sum(r.get("accounts_found", 0) for r in results.values() if isinstance(r, dict) and "accounts_found" in r),
                output_length=len(result_json))
    
    return result_json


def _apply_limit_to_results(result_json: str, limit: int, usernames: List[str], logger) -> str:
    """
    Apply limit to parsed Sherlock results by truncating sites list per username.
    
    Args:
        result_json: JSON string with parsed results
        limit: Maximum number of results to return per username
        usernames: List of usernames that were searched
        logger: Logger instance
        
    Returns:
        JSON string with limited results
    """
    try:
        # Parse the JSON
        results = json.loads(result_json)
        
        # Handle single username result (dict) vs multiple usernames (dict with username keys)
        if isinstance(results, dict):
            # Check if it's a single username result (has "username" key) or multiple usernames
            if "username" in results and "sites" in results:
                # Single username result
                original_count = len(results.get("sites", []))
                if original_count > limit:
                    results["sites"] = results["sites"][:limit]
                    results["accounts_found"] = limit
                    # Update summary to reflect limit
                    results["summary"] = f"[*] Search completed with {limit} results (showing top {limit} of {original_count} total)"
                    safe_log_info(logger, "[sherlock_enum] Applied limit to single username result",
                                username=results.get("username"),
                                original_count=original_count,
                                limited_count=limit)
            else:
                # Multiple usernames or has _summary
                for username in usernames:
                    if username in results and isinstance(results[username], dict):
                        user_result = results[username]
                        if "sites" in user_result:
                            original_count = len(user_result["sites"])
                            if original_count > limit:
                                user_result["sites"] = user_result["sites"][:limit]
                                user_result["accounts_found"] = limit
                                # Update summary to reflect limit
                                user_result["summary"] = f"[*] Search completed with {limit} results (showing top {limit} of {original_count} total)"
                                safe_log_info(logger, "[sherlock_enum] Applied limit to username result",
                                            username=username,
                                            original_count=original_count,
                                            limited_count=limit)
        
        # Re-serialize to JSON
        if isinstance(results, dict) and "username" in results and "_summary" not in results:
            # Single username - return just that result
            return json.dumps(results, indent=2)
        else:
            # Multiple usernames or with summary - return dict
            return json.dumps(results, indent=2)
            
    except json.JSONDecodeError as e:
        safe_log_error(logger, "[sherlock_enum] Error parsing JSON for limit application", 
                      error=str(e), exc_info=True)
        # Return original if parsing fails
        return result_json
    except Exception as e:
        safe_log_error(logger, "[sherlock_enum] Error applying limit to results", 
                      error=str(e), exc_info=True)
        # Return original if limit application fails
        return result_json


@tool
def sherlock_enum(
    runtime: ToolRuntime,
    usernames: List[str],
    output_format: Optional[Literal["csv", "json", "xlsx"]] = None,
    timeout: int = 60,
    nsfw: bool = False,
    sites: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> str:
    """
    Username enumeration across 300+ sites using Sherlock.
    
    Searches for usernames across social networks and returns results in specified format.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        usernames: List of usernames to search (required).
        output_format: Output format - "csv", "json", or "xlsx" (default: None, uses stdout).
            If None, parses Sherlock's default stdout output into a structured summary (recommended for LLM consumption).
        timeout: Timeout in seconds for each request (default: 60, range: 1-3600).
        nsfw: Include NSFW sites in search (default: False).
        sites: Optional list of specific sites to search (default: all sites).
        limit: Maximum number of results to return per username (default: None, no limit).
            If specified, results are post-filtered to return only the top N results.
            Range: 1-500. Recommended: 10-50 for LLM consumption.
    
    Returns:
        - If output_format is None (default): Structured JSON with parsed stdout results:
          {
            "username": "example",
            "accounts_found": 5,
            "sites": [
              {"site": "GitHub", "url": "https://github.com/example"},
              ...
            ],
            "summary": "[*] Search completed with 5 results"
          }
        - If output_format="csv": Raw CSV string (single username) or JSON dict (multiple usernames)
        - If output_format="json": JSON file content (may be large)
        - If output_format="xlsx": XLSX file (binary, returned as base64 or path)
    """
    try:
        safe_log_info(logger, "[sherlock_enum] Starting", 
                     usernames=usernames, 
                     output_format=output_format, 
                     timeout=timeout, 
                     nsfw=nsfw,
                     limit=limit,
                     usernames_count=len(usernames) if usernames else 0)
        
        # Validate inputs
        if not usernames or not isinstance(usernames, list) or len(usernames) == 0:
            error_msg = "usernames must be a non-empty list"
            safe_log_error(logger, "[sherlock_enum] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Validate each username
        for username in usernames:
            if not isinstance(username, str) or len(username.strip()) == 0:
                error_msg = f"Invalid username in list: {username}"
                safe_log_error(logger, "[sherlock_enum] Validation failed", error_msg=error_msg, username=username)
                return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[sherlock_enum] Usernames validated", usernames_count=len(usernames))
        
        # Handle string "None" from LLM (LangChain may convert None to string "None")
        if output_format == "None" or output_format == "none":
            output_format = None
            safe_log_debug(logger, "[sherlock_enum] Converted string 'None' to actual None", output_format=output_format)
        
        if output_format is not None and output_format not in ["csv", "json", "xlsx"]:
            error_msg = "output_format must be 'csv', 'json', 'xlsx', or None (for stdout)"
            safe_log_error(logger, "[sherlock_enum] Validation failed", error_msg=error_msg, output_format=output_format)
            return json.dumps({"status": "error", "message": error_msg})
        
        if timeout < 1 or timeout > 3600:
            error_msg = "timeout must be between 1 and 3600 seconds"
            safe_log_error(logger, "[sherlock_enum] Validation failed", error_msg=error_msg, timeout=timeout)
            return json.dumps({"status": "error", "message": error_msg})
        
        if limit is not None and (limit < 1 or limit > 500):
            error_msg = "limit must be between 1 and 500"
            safe_log_error(logger, "[sherlock_enum] Validation failed", error_msg=error_msg, limit=limit)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[sherlock_enum] All parameters validated", 
                      output_format=output_format,
                      timeout=timeout,
                      nsfw=nsfw)
        
        # Docker-only execution
        safe_log_debug(logger, "[sherlock_enum] Checking Docker availability")
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Pull Docker image: docker pull sherlock/sherlock:latest\n"
                "2. Ensure Docker is running"
            )
            safe_log_error(logger, "[sherlock_enum] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_info(logger, "[sherlock_enum] Docker available, proceeding with execution", 
                     usernames=usernames,
                     output_format=output_format)
        
        # Build command arguments
        args = []
        volumes = []
        output_file_path = None
        
        safe_log_debug(logger, "[sherlock_enum] Building command arguments", output_format=output_format)
        
        # Output format - handle file-based outputs (only if explicitly requested)
        # Default (None) uses stdout which is concise and LLM-friendly
        # Note: --json is for INPUT (loading data), not output
        # For JSON output, use --output with .json extension
        # For CSV/XLSX, use --csv/--xlsx flags (output to stdout or default location)
        if output_format == "json":
            # JSON output via --output with .json extension
            temp_dir = tempfile.mkdtemp()
            if len(usernames) == 1:
                output_file_path = os.path.join(temp_dir, f"{usernames[0]}.json")
                container_json_path = f"/output/{usernames[0]}.json"
            else:
                # Multiple usernames - use folderoutput
                output_file_path = temp_dir  # Will contain multiple files
                container_json_path = "/output"
            volumes.append(f"{temp_dir}:/output")
            if len(usernames) == 1:
                args.extend(["--output", container_json_path])
            else:
                args.extend(["--folderoutput", container_json_path])
        elif output_format == "csv":
            # CSV output via --output with .csv extension
            temp_dir = tempfile.mkdtemp()
            if len(usernames) == 1:
                output_file_path = os.path.join(temp_dir, f"{usernames[0]}.csv")
                container_csv_path = f"/output/{usernames[0]}.csv"
            else:
                # Multiple usernames - use folderoutput
                output_file_path = temp_dir  # Will contain multiple files
                container_csv_path = "/output"
            volumes.append(f"{temp_dir}:/output")
            if len(usernames) == 1:
                args.extend(["--csv", "--output", container_csv_path])
            else:
                args.extend(["--csv", "--folderoutput", container_csv_path])
        elif output_format == "xlsx":
            # XLSX output
            temp_dir = tempfile.mkdtemp()
            if len(usernames) == 1:
                output_file_path = os.path.join(temp_dir, f"{usernames[0]}.xlsx")
                container_xlsx_path = f"/output/{usernames[0]}.xlsx"
                volumes.append(f"{temp_dir}:/output")
                args.extend(["--xlsx", "--output", container_xlsx_path])
            else:
                output_file_path = temp_dir  # Will contain multiple files
                container_xlsx_path = "/output"
                volumes.append(f"{temp_dir}:/output")
                args.extend(["--xlsx", "--folderoutput", container_xlsx_path])
        
        # Timeout
        args.extend(["--timeout", str(timeout)])
        
        # NSFW flag
        if nsfw:
            args.append("--nsfw")
        
        # Site filtering
        if sites:
            for site in sites:
                args.extend(["--site", site])
        
        # Add --print-found flag to ensure stdout output (even when file formats are used)
        # This ensures we can parse stdout for default behavior
        args.append("--print-found")
        
        # Add usernames (positional arguments)
        args.extend(usernames)
        
        # Execute in Docker using official sherlock/sherlock image
        # Calculate timeout: (timeout per request * number of usernames) + buffer
        execution_timeout = (timeout * len(usernames) * 2) + 120  # Buffer for processing
        
        # Respect DOCKER_TOOL_EXECUTION_TIMEOUT environment variable as minimum
        # If set, ensures execution_timeout is at least this value (useful for long-running scans)
       
        env_min_timeout = os.getenv("DOCKER_TOOL_EXECUTION_TIMEOUT")
        if env_min_timeout:
            min_timeout = int(env_min_timeout)
            if min_timeout > 0:
                execution_timeout = max(execution_timeout, min_timeout)
        
        safe_log_info(logger, "[sherlock_enum] Executing in Docker", 
                     command="sherlock",
                     args_count=len(args),
                     execution_timeout=execution_timeout,
                     volumes_count=len(volumes))
        
        docker_result = execute_in_docker("sherlock", args, timeout=execution_timeout, volumes=volumes if volumes else None)
        
        safe_log_debug(logger, "[sherlock_enum] Docker execution complete", 
                      status=docker_result.get("status"),
                      has_stdout=bool(docker_result.get("stdout")),
                      has_stderr=bool(docker_result.get("stderr")))
        
        if docker_result["status"] != "success":
            error_msg = f"Sherlock failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, "[sherlock_enum] Docker execution failed", 
                         stderr=docker_result.get('stderr', ''),
                         docker_message=docker_result.get('message', ''),
                         error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Parse output
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        safe_log_debug(logger, "[sherlock_enum] Parsing output", 
                      stdout_length=len(stdout),
                      stderr_length=len(stderr),
                      output_file_path=output_file_path,
                      output_format=output_format)
        
        # DEFAULT: Parse stdout (when output_format is None) - concise and LLM-friendly
        if output_format is None:
            result_json = _parse_sherlock_stdout(stdout, usernames, logger)
            # Apply limit if specified (post-filtering)
            if limit is not None:
                result_json = _apply_limit_to_results(result_json, limit, usernames, logger)
            return result_json
        
        # For JSON format with single file: return the JSON file content directly, verbatim
        if output_format == "json" and output_file_path:
            # Check if file exists
            if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
                try:
                    with open(output_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        json_content = f.read()
                    # Cleanup temp directory
                    if os.path.exists(os.path.dirname(output_file_path)):
                        try:
                            shutil.rmtree(os.path.dirname(output_file_path))
                        except Exception:
                            pass
                    # Return JSON file content directly, verbatim - no wrapper
                    safe_log_info(logger, "[sherlock_enum] Complete - returning JSON file content verbatim", 
                                usernames=usernames,
                                json_file=output_file_path,
                                json_content_length=len(json_content))
                    return json_content
                except Exception as e:
                    safe_log_error(logger, "[sherlock_enum] Error reading JSON file", 
                                 exc_info=True,
                                 error=str(e),
                                 json_file=output_file_path)
                    # Fall through to check directory
            # If single file doesn't exist, check if it's in the temp directory
            elif output_file_path and os.path.exists(os.path.dirname(output_file_path)):
                # Get the temp directory - since file doesn't exist, use parent directory
                # If output_file_path is a directory, use it directly; otherwise use parent
                if os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                    search_dir = output_file_path
                else:
                    search_dir = os.path.dirname(output_file_path)
                # Look for JSON file in temp directory
                json_file = os.path.join(search_dir, os.path.basename(output_file_path))
                if os.path.exists(json_file) and os.path.isfile(json_file):
                    try:
                        with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                            json_content = f.read()
                        # Cleanup temp directory
                        try:
                            shutil.rmtree(search_dir)
                        except Exception:
                            pass
                        # Return JSON file content directly, verbatim - no wrapper
                        safe_log_info(logger, "[sherlock_enum] Complete - returning JSON file content verbatim", 
                                    usernames=usernames,
                                    json_file=json_file,
                                    json_content_length=len(json_content))
                        return json_content
                    except Exception as e:
                        safe_log_error(logger, "[sherlock_enum] Error reading JSON file", 
                                     exc_info=True,
                                     error=str(e),
                                     json_file=json_file)
                        # Fall through
        
        # For other formats or multiple files: return JSON files directly (no wrapper)
        if output_format == "json" and output_file_path and os.path.exists(output_file_path):
            # Multiple JSON files - return as dictionary mapping username to JSON content
            if os.path.isdir(output_file_path):
                json_results = {}
                try:
                    for file in os.listdir(output_file_path):
                        file_path = os.path.join(output_file_path, file)
                        if os.path.isfile(file_path) and file.endswith('.json'):
                            # Extract username from filename (e.g., "username.json")
                            username = file.replace('.json', '')
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                json_results[username] = f.read()
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error reading JSON files: {str(e)}", exc_info=True)
                
                # Cleanup temp directory
                # output_file_path is the directory itself for multiple usernames
                cleanup_dir = output_file_path if os.path.isdir(output_file_path) else os.path.dirname(output_file_path)
                if cleanup_dir and os.path.exists(cleanup_dir):
                    try:
                        import shutil
                        shutil.rmtree(cleanup_dir)
                    except Exception:
                        pass
                
                # Return JSON files as dictionary - no wrapper metadata
                safe_log_info(logger, "[sherlock_enum] Complete - returning JSON files verbatim", 
                            usernames=usernames,
                            files_count=len(json_results))
                return json.dumps(json_results, indent=2)
        
        # For CSV format: check for CSV files in output directory
        if output_format == "csv" and output_file_path:
            # Check if CSV file exists
            if os.path.exists(output_file_path) and os.path.isfile(output_file_path):
                try:
                    with open(output_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        csv_content = f.read()
                    # Cleanup temp directory
                    if os.path.exists(os.path.dirname(output_file_path)):
                        try:
                            shutil.rmtree(os.path.dirname(output_file_path))
                        except Exception:
                            pass
                    # Return CSV file content directly, verbatim - no wrapper
                    safe_log_info(logger, "[sherlock_enum] Complete - returning CSV file content verbatim", 
                                usernames=usernames,
                                csv_file=output_file_path,
                                csv_content_length=len(csv_content))
                    return csv_content
                except Exception as e:
                    safe_log_error(logger, "[sherlock_enum] Error reading CSV file", 
                                 exc_info=True,
                                 error=str(e),
                                 csv_file=output_file_path)
                    # Fall through to check directory
            # Check if it's a directory with multiple CSV files
            elif os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                csv_results = {}
                try:
                    for file in os.listdir(output_file_path):
                        file_path = os.path.join(output_file_path, file)
                        if os.path.isfile(file_path) and file.endswith('.csv'):
                            # Extract username from filename (e.g., "username.csv")
                            username = file.replace('.csv', '')
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                csv_results[username] = f.read()
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error reading CSV files: {str(e)}", exc_info=True)
                
                # Cleanup temp directory
                # output_file_path is the directory itself for multiple usernames
                cleanup_dir = output_file_path if os.path.isdir(output_file_path) else os.path.dirname(output_file_path)
                if cleanup_dir and os.path.exists(cleanup_dir):
                    try:
                        import shutil
                        shutil.rmtree(cleanup_dir)
                    except Exception:
                        pass
                
                # Return CSV files as dictionary - no wrapper metadata
                if csv_results:
                    safe_log_info(logger, "[sherlock_enum] Complete - returning CSV files verbatim", 
                                usernames=usernames,
                                files_count=len(csv_results))
                    return json.dumps(csv_results, indent=2)
            # Fallback: check temp directory for CSV files
            elif output_file_path:
                # Get the temp directory - check if output_file_path exists and is a directory
                if os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                    search_dir = output_file_path
                else:
                    search_dir = os.path.dirname(output_file_path)
                if os.path.exists(search_dir):
                    try:
                        csv_files = [f for f in os.listdir(search_dir) if f.endswith('.csv')]
                        if csv_files:
                            if len(csv_files) == 1 and len(usernames) == 1:
                                # Single CSV file - return it verbatim
                                csv_file = os.path.join(search_dir, csv_files[0])
                                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                                    csv_content = f.read()
                                # Cleanup
                                try:
                                    import shutil
                                    shutil.rmtree(search_dir)
                                except Exception:
                                    pass
                                safe_log_info(logger, "[sherlock_enum] Complete - returning CSV file content verbatim", 
                                            usernames=usernames,
                                            csv_file=csv_file)
                                return csv_content
                            else:
                                # Multiple CSV files - return as dict
                                csv_results = {}
                                for csv_file in csv_files:
                                    file_path = os.path.join(search_dir, csv_file)
                                    username = csv_file.replace('.csv', '')
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        csv_results[username] = f.read()
                                # Cleanup
                                try:
                                    import shutil
                                    shutil.rmtree(search_dir)
                                except Exception:
                                    pass
                                safe_log_info(logger, "[sherlock_enum] Complete - returning CSV files verbatim", 
                                            usernames=usernames,
                                            files_count=len(csv_results))
                                return json.dumps(csv_results, indent=2)
                    except Exception as e:
                        safe_log_error(logger, f"[sherlock_enum] Error checking temp directory for CSV: {str(e)}", exc_info=True)
        
        # For JSON format: check if JSON files were created in temp directory even if path check failed
        if output_format == "json" and output_file_path:
            # Get the temp directory - check if output_file_path exists and is a directory
            if os.path.exists(output_file_path) and os.path.isdir(output_file_path):
                search_dir = output_file_path
            else:
                search_dir = os.path.dirname(output_file_path)
            if search_dir and os.path.exists(search_dir):
                # Look for any JSON files in the temp directory
                try:
                    json_files = [f for f in os.listdir(search_dir) if f.endswith('.json')]
                    if json_files:
                        if len(json_files) == 1 and len(usernames) == 1:
                            # Single JSON file - return it verbatim
                            json_file = os.path.join(search_dir, json_files[0])
                            with open(json_file, 'r', encoding='utf-8', errors='ignore') as f:
                                json_content = f.read()
                            # Cleanup
                            try:
                                import shutil
                                shutil.rmtree(search_dir)
                            except Exception:
                                pass
                            safe_log_info(logger, "[sherlock_enum] Complete - returning JSON file content verbatim", 
                                        usernames=usernames,
                                        json_file=json_file)
                            return json_content
                        else:
                            # Multiple JSON files - return as dict
                            json_results = {}
                            for json_file in json_files:
                                file_path = os.path.join(search_dir, json_file)
                                username = json_file.replace('.json', '')
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    json_results[username] = f.read()
                            # Cleanup
                            try:
                                import shutil
                                shutil.rmtree(search_dir)
                            except Exception:
                                pass
                            safe_log_info(logger, "[sherlock_enum] Complete - returning JSON files verbatim", 
                                        usernames=usernames,
                                        files_count=len(json_results))
                            return json.dumps(json_results, indent=2)
                except Exception as e:
                    safe_log_error(logger, f"[sherlock_enum] Error checking temp directory: {str(e)}", exc_info=True)
        
        # Cleanup temp directory
        if output_file_path:
            # output_file_path might be a directory (for multiple usernames) or a file path
            cleanup_dir = output_file_path if os.path.isdir(output_file_path) else os.path.dirname(output_file_path)
            if cleanup_dir and os.path.exists(cleanup_dir):
                try:
                    import shutil
                    shutil.rmtree(cleanup_dir)
                except Exception:
                    pass
        
        # Return stdout/stderr verbatim - no wrapper
        safe_log_info(logger, "[sherlock_enum] Complete - returning stdout verbatim", 
                    usernames=usernames,
                    stdout_length=len(stdout) if stdout else 0,
                    stderr_length=len(stderr) if stderr else 0)
        return stdout if stdout else stderr

    except Exception as e:
        safe_log_error(logger, "[sherlock_enum] Error", 
                     exc_info=True, 
                     error=str(e),
                     usernames=usernames)
        return json.dumps({"status": "error", "message": f"Sherlock enumeration failed: {str(e)}"})
