"""
OnionSearch Tool for LangChain Agents

Scrape Dark Web search engines using OnionSearch tool.
This tool searches across multiple .onion search engines to find URLs and content
on the Dark Web.

Reference: https://github.com/megadose/OnionSearch

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following environment variables/configuration:

1. TOR_PROXY (Required)
   - Description: TOR proxy address for connecting to Dark Web
   - Example: "tor-proxy:9050" (Docker network) or "127.0.0.1:9050" (host)
   - Retrieval Priority (in order):
     a) runtime.state.environment_variables[<tool_instance>]["TOR_PROXY"]
        - Searches through all tool instances in environment_variables dict
        - Preferred method: ensures per-tool-instance configuration
     b) os.getenv("TOR_PROXY") [FALLBACK - with warning log]
        - Only used if not found in runtime state
        - Default: "tor-proxy:9050"
        - WARNING logged when fallback is used

2. Docker Environment (Required)
   - Description: OnionSearch requires Docker to execute
   - Setup:
     a) Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .
     b) Start container: docker-compose up -d
   - The tool will check Docker availability and log errors if not available

Configuration Example:
    agent_state = {
        "environment_variables": {
            "onionsearch_instance_1": {
                "TOR_PROXY": "tor-proxy:9050"  # For Docker network
                # OR
                "TOR_PROXY": "127.0.0.1:9050"  # For host execution
            }
        }
    }

Security Notes:
- TOR proxy configuration is logged (not sensitive, but logged for debugging)
- Ensure TOR proxy is properly configured and accessible
- Dark Web searches may take longer due to TOR network latency

================================================================================
Key Features:
================================================================================
- Search across multiple Dark Web search engines
- Extract URLs and metadata from .onion sites
- Support for multiple search engines (configurable)
- CSV and JSON output formats
- Docker-based execution for isolation

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.onionsearch_langchain import onionsearch_search
    
    agent = create_agent(
        model=llm,
        tools=[onionsearch_search],
        system_prompt="You are a Dark Web OSINT specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Search for 'example' on Dark Web"}],
        "user_id": "analyst_001",
        "environment_variables": {
            "onionsearch_instance": {
                "TOR_PROXY": "tor-proxy:9050"
            }
        }
    })
"""

import json
import os
import csv
import io
import re
import uuid
import subprocess
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/onionsearch_tool.log")


class OnionSearchSecurityAgentState(AgentState):
    """Extended agent state for OnionSearch operations."""
    user_id: str = ""


def _get_tor_proxy_from_runtime(runtime: ToolRuntime) -> str:
    """
    Get TOR proxy configuration from runtime state or environment variable (fallback).
    
    Retrieval Priority:
    1. PRIMARY: runtime.state.environment_variables[<instance>]["TOR_PROXY"]
    2. FALLBACK: os.getenv("TOR_PROXY") with WARNING log (default: "tor-proxy:9050")
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Expected structure:
            runtime.state.environment_variables = {
                "onionsearch_instance_1": {
                    "TOR_PROXY": "tor-proxy:9050"  # For Docker network
                    # OR
                    "TOR_PROXY": "127.0.0.1:9050"  # For host execution
                }
            }
    
    Returns:
        TOR proxy address string (e.g., "tor-proxy:9050" or "127.0.0.1:9050").
        - "tor-proxy:9050": Use when running in Docker network (service name)
        - "127.0.0.1:9050": Use when running on host (localhost)
    """
    safe_log_debug(logger, "[_get_tor_proxy_from_runtime] Starting TOR proxy retrieval")
    
    # PRIMARY METHOD: Try to get from runtime state environment_variables
    # This searches through all tool instances for TOR_PROXY
    env_vars_dict = runtime.state.get("environment_variables", {})
    instances_count = len(env_vars_dict) if isinstance(env_vars_dict, dict) else 0
    safe_log_debug(logger, "[_get_tor_proxy_from_runtime] Environment variables dict", 
                   instances_count=instances_count, 
                   instance_names=list(env_vars_dict.keys()) if isinstance(env_vars_dict, dict) else [])
    
    # Search through all tool instances to find TOR_PROXY
    # Each instance represents a separate tool configuration
    for instance_name, env_vars in env_vars_dict.items():
        if isinstance(env_vars, dict):
            tor_proxy = env_vars.get("TOR_PROXY")
            if tor_proxy:
                # Successfully found TOR proxy in runtime state - preferred method
                safe_log_info(logger, "[_get_tor_proxy_from_runtime] Found TOR proxy in runtime state", 
                            instance_name=instance_name, 
                            tor_proxy=tor_proxy)
                return tor_proxy
    
    # FALLBACK METHOD: Use os.getenv() - this is NOT preferred
    # Log warning to indicate fallback is being used
    fallback_proxy = os.getenv("TOR_PROXY", "tor-proxy:9050")
    safe_log_error(logger, "[_get_tor_proxy_from_runtime] WARNING: Using fallback TOR proxy from os.getenv()", 
                   fallback_proxy=fallback_proxy,
                   note="TOR_PROXY should be provided via runtime.state.environment_variables")
    return fallback_proxy


@tool
def onionsearch_search(
    runtime: ToolRuntime,
    query: str,
    engines: Optional[List[str]] = None,
    limit: int = 25,
    output_format: str = "csv"
) -> str:
    """
    Search Dark Web (.onion) search engines for URLs.
    
    This tool queries multiple Dark Web search engines to find URLs and content
    matching the search query. Results are returned in CSV or JSON format.
    
    Configuration Requirements:
        - TOR_PROXY: TOR proxy address for Dark Web access
          Source: runtime.state.environment_variables[<instance>]["TOR_PROXY"]
          Fallback: os.getenv("TOR_PROXY") (with warning, default: "tor-proxy:9050")
        - Docker: Docker must be available and osint-tools image must be built
          The tool checks Docker availability and logs errors if not available
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Must contain environment_variables with TOR_PROXY configuration.
        query: Search query string. Non-empty string required.
        engines: Optional list of specific search engines to use (default: all available).
            Example: ["ahmia", "notevil", "candle"]
        limit: Maximum number of total results to return (default: 10).
            Range: 1-200. The tool will limit final results to this exact value.
            NOTE: Internally, OnionSearch's --limit parameter controls "pages per engine".
            The tool automatically calculates appropriate pages per engine based on your limit,
            then applies post-filtering to ensure you get exactly the requested number of results.
            Example: limit=10 → returns max 10 results, limit=50 → returns max 50 results.
        output_format: Output format - "csv" (default) or "json".
            - "csv": Returns raw CSV output from OnionSearch
            - "json": Parses CSV and returns structured JSON array
    
    Returns:
        - If output_format="csv": Raw CSV string with columns: engine, name, url
        - If output_format="json": JSON string with array of objects:
          [
            {
              "engine": "ahmia",
              "name": "Example Site",
              "url": "http://example.onion"
            },
            ...
          ]
        - If no results: Empty CSV header ("engine,name,url\\n") or empty JSON array ([])
        - On error: JSON string with {"status": "error", "message": "..."}
    
    Raises:
        ValueError: If query is invalid, limit is out of range, or output_format is invalid
        RuntimeError: If Docker is not available or OnionSearch execution fails
    
    Note:
        - Dark Web searches can be slow due to TOR network latency
        - Timeout is set to 5 minutes (300 seconds) to accommodate slow responses
        - Results may vary based on search engine availability and TOR network conditions
        - Some search engines may be temporarily unavailable
    """
    try:
        safe_log_info(logger, f"[onionsearch_search] Starting", query=query, engines=engines, limit=limit, output_format=output_format)
        
        # Validate inputs
        if not query or not isinstance(query, str) or len(query.strip()) == 0:
            error_msg = "query must be a non-empty string"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if limit < 1 or limit > 200:
            error_msg = "limit must be between 1 and 200"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if output_format not in ["csv", "json"]:
            error_msg = "output_format must be 'csv' or 'json'"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Check Docker availability (Docker-only execution)

        docker_client = get_docker_client()
        
        if not docker_client or not docker_client.docker_available:
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build command arguments
        # OnionSearch CLI: onionsearch "query" [options]
        args = [query]
        
        # Get Tor proxy from runtime state (required for OnionSearch)
        # In Docker network, use service name; fallback to host IP if running on host
        tor_proxy = _get_tor_proxy_from_runtime(runtime)
        safe_log_info(logger, "[onionsearch_search] Using TOR proxy", tor_proxy=tor_proxy)
        args.extend(["--proxy", tor_proxy])
        
        # Add limit for OnionSearch (pages per engine)
        # NOTE: OnionSearch's --limit is "pages per engine", not total results
        # We'll limit total results to the `limit` parameter value after retrieval
        # Calculate pages per engine: assume ~20 results per page, multiple engines
        # Request enough pages to potentially get the desired results, but cap at 10 pages
        # Example: limit=10 results → request 1-2 pages per engine (enough for ~10 engines)
        # Example: limit=50 results → request 3-5 pages per engine
        if limit <= 20:
            pages_per_engine = 1  # 1 page × ~20 results × multiple engines = enough
        elif limit <= 100:
            pages_per_engine = min((limit // 20) + 1, 5)  # 2-5 pages
        else:
            pages_per_engine = min((limit // 20) + 1, 10)  # Up to 10 pages max
        args.extend(["--limit", str(pages_per_engine)])
        safe_log_debug(logger, f"[onionsearch_search] OnionSearch pages per engine", 
                      pages_per_engine=pages_per_engine,
                      user_limit=limit,
                      note="Will limit final results to user's limit parameter")
        
        # Add specific engines if provided
        if engines and len(engines) > 0:
            args.extend(["--engines"] + engines)
        
        # CRITICAL: OnionSearch doesn't write CSV to stdout when using --output -
        # It only writes to stdout for status messages. CSV must be written to a file.
        # Use a unique temporary file inside the container workspace to avoid race conditions
        unique_id = str(uuid.uuid4())[:8]
        output_file = f"/workspace/onionsearch_output_{unique_id}.csv"
        args.extend(["--output", output_file])
        
        # Execute in Docker using custom osint-tools container
        # OnionSearch doesn't have an official Docker image
        # Timeout: 5 minutes (can take time to scrape multiple engines)
        safe_log_info(logger, "[onionsearch_search] Executing in Docker", 
                     command="onionsearch", 
                     args_count=len(args),
                     output_file=output_file,
                     timeout=300)
        docker_result = execute_in_docker("onionsearch", args, timeout=300)
        
        safe_log_debug(logger, "[onionsearch_search] Docker execution complete", 
                      status=docker_result.get("status"),
                      has_stdout=bool(docker_result.get("stdout")),
                      has_stderr=bool(docker_result.get("stderr")))

        # Helpful diagnostics: OnionSearch sometimes returns exit code 0 but writes warnings/errors to stderr
        # and/or produces an empty output file. Log a short preview to aid debugging without flooding logs.
        stdout_preview = (docker_result.get("stdout") or "")[:800]
        stderr_preview = (docker_result.get("stderr") or "")[:800]
        if stdout_preview or stderr_preview:
            safe_log_debug(
                logger,
                "[onionsearch_search] Docker stdout/stderr preview",
                stdout_preview=stdout_preview,
                stderr_preview=stderr_preview,
            )
        
        if docker_result["status"] != "success":
            error_msg = f"OnionSearch failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, f"[onionsearch_search] {error_msg}", 
                         stderr=docker_result.get('stderr', ''),
                         message=docker_result.get('message', ''))
            return json.dumps({"status": "error", "message": error_msg})
        
        # CRITICAL FIX: OnionSearch doesn't write CSV to stdout when using --output -
        # The CSV is written to the file specified in --output. Read it from the file.
        # The file is inside the container at /workspace/onionsearch_output.csv
        # We need to read it using docker exec
        safe_log_debug(logger, "[onionsearch_search] Reading CSV from file", output_file=output_file)
        
        try:
            # Read the CSV file from the container using docker exec
            # The file is written to /workspace/onionsearch_output.csv inside the container
            # NOTE: do NOT re-import get_docker_client here. Doing so makes Python treat
            # get_docker_client as a local variable within onionsearch_search(), which
            # triggers UnboundLocalError when it's referenced earlier in the function.
            container_name = None
            if docker_client and docker_client.docker_available:
                # Use docker exec to read the file (container name is "osint-tools" by default)
                container_name = docker_client.container_name  # Get container name from client
                read_result = subprocess.run(
                    [docker_client.docker_runtime, "exec", container_name, "cat", output_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if read_result.returncode == 0:
                    csv_output = read_result.stdout
                    safe_log_info(logger, "[onionsearch_search] Successfully read CSV file", 
                                csv_length=len(csv_output),
                                lines_count=len(csv_output.split('\n')) if csv_output else 0)
                else:
                    safe_log_error(logger, "[onionsearch_search] Failed to read CSV file", 
                                 stderr=read_result.stderr,
                                 returncode=read_result.returncode)
                    csv_output = ""
            else:
                safe_log_error(logger, "[onionsearch_search] Docker client not available for reading CSV file")
                csv_output = ""
        except Exception as read_error:
            safe_log_error(logger, f"[onionsearch_search] Error reading CSV file: {str(read_error)}", exc_info=True)
            csv_output = ""
        
        # Clean up the CSV output (remove empty lines, ensure proper format)
        if csv_output:
            csv_lines = [line.strip() for line in csv_output.split('\n') if line.strip()]
            
            # CRITICAL: OnionSearch's --limit is "pages per engine", not total results
            # With multiple engines, this can return hundreds of results even with limit=10
            # Example: 10 engines × 10 pages × ~20 results/page = 2000+ results
            # Apply limit directly as maximum total results to match user expectation
            # The limit parameter should control total results, not pages per engine
            max_results = limit  # Use limit directly as max total results
            
            original_count = len(csv_lines)
            if original_count > max_results:
                # OnionSearch CSV has no header - just data rows starting with quoted engine names
                # Limit to max_results rows
                csv_lines = csv_lines[:max_results]
                safe_log_info(logger, f"[onionsearch_search] Limited results", 
                            original_count=original_count,
                            limited_count=len(csv_lines),
                            max_results=max_results,
                            limit_param=limit,
                            note="OnionSearch --limit is pages per engine, not total results. Applied post-filtering.")
            else:
                safe_log_debug(logger, f"[onionsearch_search] Results within limit", 
                              count=original_count,
                              max_results=max_results,
                              limit_param=limit)
            
            csv_output = '\n'.join(csv_lines)
            safe_log_debug(logger, f"[onionsearch_search] CSV cleaned", 
                          original_lines=original_count,
                          cleaned_lines=len(csv_lines))
        else:
            # If OnionSearch produced an empty CSV file, log context so we can distinguish
            # "no results" from "execution produced warnings/errors".
            if stderr_preview:
                safe_log_error(
                    logger,
                    "[onionsearch_search] Empty CSV output file; OnionSearch stderr preview",
                    query=query,
                    stderr_preview=stderr_preview,
                )
        
        # Cleanup: Delete the temporary CSV file from the container after reading
        try:
            if docker_client and docker_client.docker_available and container_name:
                cleanup_result = subprocess.run(
                    [docker_client.docker_runtime, "exec", container_name, "rm", "-f", output_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if cleanup_result.returncode == 0:
                    safe_log_debug(logger, f"[onionsearch_search] Cleaned up temporary file", output_file=output_file)
                else:
                    safe_log_debug(logger, f"[onionsearch_search] Failed to cleanup file (non-critical)", 
                                   output_file=output_file,
                                   stderr=cleanup_result.stderr)
        except Exception as cleanup_error:
            # Non-critical - log but don't fail
            safe_log_debug(logger, f"[onionsearch_search] Error during cleanup (non-critical): {str(cleanup_error)}")
        
        # OnionSearch outputs CSV format by default: "engine","name","url"
        # Return verbatim CSV output
        if output_format == "csv":
            if csv_output:
                safe_log_info(logger, f"[onionsearch_search] Complete - returning CSV verbatim", query=query)
                return csv_output
            else:
                safe_log_info(logger, f"[onionsearch_search] Complete - no results", query=query)
                return "engine,name,url\n"  # Empty CSV header
        
        # For JSON format, parse CSV to JSON
        if output_format == "json":
            if csv_output:
                try:
                    results = []
                    csv_reader = csv.DictReader(io.StringIO(csv_output))
                    for row in csv_reader:
                        results.append(row)
                    safe_log_info(logger, f"[onionsearch_search] Complete - returning JSON", query=query, results_count=len(results))
                    return json.dumps(results, indent=2)
                except Exception as e:
                    safe_log_error(logger, f"[onionsearch_search] Error parsing CSV: {str(e)}", exc_info=True)
                    # Return raw CSV if parsing fails
                    return csv_output
            else:
                safe_log_info(logger, f"[onionsearch_search] Complete - no results", query=query)
                return json.dumps([])
        
        # Fallback: return CSV output (or empty if no results)
        safe_log_info(logger, f"[onionsearch_search] Complete - returning CSV verbatim", query=query)
        return csv_output if csv_output else "engine,name,url\n"  # Empty CSV header if no results
        
    except Exception as e:
        safe_log_error(logger, f"[onionsearch_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"OnionSearch failed: {str(e)}"})
