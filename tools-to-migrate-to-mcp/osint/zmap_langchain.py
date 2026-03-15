"""
zmap Tool for LangChain Agents

Single-packet scanning
"""

import json
import subprocess
import shutil
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/zmap_tool.log")


class ZMapSecurityAgentState(AgentState):
    """Extended agent state for ZMap operations."""
    user_id: str = ""


def _check_zmap_installed() -> bool:
    """Check if ZMap binary/package is installed."""
    return shutil.which("zmap") is not None or True  # Adjust based on tool type


@tool
def zmap_scan(
    runtime: ToolRuntime,
    ip_range: str,
    port: int,
    bandwidth: str
) -> str:
    """
    Single-packet scanning
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
                ip_range: str - Parameter description
        port: int - Parameter description
        bandwidth: str - Parameter description
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, "[zmap_scan] Starting", 
                     ip_range=ip_range, 
                     port=port, 
                     bandwidth=bandwidth)
        
        # Validate inputs
        if not ip_range or not isinstance(ip_range, str) or len(ip_range.strip()) == 0:
            error_msg = "ip_range must be a non-empty string"
            safe_log_error(logger, "[zmap_scan] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        ip_range = ip_range.strip()
        
        if not isinstance(port, int) or port < 1 or port > 65535:
            error_msg = "port must be between 1 and 65535"
            safe_log_error(logger, "[zmap_scan] Validation failed", error_msg=error_msg, port=port)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not bandwidth or not isinstance(bandwidth, str) or len(bandwidth.strip()) == 0:
            error_msg = "bandwidth must be a non-empty string"
            safe_log_error(logger, "[zmap_scan] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        bandwidth = bandwidth.strip()
        
        safe_log_debug(logger, "[zmap_scan] Inputs validated", 
                      ip_range=ip_range, 
                      port=port, 
                      bandwidth=bandwidth)
        
        # Check Docker availability (Docker-only execution)
        safe_log_debug(logger, "[zmap_scan] Checking Docker availability")
        from shared.modules.tools.docker_client import get_docker_client, execute_in_docker
        docker_client = get_docker_client()
        
        if docker_client is None:
            safe_log_debug(logger, "[zmap_scan] Docker client is None")
        
        is_available = docker_client.docker_available if docker_client else False
        safe_log_debug(logger, "[zmap_scan] Docker availability check", docker_available=is_available)
        
        if not docker_client or not is_available:
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, "[zmap_scan] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # TODO: Implement tool-specific logic
        # This is a template - implement actual tool execution
        
        safe_log_info(logger, "[zmap_scan] Complete", 
                     ip_range=ip_range, 
                     port=port,
                     bandwidth=bandwidth)
        return json.dumps({"status": "error", "message": "Tool execution not yet implemented"})
        
    except Exception as e:
        safe_log_error(logger, "[zmap_scan] Error", 
                     exc_info=True,
                     error=str(e),
                     ip_range=ip_range if 'ip_range' in locals() else None)
        return json.dumps({"status": "error", "message": f"ZMap scan failed: {str(e)}"})
