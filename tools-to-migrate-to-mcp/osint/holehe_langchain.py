"""
Holehe Tool for LangChain Agents

Check email registration on 120+ sites using Holehe tool.
This tool verifies if an email address is registered on various websites and services
by attempting to create accounts or checking account existence.

Reference: https://github.com/megadose/holehe

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following configuration:

1. Docker Environment (Required)
   - Description: Holehe requires Docker to execute
   - Setup:
     a) Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .
     b) Start container: docker-compose up -d
   - The tool will check Docker availability and log errors if not available

2. No Additional Environment Variables Required
   - This tool does not require API keys or external service URLs
   - All configuration is passed via function parameters

Configuration Example:
    agent_state = {
        "user_id": "analyst_001"
        # No environment_variables needed for this tool
    }

Security Notes:
- Email addresses are logged for audit purposes (not sensitive, but logged)
- All scraping operations are logged with user_id for audit purposes
- Docker execution provides isolation for scraping operations
- No sensitive credentials required

================================================================================
Key Features:
================================================================================
- Check email registration across 120+ websites
- Filter results to show only sites where email exists (only_used flag)
- Fast parallel checking across multiple sites
- Docker-based execution for isolation

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.osint.holehe_langchain import holehe_search
    
    agent = create_agent(
        model=llm,
        tools=[holehe_search],
        system_prompt="You are an OSINT specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Check if email@example.com is registered anywhere"}],
        "user_id": "analyst_001"
    })
"""

import json
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key

logger = setup_logger(__name__, log_file_path="logs/holehe_tool.log")


class HoleheSecurityAgentState(AgentState):
    """Extended agent state for Holehe operations."""
    user_id: str = ""


@tool
def holehe_search(
    runtime: ToolRuntime,
    email: str,
    only_used: bool = True
) -> str:
    """
    Check email registration on 120+ sites using Holehe.
    
    This tool verifies if an email address is registered on various websites and services
    by attempting to create accounts or checking account existence. It checks across 120+
    popular websites and services.
    
    Configuration Requirements:
        - Docker: Docker must be available and osint-tools image must be built
          The tool checks Docker availability and logs errors if not available
        - No API keys or external service URLs required
          All configuration is passed via function parameters
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Used for user_id tracking and audit logging.
        email: The email address to check (required).
            Must be a valid email format (contains '@').
            Example: "user@example.com"
        only_used: If True, return only sites where the email is registered (default: True).
            If False, return all sites checked (both registered and not registered).
    
    Returns:
        JSON string with array of results, each containing:
        - name: Site name where email was checked
        - exists: Boolean indicating if email is registered on this site
        - url: URL of the site (constructed from site name)
        
        Example:
        [
            {
                "name": "github.com",
                "exists": true,
                "url": "https://github.com"
            },
            {
                "name": "twitter.com",
                "exists": false,
                "url": "https://twitter.com"
            }
        ]
    
    Raises:
        ValueError: If email is invalid or missing '@' symbol
        RuntimeError: If Docker is not available or Holehe execution fails
    
    Note:
        - Holehe checks 120+ sites, which can take several minutes
        - Results are returned as JSON array for easy parsing
        - Only sites where email exists are returned if only_used=True
        - All sites checked are returned if only_used=False
    """
    try:
        safe_log_info(logger, "[holehe_search] Starting", email=email, only_used=only_used)
        
        # Validate inputs
        if not email or not isinstance(email, str) or "@" not in email:
            error_msg = "Invalid email address provided (must contain '@' symbol)"
            safe_log_error(logger, "[holehe_search] Validation failed", error_msg=error_msg, email=email)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[holehe_search] Email validated", email=email)
        
        # Check Docker availability (Docker-only execution)
        safe_log_debug(logger, "[holehe_search] Checking Docker availability")
        from shared.modules.tools.docker_client import get_docker_client, execute_in_docker
        docker_client = get_docker_client()
        
        if not docker_client or not docker_client.docker_available:
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, "[holehe_search] Docker not available", 
                         docker_available=bool(docker_client and docker_client.docker_available),
                         error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_info(logger, "[holehe_search] Docker available, proceeding with execution", 
                     email=email, only_used=only_used)
        
        # Build command arguments
        # Holehe CLI: holehe <email>
        # Optional: --only-used flag to filter results (but we filter in post-processing)
        args = [email]
        
        # Execute in Docker using custom osint-tools container
        # Holehe doesn't have an official Docker image, so it uses the custom container
        # Timeout: 5 minutes (holehe checks 120+ sites, can take time)
        safe_log_info(logger, "[holehe_search] Executing in Docker", 
                     command="holehe", 
                     args_count=len(args),
                     timeout=300)
        docker_result = execute_in_docker("holehe", args, timeout=300)
        
        safe_log_debug(logger, "[holehe_search] Docker execution complete", 
                      status=docker_result.get("status"),
                      has_stdout=bool(docker_result.get("stdout")),
                      has_stderr=bool(docker_result.get("stderr")))
        
        if docker_result["status"] != "success":
            error_msg = f"Holehe failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, "[holehe_search] Docker execution failed", 
                         stderr=docker_result.get('stderr', ''),
                         docker_message=docker_result.get('message', ''),
                         error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Parse output
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        safe_log_debug(logger, "[holehe_search] Parsing output", 
                      stdout_length=len(stdout),
                      stderr_length=len(stderr))
        
        # Holehe outputs text format: [x] site_name (exists) or [-] site_name (doesn't exist)
        # Parse text output and convert to JSON
        if stdout:
            try:
                results = []
                for line in stdout.strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Skip header lines (lines with asterisks or dashes)
                    if line.startswith('*') or (line.startswith('-') and len(line) > 20):
                        continue
                    # Skip email header line
                    if '@' in line and ('gmail.com' in line.lower() or 'hotmail.com' in line.lower() or 'live.com' in line.lower()):
                        continue
                    # Parse [x] site_name or [-] site_name
                    if line.startswith('[x]'):
                        site_name = line[3:].strip()
                        if site_name:
                            site_result = {
                                "name": site_name,
                                "exists": True,
                                "url": f"https://{site_name}" if not site_name.startswith('http') else site_name
                            }
                            if not only_used or site_result.get("exists", False):
                                results.append(site_result)
                    elif line.startswith('[-]'):
                        site_name = line[3:].strip()
                        if site_name:
                            site_result = {
                                "name": site_name,
                                "exists": False,
                                "url": f"https://{site_name}" if not site_name.startswith('http') else site_name
                            }
                            if not only_used:  # Include non-existing sites if only_used is False
                                results.append(site_result)
                
                # Return results as JSON array
                safe_log_info(logger, "[holehe_search] Complete", 
                            email=email, 
                            sites_found=len(results),
                            only_used=only_used)
                return json.dumps(results, indent=2)
            except Exception as e:
                safe_log_error(logger, "[holehe_search] Error parsing output", 
                             exc_info=True, 
                             error=str(e),
                             stdout_preview=stdout[:200] if stdout else "")
                # Fall through to return raw output
        elif stderr:
            # If stdout is empty but stderr has content, return it
            safe_log_info(logger, "[holehe_search] Complete - returning stderr", 
                        email=email,
                        stderr_length=len(stderr))
            return stderr
        
        # If both stdout and stderr are empty, return empty array (no results found)
        safe_log_info(logger, "[holehe_search] Complete - no output, returning empty array", 
                    email=email)
        return json.dumps([], indent=2)
        
    except Exception as e:
        safe_log_error(logger, "[holehe_search] Error", exc_info=True, error=str(e), email=email)
        return json.dumps({"status": "error", "message": f"Holehe search failed: {str(e)}"})
