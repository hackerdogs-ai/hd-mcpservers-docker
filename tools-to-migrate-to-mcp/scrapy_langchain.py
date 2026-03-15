"""
Scrapy Tool for LangChain Agents

Custom web scraping framework using Scrapy.
This tool provides advanced web scraping capabilities with spider-based architecture.

Reference: https://scrapy.org/

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following configuration:

1. Docker Environment (Required)
   - Description: Scrapy requires Docker to execute
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
- All scraping operations are logged with user_id for audit purposes
- Docker execution provides isolation for scraping operations
- No sensitive credentials required

================================================================================
Key Features:
================================================================================
- Advanced web scraping with Scrapy framework
- Spider-based architecture for custom scraping logic
- Link following and pagination support
- Configurable page limits
- Docker-based execution for isolation

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.scrapy_langchain import scrapy_search
    
    agent = create_agent(
        model=llm,
        tools=[scrapy_search],
        system_prompt="You are a web scraping specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Scrape https://example.com"}],
        "user_id": "analyst_001"
    })

Note:
    This tool is currently a template and requires implementation of actual
    Scrapy scraping logic. The Docker execution framework is in place.
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
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/scrapy_tool.log")


class ScrapySecurityAgentState(AgentState):
    """Extended agent state for Scrapy operations."""
    user_id: str = ""


def _check_scrapy_installed() -> bool:
    """Check if Scrapy binary/package is installed."""
    return shutil.which("scrapy") is not None or True  # Adjust based on tool type


@tool
def scrapy_search(
    runtime: ToolRuntime,
    url: str,
    spider_name: str = "generic",
    follow_links: bool = False,
    max_pages: int = 10
) -> str:
    """
    Custom web scraping framework using Scrapy.
    
    This tool performs advanced web scraping using the Scrapy framework.
    It supports custom spider configurations, link following, and pagination.
    
    Configuration Requirements:
        - Docker: Docker must be available and osint-tools image must be built
          The tool checks Docker availability and logs errors if not available
        - No API keys or external service URLs required
          All configuration is passed via function parameters
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Used for user_id tracking and audit logging.
        url: The URL to scrape. Must include protocol (http:// or https://).
            Example: "https://example.com" or "http://example.com/page"
        spider_name: Name of the Scrapy spider to use (default: "generic").
            Custom spiders can be configured for specific websites.
        follow_links: If True, follow links found on the page (default: False).
            Enables recursive scraping of linked pages.
        max_pages: Maximum number of pages to scrape (default: 10).
            Range: 1-1000. Prevents excessive resource usage.
    
    Returns:
        JSON string with scraping results containing:
        - status: "success" or "error"
        - url: The requested URL
        - spider_name: Spider used for scraping
        - results: Scraped data (structure depends on spider configuration)
        - pages_scraped: Number of pages successfully scraped
        - user_id: User ID from runtime state
    
    Raises:
        ValueError: If URL is invalid or max_pages is out of range
        RuntimeError: If Docker is not available or Scrapy execution fails
    
    Note:
        This tool is currently a template and requires implementation of actual
        Scrapy scraping logic. The Docker execution framework is in place.
        When implemented, it will support:
        - Custom spider configurations
        - Data extraction pipelines
        - Item processing
        - Export to various formats (JSON, CSV, XML)
    """
    try:
        safe_log_info(logger, f"[scrapy_search] Starting", url=url, spider_name=spider_name, follow_links=follow_links, max_pages=max_pages)
        
        # Validate inputs
        if not url or not isinstance(url, str) or not url.startswith(("http://", "https://")):
            error_msg = "Invalid URL provided (must start with http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if max_pages < 1 or max_pages > 1000:
            error_msg = "Max pages must be between 1 and 1000"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Check Docker availability (Docker-only execution)
        safe_log_debug(logger, "[scrapy_search] Checking Docker availability")
       
        docker_client = get_docker_client()
        
        if not docker_client or not docker_client.docker_available:
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, f"[scrapy_search] {error_msg}", 
                         docker_available=bool(docker_client and docker_client.docker_available))
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_info(logger, "[scrapy_search] Docker available, proceeding with execution", 
                     url=url, 
                     spider_name=spider_name,
                     follow_links=follow_links,
                     max_pages=max_pages)
        
        # TODO: Implement tool-specific logic
        # This is a template - implement actual tool execution
        
        safe_log_info(logger, f"[scrapy_search] Complete", url=url)
        return json.dumps({"status": "error", "message": "Tool execution not yet implemented"})
        
    except Exception as e:
        safe_log_error(logger, f"[scrapy_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Scrapy scraping failed: {str(e)}"})
