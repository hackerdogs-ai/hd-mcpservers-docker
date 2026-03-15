"""
Waybackurls Tool for LangChain Agents

Fetch URLs from Wayback Machine using waybackpy Python package.
This tool queries the Wayback Machine to retrieve historical URLs for a given domain.

Reference: https://github.com/akamhy/waybackpy

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following configuration:

1. No Environment Variables Required
   - This tool uses the waybackpy Python package directly
   - No API keys or external service URLs required
   - No Docker required (runs natively in Python environment)
   - All configuration is passed via function parameters

2. User Agent (Internal)
   - Description: User agent string for Wayback Machine API requests
   - Source: Hardcoded in tool (not configurable)
   - Value: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
   - Used for: Identifying requests to Wayback Machine API

Configuration Example:
    agent_state = {
        "user_id": "analyst_001"
        # No environment_variables needed for this tool
    }

Security Notes:
- All queries are logged with user_id for audit purposes
- No sensitive credentials required
- Wayback Machine API is publicly accessible
- Rate limiting may apply based on Wayback Machine policies

================================================================================
Key Features:
================================================================================
- Fetch all URLs archived in Wayback Machine for a domain
- Exclude subdomains option (no_subs parameter)
- Date filtering support (YYYYMMDD-YYYYMMDD format)
- Get versions of specific URLs
- Native Python execution (no Docker required)
- Automatic pagination and result limiting (max 10,000 snapshots)

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.waybackurls_langchain import waybackurls_search
    
    agent = create_agent(
        model=llm,
        tools=[waybackurls_search],
        system_prompt="You are an OSINT specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Get Wayback URLs for example.com"}],
        "user_id": "analyst_001"
    })
"""

import json
from typing import Optional, Any
from urllib.parse import urlparse
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from waybackpy import WaybackMachineCDXServerAPI

logger = setup_logger(__name__, log_file_path="logs/waybackurls_tool.log")


class WaybackurlsSecurityAgentState(AgentState):
    """Extended agent state for Waybackurls operations."""
    user_id: str = ""


@tool
def waybackurls_search(
    runtime: ToolRuntime,
    domain: str,
    no_subs: bool = False,
    dates: Optional[str] = None,
    get_versions: bool = False,
    **kwargs: Any
) -> str:
    """
    Fetch URLs from Wayback Machine for a given domain.
    
    This tool queries the Wayback Machine archive to retrieve all URLs that have been
    archived for the specified domain. Useful for discovering historical endpoints,
    finding deleted pages, and mapping website structure over time.
    
    Configuration Requirements:
        - No environment variables or API keys required
          This tool uses the waybackpy Python package directly
          No Docker required (runs natively in Python environment)
        - User agent is hardcoded internally for Wayback Machine API requests
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
            Used for user_id tracking and audit logging.
            No environment_variables or api_keys required.
        domain: Domain name to fetch URLs for (e.g., "example.com").
            Must be a non-empty string. Protocol (http://) is automatically added.
            Example: "example.com" (not "https://example.com")
        no_subs: If True, exclude subdomains (default: False).
            When True, only returns URLs for exact domain match (e.g., "example.com")
            and "www.example.com". Excludes "subdomain.example.com".
            When False, returns URLs for all subdomains.
        dates: Optional date range filter in format "YYYYMMDD-YYYYMMDD".
            Example: "20200101-20201231" for all of 2020
            Both dates must be 8 digits (YYYYMMDD format)
            If invalid format, returns error
        get_versions: If True, list URLs for crawled versions of input URL(s) (default: False).
            Note: Currently not implemented - all snapshots are returned regardless of this flag.
            Reserved for future implementation.
    
    Returns:
        JSON string with list of URLs found in Wayback Machine:
        {
            "status": "success",
            "domain": "example.com",
            "no_subs": false,
            "dates": "20200101-20201231",
            "get_versions": false,
            "urls": [
                {
                    "url": "https://example.com/page1",
                    "date": "20200115",
                    "archive_url": "https://web.archive.org/web/20200115/https://example.com/page1"
                },
                ...
            ],
            "count": 1234,
            "user_id": "analyst_001",
            "note": "Raw URLs returned verbatim from Wayback Machine using waybackpy Python package"
        }
    
    Raises:
        ValueError: If domain is invalid, dates format is incorrect, or waybackpy fails
        RuntimeError: If waybackpy package is not installed or API is unavailable
    
    Note:
        - Results are limited to 10,000 snapshots to prevent excessive memory usage
        - Wayback Machine API may have rate limiting
        - Large domains may return many results (consider using date filters)
        - Some domains may have no archived URLs
        - Date filtering can significantly reduce result count
    """
    try:
        safe_log_info(logger, "[waybackurls_search] Starting", 
                     domain=domain, 
                     no_subs=no_subs, 
                     dates=dates, 
                     get_versions=get_versions)
        
        # Validate inputs
        user_id = runtime.state.get("user_id", "") if runtime and runtime.state else ""
        
        if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
            error_msg = "domain must be a non-empty string"
            safe_log_error(logger, "[waybackurls_search] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        domain = domain.strip()
        
        # Use waybackpy Python package instead of Docker
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        safe_log_debug(logger, "[waybackurls_search] Using waybackpy package", 
                      user_agent=user_agent[:50] + "...")
        
        # Parse date range if provided
        start_timestamp = None
        end_timestamp = None
        if dates:
            try:
                # Format: YYYYMMDD-YYYYMMDD
                dates_cleaned = dates.strip()
                if not dates_cleaned:
                    raise ValueError("Date range cannot be empty")
                parts = dates_cleaned.split("-")
                if len(parts) == 2:
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()
                    # Validate format (must be 8 digits)
                    if len(start_str) == 8 and len(end_str) == 8 and start_str.isdigit() and end_str.isdigit():
                        start_timestamp = int(start_str)  # YYYYMMDD
                        end_timestamp = int(end_str)    # YYYYMMDD
                        # Use cleaned dates in result
                        dates = dates_cleaned
                    else:
                        raise ValueError("Date must be in YYYYMMDD format (8 digits)")
                else:
                    raise ValueError("Date range must be in format YYYYMMDD-YYYYMMDD")
            except (ValueError, AttributeError) as e:
                error_msg = f"Invalid date format: {dates}. Expected YYYYMMDD-YYYYMMDD. Error: {str(e)}"
                safe_log_error(logger, "[waybackurls_search] Validation failed", error_msg=error_msg, dates=dates)
                return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[waybackurls_search] Domain validated", domain=domain)
        
        # Create CDX API instance
        try:
            safe_log_info(logger, "[waybackurls_search] Creating CDX API instance", 
                         domain=domain,
                         has_date_range=bool(start_timestamp and end_timestamp),
                         start_timestamp=start_timestamp,
                         end_timestamp=end_timestamp)
            
            cdx_api = WaybackMachineCDXServerAPI(
                url=f"https://{domain}",
                user_agent=user_agent,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp
            )
            
            safe_log_debug(logger, "[waybackurls_search] CDX API instance created, fetching snapshots")
            
            # Get snapshots
            urls = []
            snapshot_count = 0
            for snapshot in cdx_api.snapshots():
                snapshot_count += 1
                
                # Extract snapshot data with defensive checks
                original_url = getattr(snapshot, 'original', None)
                timestamp = getattr(snapshot, 'timestamp', None)
                archive_url = getattr(snapshot, 'archive_url', None)
                
                # Skip if essential data is missing
                if not original_url or not timestamp:
                    safe_log_debug(logger, "[waybackurls_search] Skipping snapshot with missing data",
                                 has_original=bool(original_url),
                                 has_timestamp=bool(timestamp))
                    continue
                
                # Filter subdomains if no_subs is True
                if no_subs:
                    # Extract domain from URL
                    parsed = urlparse(original_url)
                    url_domain = parsed.netloc
                    if not url_domain:
                        # If netloc is empty, skip this URL (invalid URL format)
                        continue
                    
                    # Remove port if present
                    if ":" in url_domain:
                        url_domain = url_domain.split(":")[0]
                    
                    # Only include if domain exactly matches base domain or www.base_domain
                    # Skip all other subdomains
                    if url_domain != domain and url_domain != f"www.{domain}":
                        # This is a subdomain, skip it
                        continue
                
                # Add URL with timestamp
                urls.append({
                    "url": original_url,
                    "date": timestamp,
                    "archive_url": archive_url if archive_url else f"https://web.archive.org/web/{timestamp}/{original_url}"
                })
                
                # Limit results to prevent excessive memory usage
                if snapshot_count >= 10000:  # Reasonable limit
                    safe_log_info(logger, "[waybackurls_search] Reached limit of 10000 snapshots", 
                                domain=domain,
                                snapshot_count=snapshot_count)
                    break
            
            safe_log_info(logger, "[waybackurls_search] Finished fetching snapshots", 
                         domain=domain,
                         total_snapshots=snapshot_count,
                         urls_collected=len(urls))
            
        except Exception as e:
            error_msg = f"Waybackpy failed: {str(e)}"
            safe_log_error(logger, "[waybackurls_search] Waybackpy execution failed", 
                         exc_info=True,
                         error=str(e),
                         domain=domain)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Return results as JSON
        result_data = {
            "status": "success",
            "domain": domain,
            "no_subs": no_subs,
            "dates": dates,
            "get_versions": get_versions,
            "urls": urls,
            "count": len(urls),
            "user_id": user_id,
            "note": "Raw URLs returned verbatim from Wayback Machine using waybackpy Python package"
        }
        
        safe_log_info(logger, "[waybackurls_search] Complete", 
                     domain=domain, 
                     urls_found=len(urls),
                     count=len(urls))
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, "[waybackurls_search] Error", 
                     exc_info=True,
                     error=str(e),
                     domain=domain if 'domain' in locals() else None)
        return json.dumps({"status": "error", "message": f"Waybackurls search failed: {str(e)}"})
