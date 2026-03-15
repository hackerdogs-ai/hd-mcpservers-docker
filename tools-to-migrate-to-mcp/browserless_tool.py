"""
Browser Tools
-------------
This module defines custom LangChain tools for web scraping and analysis.
"""

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, Optional
from hd_logging import setup_logger
import requests
import json
import os
from unstructured.partition.html import partition_html
from dotenv import load_dotenv
import logging

logger = setup_logger(__name__, log_file_path="logs/browserless_tool.log")
load_dotenv(override=True)

# --- Browser Tools ---

class BrowserInput(BaseModel):
    """
    Input schema for the BrowserTools.
    
    Attributes:
        website: The full URL (including http:// or https://) of the website to scrape and analyze.
                 Must be a valid, accessible URL. Examples: "https://example.com", "https://www.cisa.gov/news-events/cybersecurity-advisories"
    """
    website: str = Field(..., description="URL of the website to scrape and analyze. Must include protocol (http:// or https://).")
    
class BrowserTools(BaseTool):
    """
    Internet Research Tool for Web Scraping and Content Analysis.
    
    This tool enables the agent to scrape and analyze website content for cybersecurity research,
    threat intelligence gathering, and information retrieval. It uses a headless browser service
    (Browserless) to fetch and parse HTML content, extracting readable text from web pages.
    
    **When to use this tool:**
    - Researching cybersecurity threats, vulnerabilities, or security advisories
    - Gathering threat intelligence from security websites and feeds
    - Retrieving current information from websites that may not have APIs
    - Analyzing security blog posts, news articles, or documentation
    - Extracting information from security vendor websites or CVE databases
    - Researching specific security topics, tools, or techniques mentioned in conversations
    
    **When NOT to use this tool:**
    - For websites that require authentication or login (will fail)
    - For websites with heavy JavaScript rendering (may not capture dynamic content)
    - For very large websites or pages (may timeout or return truncated content)
    - For websites that block automated access or have rate limiting
    - If the information is already available through other tools or APIs
    
    **Input requirements:**
    - Must provide a valid URL with protocol (http:// or https://)
    - URL must be accessible from the server where this tool runs
    - Website should be publicly accessible (no authentication required)
    
    **Output:**
    - Returns extracted text content from the webpage
    - Content is cleaned and structured for easy reading
    - May include headings, paragraphs, lists, and other text elements
    - Returns error message if scraping fails (network issues, invalid URL, etc.)
    
    **Limitations:**
    - Does not execute JavaScript (static HTML only)
    - May not capture content loaded dynamically via AJAX
    - Large pages may be truncated
    - Rate limiting may apply depending on Browserless service configuration
    - Some websites may block automated access
    
    **Example use cases:**
    1. "Research the latest CVE-2024-1234 vulnerability details from cve.mitre.org"
    2. "Get information about the latest security advisory from CISA website"
    3. "Scrape threat intelligence from [security vendor] blog about recent attacks"
    4. "Analyze the content of this security research paper: https://example.com/paper.pdf"
    
    **Configuration:**
    Requires BROWSERLESS_URL and BROWSERLESS_API_KEY environment variables to be configured.
    The tool connects to a Browserless service instance to perform the web scraping.
    """
    name: str = "Internet_Research_Tool"
    description: str = (
        "Scrape and analyze website content for cybersecurity related information, threat intelligence research. "
        "Use this tool to research the latest information about identified threats from cybersecurity websites, "
        "threat intelligence feeds, and security advisories. "
        "IMPORTANT: Only use for publicly accessible websites. Provide full URLs with http:// or https:// protocol. "
        "Best for: security blogs, CVE databases, vendor advisories, threat intelligence feeds, security news sites. "
        "NOT suitable for: authenticated sites, heavy JavaScript pages, or sites that block automated access."
    )
    args_schema: Type[BaseModel] = BrowserInput

    def _run(self, website: str) -> str:
        """
        Scrape website content and return raw content for agent processing.
        
        This method performs the actual web scraping operation:
        1. Validates and constructs the Browserless API URL
        2. Sends HTTP POST request to Browserless service with target URL
        3. Receives HTML content from Browserless
        4. Parses HTML using unstructured library to extract readable text
        5. Returns cleaned, structured text content
        
        Args:
            website: The full URL (with protocol) of the website to scrape.
                    Example: "https://www.cisa.gov/news-events/cybersecurity-advisories"
        
        Returns:
            str: Extracted and cleaned text content from the webpage.
                 Content includes headings, paragraphs, lists, and other text elements.
                 Returns error message string if scraping fails.
        
        Raises:
            No exceptions are raised - all errors are caught and returned as error message strings.
        """
        try:
            logger.info(f"Scraping website: {website}")
            
            # Get browserless URL from environment variable
            browserless_url = os.getenv('BROWSERLESS_URL', 'http://localhost:3000/content')
            api_key = os.getenv('BROWSERLESS_API_KEY', '')
            
            # Use URL as-is if it already contains a token, otherwise add token
            if 'token=' in browserless_url:
                url = browserless_url
            elif '?' in browserless_url:
                url = f"{browserless_url}&token={api_key}"
            else:
                url = f"{browserless_url}?token={api_key}"
            payload = json.dumps({"url": website})
            headers = {'cache-control': 'no-cache', 'content-type': 'application/json'}
            logger.info(f"[BROWSERLESS_TOOL] Sending request to browserless: {url}")
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[BROWSERLESS_TOOL] Payload: {payload}")
                logger.debug(f"[BROWSERLESS_TOOL] Headers: {headers}")
            response = requests.request("POST", url, headers=headers, data=payload)
           
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[BROWSERLESS_TOOL] Response: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"[BROWSERLESS_TOOL] Failed to fetch website content. Status code: {response.status_code}")
                return f"[BROWSERLESS_TOOL] Error: Failed to fetch website content. Status code: {response.status_code}"
            
            # Parse HTML content
            elements = partition_html(text=response.text)
            content = "\n\n".join([str(el) for el in elements])
            
            logger.info(f"[BROWSERLESS_TOOL] Successfully scraped {len(content)} characters from {website}")
            return content
            
        except Exception as e:
            logger.error(f"[BROWSERLESS_TOOL] Error while processing website {website}: {str(e)}", exc_info=True)
            return f"[BROWSERLESS_TOOL] Error while processing website: {str(e)}"
    
    async def _arun(self, website: str) -> str:
        """
        Async version of _run for better performance in async contexts.
        
        This method provides an asynchronous interface for the web scraping operation,
        allowing it to be used efficiently in async agent execution flows. Currently
        delegates to the synchronous _run method, but structured for future async optimization.
        
        Args:
            website: The full URL (with protocol) of the website to scrape.
                    Example: "https://www.cisa.gov/news-events/cybersecurity-advisories"
        
        Returns:
            str: Extracted and cleaned text content from the webpage, same as _run().
        
        Note:
            Currently implemented as a wrapper around _run() for compatibility.
            Future versions may implement true async HTTP requests for better performance.
        """
        return self._run(website)

# You can add other tools here, for example:
# class ThreatIntelTool(BaseTool): ...
# class SystemIsolationTool(BaseTool): ...
