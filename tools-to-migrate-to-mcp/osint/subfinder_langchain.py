"""
Subfinder Tool for LangChain Agents

Fast passive subdomain discovery using ProjectDiscovery Subfinder.
"""

import json
import subprocess
import shutil
from typing import Optional
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/subfinder_tool.log")


class SubfinderSecurityAgentState(AgentState):
    """Extended agent state for Subfinder operations."""
    user_id: str = ""


def _check_docker_available() -> bool:
    """Check if Docker is available for running Subfinder in container."""
    client = get_docker_client()
    if client is None:
        safe_log_debug(logger, "[subfinder_enum] Docker client is None")
    is_available = client.docker_available if client else False
    safe_log_debug(logger, "[subfinder_enum] Docker availability check", docker_available=is_available)
    return is_available


@tool
def subfinder_enum(
    runtime: ToolRuntime,
    domain: str,
    recursive: bool = False,
    silent: bool = True,
    sources: Optional[str] = None,
    exclude_sources: Optional[str] = None,
    all_sources: bool = False,
    rate_limit: Optional[int] = None,
    timeout: int = 30,
    max_time: int = 10,
    provider_config: Optional[str] = None,
    config: Optional[str] = None,
    active: bool = False,
    include_ip: bool = False,
    collect_sources: bool = False
) -> str:
    """
    Enumerate subdomains using Subfinder (fast passive discovery).
    
    Subfinder is extremely fast for passive subdomain discovery using
    multiple passive sources. Use this for quick subdomain enumeration.
    
    Reference: https://docs.projectdiscovery.io/opensource/subfinder/install
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Target domain to find subdomains for.
        recursive: Use only sources that can handle subdomains recursively (default: False).
        silent: Show only subdomains in output (default: True).
        sources: Comma-separated list of specific sources to use (e.g., "crtsh,github").
        exclude_sources: Comma-separated list of sources to exclude (e.g., "alienvault,zoomeyeapi").
        all_sources: Use all sources for enumeration (slow) (default: False).
        rate_limit: Maximum number of HTTP requests per second (default: None).
        timeout: Seconds to wait before timing out (default: 30).
        max_time: Minutes to wait for enumeration results (default: 10).
        provider_config: Path to custom provider config file (default: $HOME/.config/subfinder/provider-config.yaml).
        config: Path to custom flag config file (default: $CONFIG/subfinder/config.yaml).
        active: Display active subdomains only (default: False).
        include_ip: Include host IP in output (active only) (default: False).
        collect_sources: Include all sources in the output (JSON only) (default: False).
    
    Returns:
        JSON string with subdomains and metadata.
    """
    try:
        safe_log_info(logger, "[subfinder_enum] Starting enumeration", 
                     domain=domain,
                     recursive=recursive,
                     silent=silent,
                     timeout=timeout,
                     max_time=max_time)
        
        # Validate inputs
        if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
            error_msg = "domain must be a non-empty string"
            safe_log_error(logger, "[subfinder_enum] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        domain = domain.strip()
        
        if timeout < 1 or timeout > 3600:
            error_msg = "timeout must be between 1 and 3600 seconds"
            safe_log_error(logger, "[subfinder_enum] Validation failed", error_msg=error_msg, timeout=timeout)
            return json.dumps({"status": "error", "message": error_msg})
        
        if max_time < 1 or max_time > 120:
            error_msg = "max_time must be between 1 and 120 minutes"
            safe_log_error(logger, "[subfinder_enum] Validation failed", error_msg=error_msg, max_time=max_time)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[subfinder_enum] Inputs validated", domain=domain)
        
        # Docker-only execution
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, "[subfinder_enum] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build command arguments
        args = ["-d", domain, "-oJ", "-"]
        
        # Source options
        if all_sources:
            args.append("-all")
        elif sources:
            args.extend(["-s"] + sources.split(","))
        
        if exclude_sources:
            args.extend(["-es"] + exclude_sources.split(","))
        
        if recursive:
            args.append("-recursive")
        
        # Rate limiting
        if rate_limit:
            args.extend(["-rl", str(rate_limit)])
        
        # Timeouts
        if timeout:
            args.extend(["-timeout", str(timeout)])
        if max_time:
            args.extend(["-max-time", str(max_time)])
        
        # Config files
        if provider_config:
            args.extend(["-pc", provider_config])
        if config:
            args.extend(["-config", config])
        
        # Output options
        if active:
            args.append("-nW")
        if include_ip:
            args.append("-oI")
        if collect_sources:
            args.append("-cs")
        if silent:
            args.append("-silent")
        
        # Execute in Docker using official ProjectDiscovery image
        # Reference: https://docs.projectdiscovery.io/opensource/subfinder/running
        # Note: Config files must be mounted into container or use default locations
        docker_result = execute_in_docker("subfinder", args, timeout=(max_time * 60) + 60)
        
        if docker_result["status"] != "success":
            error_msg = f"Subfinder failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, "[subfinder_enum] Execution failed", 
                         exc_info=True,
                         error=error_msg,
                         domain=domain)
            return json.dumps({"status": "error", "message": error_msg})
        
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        safe_log_info(logger, "[subfinder_enum] Complete", 
                     domain=domain,
                     output_length=len(stdout) if stdout else len(stderr))
        # Return raw output verbatim - no parsing, no reformatting
        return stdout if stdout else stderr
        
    except subprocess.TimeoutExpired:
        error_msg = f"Subfinder timed out after {max_time * 60 + 60} seconds"
        safe_log_error(logger, "[subfinder_enum] Timeout", 
                     error=error_msg,
                     max_time=max_time,
                     domain=domain if 'domain' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})
    except Exception as e:
        safe_log_error(logger, "[subfinder_enum] Error", 
                     exc_info=True,
                     error=str(e),
                     domain=domain if 'domain' in locals() else None)
        return json.dumps({"status": "error", "message": f"Subfinder enumeration failed: {str(e)}"})

