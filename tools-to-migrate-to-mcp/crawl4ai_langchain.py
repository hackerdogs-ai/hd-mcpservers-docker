"""
Crawl4AI Tool for LangChain Agents

Advanced web crawling and content extraction using Crawl4AI API service.
This tool provides intelligent web scraping with JavaScript execution, CSS selectors,
structured extraction, LLM-based extraction, and screenshot capabilities.

Reference: https://github.com/unclecode/crawl4ai

Key Features:
- JavaScript execution support for dynamic content
- CSS selector-based content extraction
- Structured data extraction (JSON-CSS, LLM-based)
- Screenshot capture
- Multiple crawl modes (direct, sync, async)
- User tracking and audit logging via agent state

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.crawl4ai_langchain import crawl4ai_crawl
    
    agent = create_agent(
        model=llm,
        tools=[crawl4ai_crawl],
        system_prompt="You are a web scraping specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Crawl https://example.com"}],
        "user_id": "analyst_001"
    })
"""

import json
import time
import requests
from typing import Optional, Dict, Any, List, Literal, Tuple
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key
import logging
logger = setup_logger(__name__, log_file_path="logs/crawl4ai_tool.log")


class Crawl4AISecurityAgentState(AgentState):
    """Extended agent state for Crawl4AI operations."""
    user_id: str = ""


def _get_crawl4ai_config_from_runtime(runtime: ToolRuntime) -> Tuple[Optional[str], Optional[str]]:
    """
    Get Crawl4AI URL and API token from runtime state environment variables.
    
    Standard approach: Search through all tool instances in environment_variables
    to find the one containing CRAWL4AI_URL and CRAWL4AI_API_TOKEN.
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
    
    Returns:
        Tuple of (url, token) or (None, None) if not found.
    """
    safe_log_debug(logger, "[_get_crawl4ai_config_from_runtime] Starting config retrieval from runtime state")
    
    env_vars_dict = runtime.state.get("environment_variables", {})
    instances_count = len(env_vars_dict) if isinstance(env_vars_dict, dict) else 0
    safe_log_debug(logger, "[_get_crawl4ai_config_from_runtime] Environment variables dict", 
                   instances_count=instances_count, 
                   instance_names=list(env_vars_dict.keys()) if isinstance(env_vars_dict, dict) else [])
    
    # Search through all tool instances to find Crawl4AI config
    for instance_name, env_vars in env_vars_dict.items():
        if isinstance(env_vars, dict):
            url = env_vars.get("CRAWL4AI_URL") or env_vars.get("CRAWL4AI_BASE_URL")
            token = env_vars.get("CRAWL4AI_API_TOKEN")
            
            if url and token:
                masked_token = mask_api_key(token)
                safe_log_info(logger, "[_get_crawl4ai_config_from_runtime] Found Crawl4AI config", 
                            instance_name=instance_name, 
                            url=url, 
                            token_masked=masked_token)
                return (url.rstrip("/"), token)
            else:
                safe_log_debug(logger, "[_get_crawl4ai_config_from_runtime] Instance missing config", 
                             instance_name=instance_name, 
                             has_url=bool(url), 
                             has_token=bool(token))
    
    safe_log_error(logger, "[_get_crawl4ai_config_from_runtime] Crawl4AI config not found in any tool instance", 
                  instances_searched=instances_count)
    return (None, None)


def _build_headers(runtime: ToolRuntime, api_token: Optional[str] = None) -> Dict[str, str]:
    """
    Build request headers with optional API token.
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
        api_token: Optional explicit token (if provided, uses this instead of runtime state).
    
    Returns:
        Headers dict with Content-Type and optional Authorization.
    """
    safe_log_debug(logger, "[_build_headers] Building request headers", 
                   has_explicit_token=bool(api_token))
    
    headers = {"Content-Type": "application/json"}
    
    if api_token:
        token = api_token
        masked_token = mask_api_key(token)
        safe_log_debug(logger, "[_build_headers] Using explicit API token", token_masked=masked_token)
    else:
        # Get token from runtime state
        _, token = _get_crawl4ai_config_from_runtime(runtime)
        if token:
            masked_token = mask_api_key(token)
            safe_log_debug(logger, "[_build_headers] Retrieved token from runtime state", token_masked=masked_token)
        else:
            safe_log_error(logger, "[_build_headers] No API token available from runtime state")
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        safe_log_debug(logger, "[_build_headers] Authorization header added", token_masked=mask_api_key(token))
    else:
        safe_log_error(logger, "[_build_headers] No token available - request will be unauthenticated")
    
    return headers


@tool
def crawl4ai_crawl(
    runtime: ToolRuntime,
    url: str,
    mode: Literal["direct", "sync", "async"] = "direct",
    priority: int = 10,
    session_id: Optional[str] = None,
    js_code: Optional[List[str]] = None,
    wait_for: Optional[str] = None,
    css_selector: Optional[str] = None,
    extraction_config: Optional[Dict[str, Any]] = None,
    screenshot: bool = False,
    crawler_params: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
    cache_mode: Optional[Literal["enabled", "disabled", "bypass", "read_only", "write_only"]] = None,
    timeout: int = 30,  # Reduced default timeout for faster responses
    **kwargs: Any
) -> str:
    """
    Crawl a website using Crawl4AI API service with advanced extraction capabilities.
    
    This tool provides intelligent web scraping with support for:
    - JavaScript execution for dynamic content
    - CSS selector-based content filtering
    - Structured data extraction (JSON-CSS, LLM-based, cosine similarity)
    - Screenshot capture
    - Multiple execution modes (direct, sync, async)
    
    When to use:
        - Need to scrape dynamic websites with JavaScript rendering
        - Extract structured data from web pages
        - Capture screenshots of web pages
        - Scrape content that requires interaction (click buttons, wait for elements)
        - Extract specific elements using CSS selectors
        - Use LLM-based extraction for complex data structures
    
    When NOT to use:
        - Simple static HTML scraping (use browserless_tool instead)
        - Websites requiring authentication/login
        - Very large websites or pages (may timeout)
        - Websites that block automated access
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to crawl. Must include protocol (http:// or https://).
            Example: "https://www.example.com/page"
        mode: Execution mode:
            - "direct": Immediate execution, returns result directly (default, fastest)
            - "sync": Synchronous execution, waits for completion (good for medium pages)
            - "async": Asynchronous execution with polling (best for long-running crawls)
        priority: Task priority (1-10, default: 10). Higher priority tasks execute first.
        session_id: Optional session ID for maintaining browser state across requests.
        js_code: Optional list of JavaScript code snippets to execute before scraping.
            Example: ["document.querySelector('.load-more').click()"]
        wait_for: Optional CSS selector to wait for before scraping.
            Example: "article.content" (waits for this element to appear)
        css_selector: Optional CSS selector to extract specific elements.
            Example: ".article-content" (only extracts matching elements)
        extraction_config: Optional extraction configuration for structured data:
            - Type "json_css": Extract structured data using CSS selectors
            - Type "llm": Use LLM to extract structured data
            - Type "cosine": Semantic similarity-based extraction
            Example: {"type": "json_css", "params": {"schema": {...}}}
        screenshot: If True, capture a screenshot of the page (default: False).
        crawler_params: Optional crawler parameters (headless, word_count_threshold, etc.).
        extra: Optional extra parameters for advanced configuration.
        cache_mode: Optional cache mode: "enabled", "disabled", "bypass", "read_only", "write_only".
            Default: "enabled" (cache is enabled by default for performance).
        timeout: Maximum time to wait for completion in seconds (default: 30).
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "url": str,
            "mode": str,
            "result": {
                "success": bool,
                "markdown": str (extracted content in markdown),
                "extracted_content": str (structured data if extraction_config provided),
                "screenshot": str (base64-encoded if screenshot=True),
                "url": str (final URL after redirects),
                "status_code": int (HTTP status code)
            },
            "user_id": str
        }
    
    Errors:
        - "Crawl4AI URL not configured" - CRAWL4AI_URL environment variable not set
        - "Request timeout" - Crawl did not complete within timeout
        - "API error {code}" - Crawl4AI API returned an error
        - "Connection error" - Failed to connect to Crawl4AI service
    
    Example:
        User: "Crawl https://example.com and extract all article titles"
        Tool call: crawl4ai_crawl(
            url="https://example.com",
            css_selector=".article-title"
        )
        Returns: JSON with markdown content and extracted titles
    """
    try:
        safe_log_info(logger, f"[crawl4ai_crawl] Starting", url=url, mode=mode, priority=priority)
        
        # Validate URL
        if not url or not isinstance(url, str) or len(url.strip()) == 0:
            error_msg = "url must be a non-empty string"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Get Crawl4AI URL and token from runtime state (standard approach)
        base_url, token = _get_crawl4ai_config_from_runtime(runtime)
        if not base_url:
            error_msg = "Crawl4AI URL not found in agent state. Ensure 'environment_variables' contains CRAWL4AI_URL for a tool instance."
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not token:
            error_msg = "Crawl4AI API token not found in agent state. Ensure 'environment_variables' contains CRAWL4AI_API_TOKEN for a tool instance."
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
            return json.dumps({"status": "error", "message": error_msg})
        
        masked_token = mask_api_key(token)
        safe_log_info(logger, "[crawl4ai_crawl] Crawl4AI config retrieved", 
                     base_url=base_url, 
                     token_masked=masked_token, 
                     url=url)
        
        # Build request payload
        # API expects urls as a list, not a string
        request_data: Dict[str, Any] = {
            "urls": [url],  # Must be a list
            "priority": priority
        }
        
        # Set cache_mode to "enabled" by default if not provided
        # According to Crawl4AI docs: cache_mode can be "enabled", "disabled", "bypass", "read_only", "write_only"
        request_data["cache_mode"] = cache_mode if cache_mode else "enabled"
        
        # Initialize crawler_params if not provided
        if crawler_params is None:
            crawler_params = {}
        
        # Set only_text=True for text-only extraction (faster, lighter)
        # This disables images and heavy content for speed
        crawler_params.setdefault("only_text", True)
        
        request_data["crawler_params"] = crawler_params
        
        if session_id:
            request_data["session_id"] = session_id
        if js_code:
            request_data["js_code"] = js_code
        if wait_for:
            request_data["wait_for"] = wait_for
        if css_selector:
            request_data["css_selector"] = css_selector
        if extraction_config:
            request_data["extraction_config"] = extraction_config
        if screenshot:
            request_data["screenshot"] = True
        if extra:
            request_data["extra"] = extra
        
        headers = _build_headers(runtime)
        
        # Execute based on mode
        # Note: The API only has /crawl endpoint which returns results directly
        # /crawl_direct and /crawl_sync don't exist in this API version
        # All modes use /crawl endpoint which returns results synchronously
        endpoint = f"{base_url}/crawl"
        safe_log_info(logger, "[crawl4ai_crawl] Sending request to Crawl4AI API", 
                     endpoint=endpoint, 
                     mode=mode, 
                     url=url,
                     timeout=timeout,
                     cache_mode=request_data.get("cache_mode"),
                     only_text=crawler_params.get("only_text"),
                     has_session_id=bool(session_id),
                     has_css_selector=bool(css_selector),
                     has_wait_for=bool(wait_for),
                     screenshot=screenshot,
                     has_extraction_config=bool(extraction_config))
        
        try:
            response = requests.post(endpoint, json=request_data, headers=headers, timeout=timeout)
            safe_log_debug(logger, "[crawl4ai_crawl] API response received", 
                          status_code=response.status_code, 
                          url=url)
            
            if response.status_code == 403:
                error_msg = "API token is invalid or missing"
                safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", 
                             url=url, 
                             status_code=403,
                             token_masked=mask_api_key(token))
                return json.dumps({"status": "error", "message": error_msg})
            
            response.raise_for_status()
            result = response.json()
 
            # API returns: {"success": true, "results": [{"url": "...", "markdown": {"raw_markdown": "..."}, ...}]}
            success = result.get("success", False)
            results = result.get("results", [])
            
            safe_log_info(logger, f"[crawl4ai_crawl] Crawl complete", 
                         url=url, mode=mode, success=success, results_count=len(results))
            
            # Extract raw_markdown from the first result
            if results and len(results) > 0:
                first_result = results[0]
                markdown_data = first_result.get("markdown", {})
                raw_markdown = markdown_data.get("raw_markdown", "")
                
                if raw_markdown:
                    safe_log_info(logger, f"[crawl4ai_crawl] Returning raw_markdown", 
                                 url=url, markdown_length=len(raw_markdown))
                    return raw_markdown
                else:
                    error_msg = "No raw_markdown found in crawl result"
                    safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
                    return json.dumps({"status": "error", "message": error_msg})
            else:
                error_msg = "No results returned from crawl"
                safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
                return json.dumps({"status": "error", "message": error_msg})
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout} seconds"
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
            return json.dumps({"status": "error", "message": error_msg})
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_text = e.response.text[:200] if e.response.text else "No error details"
                error_msg = f"HTTP error {e.response.status_code}: {error_text}"
            else:
                error_msg = f"HTTP error: {str(e)}"
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
            return json.dumps({"status": "error", "message": error_msg})
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})
        
    except Exception as e:
        error_msg = f"Unexpected error in crawl4ai_crawl: {str(e)}"
        safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})

