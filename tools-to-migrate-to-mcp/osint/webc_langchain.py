"""
Web Content Analysis Tools for LangChain Agents

This module provides LangChain tools for comprehensive web content and text analysis:
- Webpage analysis (content extraction, metadata, language detection)
- Text analysis (entities, readability, key terms, similarity)
- Domain/IP analysis (DNS, WHOIS, geolocation, certificates)
- Sensitive data detection (PII, credit cards, SSN, etc.)
- Language detection and translation
- Network service scanning and pinging
- Geographic distance calculations

Reference: shared/modules/txtanalytics/nlp_general_analytics.py

Key Features:
- Comprehensive web content analysis
- NLP-powered text processing
- Domain and IP intelligence
- Sensitive data detection
- Multi-language support
- Network reconnaissance
- Geographic analysis

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.osint.webc_langchain import (
        webc_analyze_webpage,
        webc_extract_text,
        webc_detect_language,
        webc_find_sensitive_data
    )
    
    agent = create_agent(
        model=llm,
        tools=[webc_analyze_webpage, webc_extract_text, ...],
        system_prompt="You are a web content analyst..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Analyze https://example.com"}],
        "user_id": "analyst_001"
    })
"""

import json
import datetime
from typing import Optional, Dict, Any, List, Tuple
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from shared.modules.txtanalytics.nlp_general_analytics import (
    get_webpagemodel,
    get_webpagemodel_meta,
    get_text_from_webpage,
    get_webpage_response,
    detect_language_from_text,
    detect_multiple_languages_from_text,
    detect_webpage_language_from_url,
    detect_webpage_multiple_languages,
    translate_text,
    translate_webpage_to_english,
    get_text_model,
    extract_entities_from_text,
    extract_entities_from_webpage,
    extract_emails_from_text,
    extract_emails_from_webpage,
    find_sensitive_data_in_text,
    get_domain_model,
    resolve_domain_ips,
    get_domain_whois,
    get_ip_location,
    get_ip_whois,
    get_certificate_info_for_hostname,
    get_domain_tld_info,
    calculate_similarity_all,
    calculate_similarity_spacy,
    extract_keyterms_all,
    extract_keyterms_textrank,
    get_readability_statistics,
    scan_service,
    ping_service,
    calculate_geo_distance,
    calculate_geoip_distance,
    calculate_geodomain_distance,
    remove_stopwords_from_text,
    get_creditcard_details
)

logger = setup_logger(__name__, log_file_path="logs/webc_tool.log")


def _json_safe(value: Any, _depth: int = 0, _max_depth: int = 4) -> Any:
    """Convert common Python objects into JSON-safe structures."""
    if _depth > _max_depth:
        return str(value)

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (datetime.datetime, datetime.date)):
        try:
            return value.isoformat()
        except Exception:
            return str(value)

    if isinstance(value, dict):
        return {str(k): _json_safe(v, _depth=_depth + 1, _max_depth=_max_depth) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v, _depth=_depth + 1, _max_depth=_max_depth) for v in value]

    # Fallback for any custom objects
    return str(value)


def _serialize_domain_whois(whois_data: Any) -> Optional[Dict[str, Any]]:
    """
    Convert various WHOIS/RDAP return types into a JSON-friendly dict.

    - RDAP fallback returns a dict -> returned as-is (json-safe conversion still applied).
    - python-whois / whois libs often return custom objects -> extract common fields.
    """
    if not whois_data:
        return None

    # RDAP fallback path (nlp_general_analytics.gwhois may return a dict)
    if isinstance(whois_data, dict):
        return _json_safe(whois_data)

    # Some libraries expose mapping-like objects
    try:
        if hasattr(whois_data, "items"):
            as_dict = dict(whois_data.items())
            if as_dict:
                return _json_safe(as_dict)
    except Exception:
        pass

    # Extract a stable subset of common fields across popular WHOIS libraries
    common_fields = [
        "domain_name",
        "name",
        "domain",
        "registrar",
        "whois_server",
        "creation_date",
        "updated_date",
        "expiration_date",
        "name_servers",
        "status",
        "emails",
        "org",
        "organization",
        "country",
        "dnssec",
    ]

    extracted: Dict[str, Any] = {}
    for field in common_fields:
        try:
            if hasattr(whois_data, field):
                val = getattr(whois_data, field)
                if val is not None and val != "":
                    extracted[field] = _json_safe(val)
        except Exception:
            continue

    if extracted:
        return extracted

    # Last resort: try vars()
    try:
        raw = vars(whois_data)
        if isinstance(raw, dict) and raw:
            return _json_safe({k: v for k, v in raw.items() if not str(k).startswith("_")})
    except Exception:
        pass

    return {"raw": str(whois_data)}


class WebContentSecurityAgentState(AgentState):
    """Extended agent state for Web Content Analysis operations."""
    user_id: str = ""


# ============================================================================
# WEBPAGE ANALYSIS TOOLS
# ============================================================================

@tool
def webc_analyze_webpage(
    runtime: ToolRuntime,
    url: str,
    extract_entities: bool = False
) -> str:
    """
    Comprehensive webpage analysis with full metadata extraction and intelligence gathering.
    
    This is the most comprehensive webpage analysis tool. It fetches a webpage, extracts
    all visible text content, and performs extensive analysis including domain intelligence,
    geolocation, WHOIS lookups, and optional named entity recognition. This tool combines
    multiple analysis capabilities into a single operation.
    
    What it does:
        - Fetches HTML content from the URL and extracts visible text (excludes scripts/styles)
        - Detects the primary language of the webpage content
        - Extracts metadata: title, description, keywords from HTML meta tags
        - Parses domain components: FQDN, domain, registered domain, subdomain, TLD suffix
        - Resolves domain to IP addresses and performs geolocation lookup for each IP
        - Performs WHOIS lookup to get domain registration information
        - Extracts all email addresses and their domains from the content
        - Collects all links (internal and external) found on the page
        - Optionally extracts named entities (people, organizations, locations) using NLP
    
    When to use:
        - User asks to "analyze a webpage" or "get information about a URL"
        - Need comprehensive intelligence about a website in a single operation
        - Performing initial reconnaissance on a target website
        - Need to understand domain infrastructure, IP locations, and registration details
        - Want to extract contact information (emails) from a webpage
        - Need to understand the language and content structure of a webpage
    
    When NOT to use:
        - Only need text content (use webc_extract_text instead - faster)
        - Only need HTTP response metadata (use webc_get_webpage_response instead)
        - Only need domain information (use webc_analyze_domain instead - faster)
        - Only need language detection (use webc_detect_language instead - faster)
        - URL is not accessible or requires authentication
        - Need real-time analysis of dynamic content (this tool captures static HTML)
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        url: Full URL of the webpage to analyze. Must include protocol (http:// or https://).
            Examples: "https://example.com", "http://192.168.1.1", "https://subdomain.example.com/path"
        extract_entities: Boolean flag to enable named entity extraction. 
            - True: Extracts named entities (PERSON, ORG, GPE, DATE, etc.) using spaCy NLP.
                    Slower but provides structured information about people, organizations, locations.
            - False (default): Skips entity extraction for faster processing.
    
    Returns:
        JSON string with status and comprehensive analysis results:
        {
            "status": "success" | "error",
            "url": "The analyzed URL",
            "fqdn": "Fully qualified domain name (e.g., 'www.example.com')",
            "domain": "Domain name without subdomain (e.g., 'example')",
            "registered_domain": "Domain + TLD (e.g., 'example.com')",
            "subdomain": "Subdomain part (e.g., 'www')",
            "suffix": "Top-level domain (e.g., 'com')",
            "language": "ISO 639-1 language code (e.g., 'en', 'fr', 'es')",
            "text_content": "All visible text extracted from the webpage",
            "title": "Page title from <title> tag",
            "description": "Meta description from <meta name='description'>",
            "keywords": "Meta keywords from <meta name='keywords'>",
            "emails": ["list", "of", "email", "addresses"],
            "email_domains": ["list", "of", "email", "domains"],
            "ip_locations": [
                {
                    "ip": "IP address",
                    "location": {
                        "city": "City name",
                        "country": "Country name",
                        "latitude": 37.7749,
                        "longitude": -122.4194
                    }
                }
            ],
            "whois": "WHOIS registration information as string",
            "links": ["list", "of", "all", "links", "found"],
            "entities": [
                {"key": "entity text", "value": "ENTITY_TYPE"}
            ]  // Only present if extract_entities=True
        }
    
    Examples:
        Basic analysis:
            url="https://example.com", extract_entities=False
            Returns: Domain info, IPs, emails, links, language, metadata
        
        Full analysis with entities:
            url="https://company.com/about", extract_entities=True
            Returns: Everything above plus named entities (people, organizations, locations)
    
    Related tools:
        - webc_extract_text: Faster if you only need text content
        - webc_analyze_domain: Faster if you only need domain/IP/WHOIS info
        - webc_detect_language: Faster if you only need language detection
        - webc_extract_entities: If you already have text and only need entities
        - webc_extract_emails: If you already have text and only need emails
    
    Performance notes:
        - Processing time: 2-10 seconds depending on page size and extract_entities flag
        - Entity extraction adds 1-5 seconds for typical pages
        - Large pages (>1MB) may take longer
        - Network timeouts may occur for slow or unreachable URLs
    """
    try:
        safe_log_info(logger, "[webc_analyze_webpage] Starting analysis", 
                     url=url, extract_entities=extract_entities)
        
        # Validate inputs
        if not url or not isinstance(url, str):
            error_msg = "url must be a non-empty string"
            safe_log_error(logger, "[webc_analyze_webpage] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            error_msg = "url must start with http:// or https://"
            safe_log_error(logger, "[webc_analyze_webpage] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_analyze_webpage] Fetching webpage model", url=url)
        
        # Get comprehensive webpage model
        webpage_model = get_webpagemodel(url, extract_e=extract_entities)
        
        # Convert model to dictionary for JSON serialization
        result = {
            "status": "success",
            "url": webpage_model.url if hasattr(webpage_model, 'url') else url,
            "fqdn": webpage_model.fqdn if hasattr(webpage_model, 'fqdn') else None,
            "domain": webpage_model.domain if hasattr(webpage_model, 'domain') else None,
            "registered_domain": webpage_model.registered_domain if hasattr(webpage_model, 'registered_domain') else None,
            "subdomain": webpage_model.subdomain if hasattr(webpage_model, 'subdomain') else None,
            "suffix": webpage_model.suffix if hasattr(webpage_model, 'suffix') else None,
            "language": webpage_model.language if hasattr(webpage_model, 'language') else None,
            "text_content": webpage_model.text_content if hasattr(webpage_model, 'text_content') else None,
            "title": webpage_model.title if hasattr(webpage_model, 'title') else None,
            "description": webpage_model.description if hasattr(webpage_model, 'description') else None,
            "keywords": webpage_model.keywords if hasattr(webpage_model, 'keywords') else None,
            "emails": list(webpage_model.emails) if hasattr(webpage_model, 'emails') and webpage_model.emails else [],
            "email_domains": list(webpage_model.email_domains) if hasattr(webpage_model, 'email_domains') and webpage_model.email_domains else [],
            "ip_locations": [
                {
                    "ip": loc.ip if hasattr(loc, 'ip') else None,
                    "location": {
                        "city": loc.location.city if hasattr(loc, 'location') and loc.location and hasattr(loc.location, 'city') else None,
                        "country": loc.location.country if hasattr(loc, 'location') and loc.location and hasattr(loc.location, 'country') else None,
                        "latitude": loc.location.latitude if hasattr(loc, 'location') and loc.location and hasattr(loc.location, 'latitude') else None,
                        "longitude": loc.location.longitude if hasattr(loc, 'location') and loc.location and hasattr(loc.location, 'longitude') else None,
                    } if hasattr(loc, 'location') and loc.location else None
                }
                for loc in (webpage_model.ip_locations if hasattr(webpage_model, 'ip_locations') and webpage_model.ip_locations else [])
            ],
            "whois": str(webpage_model.whois) if hasattr(webpage_model, 'whois') and webpage_model.whois else None,
            "links": list(webpage_model.links.keys()) if hasattr(webpage_model, 'links') and webpage_model.links else [],
            "entities": [
                {"key": e.key, "value": e.value}
                for e in (webpage_model.entities if hasattr(webpage_model, 'entities') and webpage_model.entities else [])
            ] if extract_entities else [],
            "intents": [
                {"key": i.key, "value": i.value}
                for i in (webpage_model.intents if hasattr(webpage_model, 'intents') and webpage_model.intents else [])
            ] if extract_entities else []
        }
        
        safe_log_info(logger, "[webc_analyze_webpage] Analysis complete", 
                     url=url, 
                     language=result.get("language"),
                     emails_found=len(result.get("emails", [])),
                     links_found=len(result.get("links", [])))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Webpage analysis failed: {str(e)}"
        safe_log_error(logger, "[webc_analyze_webpage] Error", 
                     exc_info=True,
                     error=str(e),
                     url=url if 'url' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_extract_text(
    runtime: ToolRuntime,
    url: str
) -> str:
    """
    Extract visible text content from a webpage, removing all HTML markup.
    
    This is a lightweight tool that fetches a webpage and extracts only the visible
    text content, stripping out all HTML tags, scripts, styles, comments, and other
    non-visible elements. The result is clean, readable text suitable for further
    text analysis or processing.
    
    What it does:
        - Fetches HTML content from the URL
        - Parses HTML and extracts only visible text content
        - Removes HTML tags, scripts, stylesheets, comments, and metadata
        - Returns plain text without any markup
    
    When to use:
        - User asks to "extract text from a webpage" or "get the text content"
        - Need clean text for further NLP analysis (entities, sentiment, etc.)
        - Want to process webpage content without HTML markup
        - Need text content for translation or language detection
        - Preparing text for readability analysis or key term extraction
    
    When NOT to use:
        - Need comprehensive webpage analysis (use webc_analyze_webpage instead)
        - Need metadata like title, description, keywords (use webc_analyze_webpage)
        - Need domain/IP/WHOIS information (use webc_analyze_domain)
        - Need HTTP response headers or status codes (use webc_get_webpage_response)
        - URL requires authentication or is behind a login
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        url: Full URL of the webpage to extract text from. Must include protocol.
            Examples: "https://example.com", "http://192.168.1.1/page.html"
    
    Returns:
        JSON string with status and extracted text:
        {
            "status": "success" | "error",
            "url": "The requested URL",
            "text_content": "All visible text from the webpage as plain text",
            "text_length": 1234  // Number of characters in extracted text
        }
    
    Examples:
        Basic extraction:
            url="https://example.com"
            Returns: Clean text content without HTML markup
        
        Large page:
            url="https://news-site.com/article"
            Returns: Full article text, excluding navigation, ads, scripts
    
    Related tools:
        - webc_analyze_webpage: Comprehensive analysis including text + metadata + domain info
        - webc_analyze_text: Analyze extracted text with NLP (entities, readability, etc.)
        - webc_detect_language: Detect language of extracted text
        - webc_translate_webpage: Translate webpage text to English
    
    Performance notes:
        - Processing time: 1-3 seconds for typical pages
        - Very fast compared to comprehensive analysis tools
        - Large pages (>1MB) may take longer
        - Returns empty text_content if page has no visible text
    """
    try:
        safe_log_info(logger, "[webc_extract_text] Starting extraction", url=url)
        
        # Validate inputs
        if not url or not isinstance(url, str):
            error_msg = "url must be a non-empty string"
            safe_log_error(logger, "[webc_extract_text] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            error_msg = "url must start with http:// or https://"
            safe_log_error(logger, "[webc_extract_text] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_extract_text] Fetching text", url=url)
        
        text_content = get_text_from_webpage(url)
        
        result = {
            "status": "success",
            "url": url,
            "text_content": text_content,
            "text_length": len(text_content) if text_content else 0
        }
        
        safe_log_info(logger, "[webc_extract_text] Extraction complete", 
                     url=url, text_length=result["text_length"])
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Text extraction failed: {str(e)}"
        safe_log_error(logger, "[webc_extract_text] Error", 
                     exc_info=True,
                     error=str(e),
                     url=url if 'url' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_get_webpage_response(
    runtime: ToolRuntime,
    url: str
) -> str:
    """
    Fetch webpage with complete HTTP response metadata and timing information.
    
    This tool performs a raw HTTP GET request and captures all response details
    including status codes, headers, timing metrics, and the full response body.
    Useful for debugging connectivity issues, analyzing server behavior, and
    understanding HTTP-level details that aren't available from content extraction.
    
    What it does:
        - Makes HTTP GET request to the URL
        - Captures HTTP status code (200, 404, 500, etc.)
        - Records all response headers (Content-Type, Server, etc.)
        - Measures server response time and total request time
        - Returns full response body as text
        - Captures any HTTP-level errors
    
    When to use:
        - User asks to "check if a URL is accessible" or "get HTTP status"
        - Need to debug connectivity or HTTP errors
        - Want to analyze response headers (server type, security headers, etc.)
        - Need to measure response times for performance analysis
        - Checking redirect chains or HTTP authentication requirements
        - Verifying if a URL returns specific status codes (404, 403, etc.)
    
    When NOT to use:
        - Need webpage content analysis (use webc_analyze_webpage instead)
        - Need only text content (use webc_extract_text instead - faster)
        - Need domain/IP intelligence (use webc_analyze_domain instead)
        - URL requires POST requests or custom headers (this tool only does GET)
        - Need to follow redirects automatically (this captures redirect responses)
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        url: Full URL to fetch. Must include protocol (http:// or https://).
            Examples: "https://example.com", "http://api.example.com/endpoint"
    
    Returns:
        JSON string with status and HTTP response details:
        {
            "status": "success" | "error",
            "url": "The requested URL",
            "status_code": 200,  // HTTP status code (200=OK, 404=Not Found, 500=Server Error, etc.)
            "content": "Full response body as text",
            "headers": {
                "Content-Type": "text/html; charset=utf-8",
                "Server": "nginx/1.18.0",
                // ... all other response headers
            },
            "response_time_ms": 150,  // Server response time in milliseconds
            "response_time_calculated_ms": 200,  // Total request time (including network latency)
            "http_error": null  // Error message if request failed, null if successful
        }
    
    Examples:
        Successful request:
            url="https://example.com"
            Returns: status_code=200, content=HTML, headers=all headers, timing info
        
        Not found:
            url="https://example.com/nonexistent"
            Returns: status_code=404, http_error="404 Not Found"
        
        Server error:
            url="https://example.com/error"
            Returns: status_code=500, http_error="500 Internal Server Error"
    
    Related tools:
        - webc_analyze_webpage: For content analysis after verifying accessibility
        - webc_extract_text: For extracting text from accessible pages
        - webc_scan_service: For checking if a port/service is open
    
    Performance notes:
        - Processing time: 1-5 seconds depending on server response time
        - Timeouts may occur for slow or unreachable servers
        - Large response bodies may take longer to download
        - Follows redirects automatically (check status_code for redirect codes)
    """
    try:
        safe_log_info(logger, "[webc_get_webpage_response] Starting request", url=url)
        
        # Validate inputs
        if not url or not isinstance(url, str):
            error_msg = "url must be a non-empty string"
            safe_log_error(logger, "[webc_get_webpage_response] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            error_msg = "url must start with http:// or https://"
            safe_log_error(logger, "[webc_get_webpage_response] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_get_webpage_response] Fetching response", url=url)
        
        response = get_webpage_response(url)
        
        result = {
            "status": "success",
            "url": url,
            "status_code": response.status_code if hasattr(response, 'status_code') else None,
            "content": response.content if hasattr(response, 'content') else None,
            "headers": dict(response.headers) if hasattr(response, 'headers') and response.headers else {},
            "response_time_ms": response.response_time_ms if hasattr(response, 'response_time_ms') else None,
            "response_time_calculated_ms": response.response_time_calculated_ms if hasattr(response, 'response_time_calculated_ms') else None,
            "http_error": response.http_error if hasattr(response, 'http_error') else None
        }
        
        safe_log_info(logger, "[webc_get_webpage_response] Request complete", 
                     url=url, 
                     status_code=result.get("status_code"),
                     response_time_ms=result.get("response_time_ms"))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Webpage response fetch failed: {str(e)}"
        safe_log_error(logger, "[webc_get_webpage_response] Error", 
                     exc_info=True,
                     error=str(e),
                     url=url if 'url' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


# ============================================================================
# LANGUAGE DETECTION & TRANSLATION TOOLS
# ============================================================================

@tool
def webc_detect_language(
    runtime: ToolRuntime,
    text: Optional[str] = None,
    url: Optional[str] = None
) -> str:
    """
    Detect the primary language of text content or webpage using statistical language detection.
    
    This tool uses the langdetect library which employs statistical language models to identify
    the most likely language of text content. It can analyze either provided text directly or
    extract text from a webpage URL. Returns a single ISO 639-1 language code representing
    the detected primary language.
    
    What it does:
        - Analyzes text using statistical language models (n-gram analysis)
        - Identifies the most probable language from 55+ supported languages
        - Returns ISO 639-1 language code (2-letter code like 'en', 'fr', 'es')
        - Works with text as short as a few words (though longer text is more accurate)
    
    When to use:
        - User asks "what language is this text?" or "detect the language"
        - Need to determine if content needs translation
        - Filtering content by language
        - Processing multilingual content and need to identify language
        - Quick language check before translation or analysis
    
    When NOT to use:
        - Need confidence scores for multiple languages (use webc_detect_multiple_languages instead)
        - Text is too short (< 3 words) - results may be inaccurate
        - Need to detect multiple languages in mixed-language text (use webc_detect_multiple_languages)
        - Already know the language and just need translation (use webc_translate_text directly)
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to analyze. Must be non-empty string if provided.
            Examples: "Hello world", "Bonjour le monde", "Hola mundo"
        url: URL of webpage to analyze. Must include http:// or https:// if provided.
            Examples: "https://example.com", "https://fr.wikipedia.org"
        Note: Exactly one of text or url must be provided, not both.
    
    Returns:
        JSON string with status and language detection result:
        {
            "status": "success" | "error",
            "language": "en",  // ISO 639-1 language code (2 letters)
            "source": "text" | "url"  // Indicates whether text or url was analyzed
        }
        Common language codes: "en" (English), "fr" (French), "es" (Spanish), "de" (German),
        "it" (Italian), "pt" (Portuguese), "ru" (Russian), "zh" (Chinese), "ja" (Japanese),
        "ko" (Korean), "ar" (Arabic), "hi" (Hindi), etc.
    
    Examples:
        Detect from text:
            text="Hello world"
            Returns: {"status": "success", "language": "en", "source": "text"}
        
        Detect from webpage:
            url="https://fr.wikipedia.org"
            Returns: {"status": "success", "language": "fr", "source": "url"}
        
        Mixed language (returns primary):
            text="Hello world. Bonjour le monde."
            Returns: {"status": "success", "language": "en", "source": "text"}
            (English detected as primary, but text contains French)
    
    Related tools:
        - webc_detect_multiple_languages: For confidence scores and multiple language detection
        - webc_translate_text: Translate text after detecting language
        - webc_translate_webpage: Translate webpage after detecting language
        - webc_analyze_webpage: Includes language detection as part of comprehensive analysis
    
    Accuracy notes:
        - Best accuracy with text > 50 characters
        - Very short text (< 10 characters) may be inaccurate
        - Works best with complete sentences
        - Accuracy improves with longer text samples
        - May struggle with code snippets, URLs, or mixed-language content
    """
    try:
        safe_log_info(logger, "[webc_detect_language] Starting detection", 
                     has_text=bool(text), has_url=bool(url))
        
        # Validate inputs
        if not text and not url:
            error_msg = "Either text or url must be provided"
            safe_log_error(logger, "[webc_detect_language] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if text and url:
            error_msg = "Provide either text or url, not both"
            safe_log_error(logger, "[webc_detect_language] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_detect_language] Detecting language")
        
        if url:
            if not url.startswith(("http://", "https://")):
                error_msg = "url must start with http:// or https://"
                safe_log_error(logger, "[webc_detect_language] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            language = detect_webpage_language_from_url(url)
            source = "url"
        else:
            if not isinstance(text, str) or len(text.strip()) == 0:
                error_msg = "text must be a non-empty string"
                safe_log_error(logger, "[webc_detect_language] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            language = detect_language_from_text(text)
            source = "text"
        
        result = {
            "status": "success",
            "language": language,
            "source": source
        }
        
        safe_log_info(logger, "[webc_detect_language] Detection complete", 
                     language=language, source=source)
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Language detection failed: {str(e)}"
        safe_log_error(logger, "[webc_detect_language] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_detect_multiple_languages(
    runtime: ToolRuntime,
    text: Optional[str] = None,
    url: Optional[str] = None
) -> str:
    """
    Detect multiple possible languages with confidence scores.
    
    Returns a list of possible languages with their confidence probabilities.
    Useful when text might contain multiple languages or when confidence
    information is needed.
    
    When to use:
        - Need confidence scores for language detection
        - Text might contain multiple languages
        - Need to rank languages by probability
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to analyze (either text or url must be provided).
        url: URL of webpage to analyze (either text or url must be provided).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - languages: List of language objects with lang (code) and prob (probability)
        - source: "text" or "url" indicating the source analyzed
    
    Examples:
        Detect from text:
            text="Hello world"
            Returns: {"status": "success", "language": "en", "source": "text"}
        
        Detect from webpage:
            url="https://example.com"
            Returns: {"status": "success", "language": "en", "source": "url"}
    """
    try:
        safe_log_info(logger, "[webc_detect_multiple_languages] Starting detection", 
                     has_text=bool(text), has_url=bool(url))
        
        # Validate inputs
        if not text and not url:
            error_msg = "Either text or url must be provided"
            safe_log_error(logger, "[webc_detect_multiple_languages] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if text and url:
            error_msg = "Provide either text or url, not both"
            safe_log_error(logger, "[webc_detect_multiple_languages] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_detect_multiple_languages] Detecting languages")
        
        if url:
            if not url.startswith(("http://", "https://")):
                error_msg = "url must start with http:// or https://"
                safe_log_error(logger, "[webc_detect_multiple_languages] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            languages = detect_webpage_multiple_languages(url)
            source = "url"
        else:
            if not isinstance(text, str) or len(text.strip()) == 0:
                error_msg = "text must be a non-empty string"
                safe_log_error(logger, "[webc_detect_multiple_languages] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            languages = detect_multiple_languages_from_text(text)
            source = "text"
        
        result = {
            "status": "success",
            "languages": [
                {"lang": lang.lang, "prob": lang.prob}
                for lang in languages
            ] if languages else [],
            "source": source
        }
        
        safe_log_info(logger, "[webc_detect_multiple_languages] Detection complete", 
                     languages_count=len(result["languages"]), source=source)
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Multiple language detection failed: {str(e)}"
        safe_log_error(logger, "[webc_detect_multiple_languages] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_translate_text(
    runtime: ToolRuntime,
    text: str,
    to_lang: str = "en"
) -> str:
    """
    Translate text content to a target language.
    
    Translates text using Google Translate (via TextBlob) with fallback
    to translate library. Automatically handles chunking for long texts.
    
    When to use:
        - Need to translate text to another language
        - Convert non-English content to English for analysis
        - Multi-language content processing
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to translate.
        to_lang: Target language code (ISO 639-1 format, default: "en").
                 Examples: "en", "fr", "es", "de", "zh", "ja"
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - original_text: The input text
        - translated_text: Translated text content
        - target_language: Target language code
    
    Examples:
        Translate to English:
            text="Bonjour le monde", to_lang="en"
            Returns: Translated text in English
        
        Translate to Spanish:
            text="Hello world", to_lang="es"
            Returns: Translated text in Spanish
    """
    try:
        safe_log_info(logger, "[webc_translate_text] Starting translation", 
                     text_length=len(text) if text else 0, to_lang=to_lang)
        
        # Validate inputs
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            error_msg = "text must be a non-empty string"
            safe_log_error(logger, "[webc_translate_text] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not isinstance(to_lang, str) or len(to_lang) != 2:
            error_msg = "to_lang must be a 2-character ISO 639-1 language code"
            safe_log_error(logger, "[webc_translate_text] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_translate_text] Translating", to_lang=to_lang)
        
        translated_text = translate_text(text, to_lang=to_lang)
        
        result = {
            "status": "success",
            "original_text": text,
            "translated_text": translated_text,
            "target_language": to_lang
        }
        
        safe_log_info(logger, "[webc_translate_text] Translation complete", 
                     to_lang=to_lang, 
                     original_length=len(text),
                     translated_length=len(translated_text))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        safe_log_error(logger, "[webc_translate_text] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_translate_webpage(
    runtime: ToolRuntime,
    url: str
) -> str:
    """
    Translate a webpage's visible text content to English.
    
    Fetches HTML content, extracts visible text, and translates it to English.
    Only translates visible text (excludes scripts, styles, comments).
    
    When to use:
        - Need to translate a webpage to English for analysis
        - Extract and translate content from foreign language websites
        - Multi-language content processing
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        url: URL of the webpage to translate (must include http:// or https://).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - url: The requested URL
        - translated_text: Translated text content in English
    
    Examples:
        Basic translation:
            url="https://example.com"
            Returns: Webpage text translated to English
        
        Foreign language site:
            url="https://fr.wikipedia.org"
            Returns: French content translated to English
    """
    try:
        safe_log_info(logger, "[webc_translate_webpage] Starting translation", url=url)
        
        # Validate inputs
        if not url or not isinstance(url, str):
            error_msg = "url must be a non-empty string"
            safe_log_error(logger, "[webc_translate_webpage] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            error_msg = "url must start with http:// or https://"
            safe_log_error(logger, "[webc_translate_webpage] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_translate_webpage] Translating webpage", url=url)
        
        translated_text = translate_webpage_to_english(url)
        
        result = {
            "status": "success",
            "url": url,
            "translated_text": translated_text,
            "text_length": len(translated_text) if translated_text else 0
        }
        
        safe_log_info(logger, "[webc_translate_webpage] Translation complete", 
                     url=url, text_length=result["text_length"])
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Webpage translation failed: {str(e)}"
        safe_log_error(logger, "[webc_translate_webpage] Error", 
                     exc_info=True,
                     error=str(e),
                     url=url if 'url' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


# ============================================================================
# TEXT ANALYSIS & ENTITY EXTRACTION TOOLS
# ============================================================================

@tool
def webc_analyze_text(
    runtime: ToolRuntime,
    text: str,
    remove_stopwords: bool = True
) -> str:
    """
    Comprehensive text analysis with full NLP metadata.
    
    Performs comprehensive text analysis including:
    - Language detection and translation
    - Email and phone number extraction
    - Readability statistics (multiple metrics)
    - Named entity extraction
    - Bag of terms (n-grams with entity weighting)
    - Stop word removal (optional)
    
    When to use:
        - Need comprehensive text analysis
        - Extract entities, readability stats, and key terms
        - Analyze text content for intelligence gathering
        - Get full NLP metadata from text
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to analyze.
        remove_stopwords: If True, removes stop words before creating bag of terms.
                         Default: True (faster, cleaner results).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - language: Detected language code
        - text_content: Cleaned text content
        - emails, email_domains: Extracted email addresses
        - phones: Extracted phone numbers
        - entities: Named entities (PERSON, ORG, GPE, etc.)
        - readability_stats: Multiple readability metrics
        - bag_of_terms: Top 25 key terms with scores
    
    Examples:
        Full analysis:
            text="Your text here", remove_stopwords=True
            Returns: Complete NLP analysis with entities, readability, key terms
        
        Quick analysis:
            text="Short text", remove_stopwords=False
            Returns: Analysis without stop word removal
    """
    try:
        safe_log_info(logger, "[webc_analyze_text] Starting analysis", 
                     text_length=len(text) if text else 0, remove_stopwords=remove_stopwords)
        
        # Validate inputs
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            error_msg = "text must be a non-empty string"
            safe_log_error(logger, "[webc_analyze_text] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_analyze_text] Analyzing text")
        
        text_model = get_text_model(text, rm_stopwords=remove_stopwords)
        
        # Extract readability stats
        readability = {}
        if hasattr(text_model, 'readability_stats') and text_model.readability_stats:
            rs = text_model.readability_stats
            readability = {
                "automated_readability_index": rs.automated_readability_index if hasattr(rs, 'automated_readability_index') else None,
                "coleman_liau_index": rs.coleman_liau_index if hasattr(rs, 'coleman_liau_index') else None,
                "flesch_kincaid_grade_level": rs.flesch_kincaid_grade_level if hasattr(rs, 'flesch_kincaid_grade_level') else None,
                "flesch_reading_ease": rs.flesch_reading_ease if hasattr(rs, 'flesch_reading_ease') else None,
                "gunning_fog_index": rs.gunning_fog_index if hasattr(rs, 'gunning_fog_index') else None,
                "smog_index": rs.smog_index if hasattr(rs, 'smog_index') else None
            }
        
        result = {
            "status": "success",
            "language": text_model.language if hasattr(text_model, 'language') else None,
            "text_content": text_model.text_content if hasattr(text_model, 'text_content') else None,
            "emails": list(text_model.emails) if hasattr(text_model, 'emails') and text_model.emails else [],
            "email_domains": list(text_model.email_domains) if hasattr(text_model, 'email_domains') and text_model.email_domains else [],
            "phones": list(text_model.phones) if hasattr(text_model, 'phones') and text_model.phones else [],
            "entities": [
                {"key": e.key, "value": e.value}
                for e in (text_model.entities if hasattr(text_model, 'entities') and text_model.entities else [])
            ],
            "intents": [
                {"key": i.key, "value": i.value}
                for i in (text_model.intents if hasattr(text_model, 'intents') and text_model.intents else [])
            ],
            "readability_stats": readability,
            "bag_of_terms": text_model.bag_of_terms if hasattr(text_model, 'bag_of_terms') and text_model.bag_of_terms else []
        }
        
        safe_log_info(logger, "[webc_analyze_text] Analysis complete", 
                     language=result.get("language"),
                     entities_count=len(result.get("entities", [])),
                     emails_count=len(result.get("emails", [])))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Text analysis failed: {str(e)}"
        safe_log_error(logger, "[webc_analyze_text] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_extract_entities(
    runtime: ToolRuntime,
    text: Optional[str] = None,
    url: Optional[str] = None
) -> str:
    """
    Extract named entities from text or webpage.
    
    Uses spaCy NLP to identify named entities such as persons, organizations,
    locations, dates, etc. Can analyze either provided text or extract text
    from a webpage URL.
    
    When to use:
        - Need to identify people, organizations, locations in text
        - Extract structured information from unstructured text
        - Entity-based content analysis
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to analyze (either text or url must be provided).
        url: URL of webpage to analyze (either text or url must be provided).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - entities: List of entities with key (text) and value (type/label)
        - source: "text" or "url" indicating the source analyzed
    
    Examples:
        Extract from text:
            text="John works at Microsoft in Seattle"
            Returns: Entities: [{"key": "John", "value": "PERSON"}, {"key": "Microsoft", "value": "ORG"}, {"key": "Seattle", "value": "GPE"}]
        
        Extract from webpage:
            url="https://example.com"
            Returns: All named entities found on the webpage
    """
    try:
        safe_log_info(logger, "[webc_extract_entities] Starting extraction", 
                     has_text=bool(text), has_url=bool(url))
        
        # Validate inputs
        if not text and not url:
            error_msg = "Either text or url must be provided"
            safe_log_error(logger, "[webc_extract_entities] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if text and url:
            error_msg = "Provide either text or url, not both"
            safe_log_error(logger, "[webc_extract_entities] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_extract_entities] Extracting entities")
        
        if url:
            if not url.startswith(("http://", "https://")):
                error_msg = "url must start with http:// or https://"
                safe_log_error(logger, "[webc_extract_entities] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            entities = extract_entities_from_webpage(url)
            source = "url"
        else:
            if not isinstance(text, str) or len(text.strip()) == 0:
                error_msg = "text must be a non-empty string"
                safe_log_error(logger, "[webc_extract_entities] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            entities = extract_entities_from_text(text)
            source = "text"
        
        result = {
            "status": "success",
            "entities": [
                {"key": e.key, "value": e.value}
                for e in (entities if entities else [])
            ],
            "source": source
        }
        
        safe_log_info(logger, "[webc_extract_entities] Extraction complete", 
                     entities_count=len(result["entities"]), source=source)
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Entity extraction failed: {str(e)}"
        safe_log_error(logger, "[webc_extract_entities] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_extract_emails(
    runtime: ToolRuntime,
    text: Optional[str] = None,
    url: Optional[str] = None
) -> str:
    """
    Extract email addresses from text or webpage.
    
    Uses regular expressions to find all email addresses and their domains.
    Can analyze either provided text or extract text from a webpage URL.
    
    When to use:
        - Need to find email addresses in content
        - Extract contact information
        - Email harvesting from webpages
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to analyze (either text or url must be provided).
        url: URL of webpage to analyze (either text or url must be provided).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - emails: Set of email addresses found
        - email_domains: Set of email domains (part after @)
        - source: "text" or "url" indicating the source analyzed
    
    Examples:
        Extract from text:
            text="Contact us at info@example.com"
            Returns: emails=["info@example.com"], email_domains=["example.com"]
        
        Extract from webpage:
            url="https://example.com"
            Returns: All email addresses found on the webpage
    """
    try:
        safe_log_info(logger, "[webc_extract_emails] Starting extraction", 
                     has_text=bool(text), has_url=bool(url))
        
        # Validate inputs
        if not text and not url:
            error_msg = "Either text or url must be provided"
            safe_log_error(logger, "[webc_extract_emails] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if text and url:
            error_msg = "Provide either text or url, not both"
            safe_log_error(logger, "[webc_extract_emails] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_extract_emails] Extracting emails")
        
        if url:
            if not url.startswith(("http://", "https://")):
                error_msg = "url must start with http:// or https://"
                safe_log_error(logger, "[webc_extract_emails] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            emails, email_domains = extract_emails_from_webpage(url)
            source = "url"
        else:
            if not isinstance(text, str) or len(text.strip()) == 0:
                error_msg = "text must be a non-empty string"
                safe_log_error(logger, "[webc_extract_emails] Validation failed", error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            emails, email_domains = extract_emails_from_text(text)
            source = "text"
        
        result = {
            "status": "success",
            "emails": list(emails) if emails else [],
            "email_domains": list(email_domains) if email_domains else [],
            "source": source
        }
        
        safe_log_info(logger, "[webc_extract_emails] Extraction complete", 
                     emails_count=len(result["emails"]), 
                     domains_count=len(result["email_domains"]),
                     source=source)
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Email extraction failed: {str(e)}"
        safe_log_error(logger, "[webc_extract_emails] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_find_sensitive_data(
    runtime: ToolRuntime,
    text: str
) -> str:
    """
    Comprehensive sensitive data detection and PII scanning tool for data loss prevention (DLP).
    
    This is a critical security tool that scans text content for all types of sensitive information
    and personally identifiable information (PII). It uses advanced regex patterns and validation
    algorithms to detect various sensitive data types including financial information, personal
    identifiers, contact information, and network addresses. Essential for compliance, security
    audits, and data protection.
    
    What it detects:
        - Phone Numbers: US format (555-123-4567, (555) 123-4567) and international formats
        - Email Addresses: All valid email formats with domain extraction
        - IP Addresses: Both IPv4 (192.168.1.1) and IPv6 (2001:0db8::1) addresses
        - Credit Card Numbers: Validates using Luhn algorithm, detects major card types
        - Bitcoin Addresses: Cryptocurrency wallet addresses (Base58 and Bech32 formats)
        - Street Addresses: US street addresses with street numbers and names
        - ZIP Codes: US ZIP codes (5-digit and ZIP+4 formats)
        - Social Security Numbers: US SSN format (123-45-6789)
        - P.O. Box Addresses: Post office box addresses
        - Strong Passwords: Potential strong passwords (long alphanumeric strings)
        - Twitter Handles: @username format
        - URLs/Links: Web links and URLs
    
    When to use:
        - User asks to "find sensitive data", "detect PII", or "scan for personal information"
        - Performing data loss prevention (DLP) analysis on text content
        - Privacy compliance checks (GDPR, CCPA, HIPAA)
        - Security audits of documents, logs, or data dumps
        - Analyzing leaked data or breach information
        - Pre-processing text before sharing or publishing
        - Detecting accidentally exposed credentials or personal information
    
    When NOT to use:
        - Only need email addresses (use webc_extract_emails instead - faster)
        - Only need IP addresses (use specific IP extraction tools)
        - Text is already known to be clean (unnecessary processing)
        - Need to detect sensitive data in binary files (this tool only works with text)
        - Need real-time scanning of streaming data (this processes complete text)
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to scan for sensitive data. Can be any length, but longer text
            may take more time to process. Examples: document content, log files, emails,
            chat messages, database dumps, etc.
    
    Returns:
        JSON string with status and all detected sensitive data types:
        {
            "status": "success" | "error",
            "us_phones": ["555-123-4567", "(555) 987-6543"],  // US phone numbers
            "us_phones_with_exts": ["555-123-4567 ext 123"],  // With extensions
            "intl_phones": ["+44 20 7946 0958"],  // International formats
            "emails": [
                ["email1@domain.com", "email2@domain.com"],  // Email addresses
                ["domain.com", "example.org"]  // Email domains
            ],
            "ipv4s": ["192.168.1.1", "10.0.0.1"],  // IPv4 addresses
            "ipv6s": ["2001:0db8::1"],  // IPv6 addresses
            "credit_cards": ["4111111111111111"],  // Credit card numbers (validated)
            "btc_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],  // Bitcoin addresses
            "street_addresses": ["123 Main St, Anytown, CA"],  // Street addresses
            "zip_codes": ["12345", "12345-6789"],  // ZIP codes
            "links": ["https://example.com", "http://test.org"],  // URLs
            "ssn_numbers": ["123-45-6789"],  // Social Security Numbers
            "po_boxes": ["PO Box 123"],  // P.O. Box addresses
            "strong_passwords": ["MyP@ssw0rd123!"],  // Potential passwords
            "twitter_handle": ["@username"]  // Twitter handles
        }
        If no sensitive data is found, all arrays will be empty.
    
    Examples:
        Basic scan:
            text="Contact: john@example.com, Phone: 555-1234"
            Returns: emails=["john@example.com"], us_phones=["555-1234"]
        
        Comprehensive scan:
            text="SSN: 123-45-6789, Credit Card: 4111111111111111, Address: 123 Main St"
            Returns: ssn_numbers, credit_cards, street_addresses populated
        
        No sensitive data:
            text="This is a normal paragraph with no sensitive information."
            Returns: All arrays empty, message="No sensitive data found"
    
    Related tools:
        - webc_extract_emails: Faster if you only need email addresses
        - webc_validate_credit_card: Validate and get details about specific credit cards
        - webc_analyze_text: Comprehensive text analysis that may include some sensitive data
    
    Security notes:
        - Credit card numbers are validated using Luhn algorithm
        - SSN format validation (does not verify if SSN is real/active)
        - Phone numbers validated for format, not existence
        - All detections are pattern-based - false positives possible
        - Use results for flagging/review, not as definitive proof
        - Consider redacting or masking detected sensitive data before logging
    
    Performance notes:
        - Processing time: 1-5 seconds depending on text length
        - Very fast for short text (< 1KB)
        - May take longer for large documents (> 100KB)
        - All patterns checked in parallel for efficiency
    """
    try:
        safe_log_info(logger, "[webc_find_sensitive_data] Starting scan", 
                     text_length=len(text) if text else 0)
        
        # Validate inputs
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            error_msg = "text must be a non-empty string"
            safe_log_error(logger, "[webc_find_sensitive_data] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_find_sensitive_data] Scanning for sensitive data")
        
        sensitive_data = find_sensitive_data_in_text(text)
        
        if not sensitive_data:
            result = {
                "status": "success",
                "message": "No sensitive data found",
                "us_phones": [],
                "us_phones_with_exts": [],
                "intl_phones": [],
                "emails": ([], []),
                "ipv4s": [],
                "ipv6s": [],
                "credit_cards": [],
                "btc_addresses": [],
                "street_addresses": [],
                "zip_codes": [],
                "links": [],
                "ssn_numbers": [],
                "po_boxes": [],
                "strong_passwords": [],
                "twitter_handle": []
            }
        else:
            result = {
                "status": "success",
                "us_phones": list(sensitive_data.us_phones) if hasattr(sensitive_data, 'us_phones') and sensitive_data.us_phones else [],
                "us_phones_with_exts": list(sensitive_data.us_phones_with_exts) if hasattr(sensitive_data, 'us_phones_with_exts') and sensitive_data.us_phones_with_exts else [],
                "intl_phones": list(sensitive_data.intl_phones) if hasattr(sensitive_data, 'intl_phones') and sensitive_data.intl_phones else [],
                "emails": (
                    list(sensitive_data.emails[0]) if hasattr(sensitive_data, 'emails') and sensitive_data.emails and len(sensitive_data.emails) > 0 else [],
                    list(sensitive_data.emails[1]) if hasattr(sensitive_data, 'emails') and sensitive_data.emails and len(sensitive_data.emails) > 1 else []
                ),
                "ipv4s": list(sensitive_data.ipv4s) if hasattr(sensitive_data, 'ipv4s') and sensitive_data.ipv4s else [],
                "ipv6s": list(sensitive_data.ipv6s) if hasattr(sensitive_data, 'ipv6s') and sensitive_data.ipv6s else [],
                "credit_cards": list(sensitive_data.credit_cards) if hasattr(sensitive_data, 'credit_cards') and sensitive_data.credit_cards else [],
                "btc_addresses": list(sensitive_data.btc_addresses) if hasattr(sensitive_data, 'btc_addresses') and sensitive_data.btc_addresses else [],
                "street_addresses": list(sensitive_data.street_addresses) if hasattr(sensitive_data, 'street_addresses') and sensitive_data.street_addresses else [],
                "zip_codes": list(sensitive_data.zip_codes) if hasattr(sensitive_data, 'zip_codes') and sensitive_data.zip_codes else [],
                "links": list(sensitive_data.links) if hasattr(sensitive_data, 'links') and sensitive_data.links else [],
                "ssn_numbers": list(sensitive_data.ssn_numbers) if hasattr(sensitive_data, 'ssn_numbers') and sensitive_data.ssn_numbers else [],
                "po_boxes": list(sensitive_data.po_boxes) if hasattr(sensitive_data, 'po_boxes') and sensitive_data.po_boxes else [],
                "strong_passwords": list(sensitive_data.strong_passwords) if hasattr(sensitive_data, 'strong_passwords') and sensitive_data.strong_passwords else [],
                "twitter_handle": list(sensitive_data.twitter_handle) if hasattr(sensitive_data, 'twitter_handle') and sensitive_data.twitter_handle else []
            }
        
        total_findings = (
            len(result["us_phones"]) + len(result["us_phones_with_exts"]) + 
            len(result["intl_phones"]) + len(result["emails"][0]) + 
            len(result["ipv4s"]) + len(result["ipv6s"]) + 
            len(result["credit_cards"]) + len(result["ssn_numbers"])
        )
        
        safe_log_info(logger, "[webc_find_sensitive_data] Scan complete", 
                     total_findings=total_findings)
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Sensitive data detection failed: {str(e)}"
        safe_log_error(logger, "[webc_find_sensitive_data] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


# ============================================================================
# DOMAIN & IP ANALYSIS TOOLS
# ============================================================================

@tool
def webc_analyze_domain(
    runtime: ToolRuntime,
    url: str
) -> str:
    """
    Comprehensive domain analysis with DNS, geolocation, and WHOIS.
    
    Extracts domain information and enriches it with:
    - Domain components (subdomain, domain, TLD, etc.)
    - IP addresses for both FQDN and registered domain
    - Geolocation data for all IPs
    - WHOIS registration information
    
    When to use:
        - Need comprehensive domain intelligence
        - Analyze domain infrastructure
        - Get IP locations and WHOIS data
        - Domain reconnaissance
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        url: URL or domain string to analyze.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - url: The analyzed URL
        - fqdn, domain, registered_domain, subdomain, suffix: Domain components
        - ip_locations: IP addresses with geolocation data
        - ip_locations_fqdn: IP addresses for FQDN with geolocation
        - whois: Domain registration information
    
    Examples:
        Analyze from URL:
            url="https://example.com"
            Returns: Complete domain analysis with IPs, geolocation, WHOIS
        
        Analyze from domain string:
            url="example.com"
            Returns: Same analysis (protocol not required)
    """
    try:
        safe_log_info(logger, "[webc_analyze_domain] Starting analysis", url=url)
        
        # Validate inputs
        if not url or not isinstance(url, str):
            error_msg = "url must be a non-empty string"
            safe_log_error(logger, "[webc_analyze_domain] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        url = url.strip()
        
        safe_log_debug(logger, "[webc_analyze_domain] Analyzing domain", url=url)
        
        domain_model = get_domain_model(url)
        
        # Convert IP locations to dictionaries
        def ip_location_to_dict(loc):
            if not loc:
                return None
            result = {
                "ip": loc.ip if hasattr(loc, 'ip') else None
            }
            if hasattr(loc, 'location') and loc.location:
                result["location"] = {
                    "city": loc.location.city if hasattr(loc.location, 'city') else None,
                    "country": loc.location.country if hasattr(loc.location, 'country') else None,
                    "latitude": loc.location.latitude if hasattr(loc.location, 'latitude') else None,
                    "longitude": loc.location.longitude if hasattr(loc.location, 'longitude') else None,
                }
            if hasattr(loc, 'ipwhois') and loc.ipwhois:
                result["ipwhois"] = str(loc.ipwhois)
            return result
        
        result = {
            "status": "success",
            "url": domain_model.url if hasattr(domain_model, 'url') else url,
            "fqdn": domain_model.fqdn if hasattr(domain_model, 'fqdn') else None,
            "domain": domain_model.domain if hasattr(domain_model, 'domain') else None,
            "registered_domain": domain_model.registered_domain if hasattr(domain_model, 'registered_domain') else None,
            "subdomain": domain_model.subdomain if hasattr(domain_model, 'subdomain') else None,
            "suffix": domain_model.suffix if hasattr(domain_model, 'suffix') else None,
            "ip_locations": [
                ip_location_to_dict(loc)
                for loc in (domain_model.ip_locations if hasattr(domain_model, 'ip_locations') and domain_model.ip_locations else [])
            ],
            "ip_locations_fqdn": [
                ip_location_to_dict(loc)
                for loc in (domain_model.ip_locations_fqdn if hasattr(domain_model, 'ip_locations_fqdn') and domain_model.ip_locations_fqdn else [])
            ],
            "whois": str(domain_model.whois) if hasattr(domain_model, 'whois') and domain_model.whois else None
        }
        
        safe_log_info(logger, "[webc_analyze_domain] Analysis complete", 
                     url=url,
                     domain=result.get("domain"),
                     ip_count=len(result.get("ip_locations", [])))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Domain analysis failed: {str(e)}"
        safe_log_error(logger, "[webc_analyze_domain] Error", 
                     exc_info=True,
                     error=str(e),
                     url=url if 'url' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_resolve_domain_ips(
    runtime: ToolRuntime,
    domain_name: str
) -> str:
    """
    Resolve a domain name to its IP addresses using DNS.
    
    Performs a DNS A record lookup to get all IPv4 addresses associated
    with the domain name.
    
    When to use:
        - Need to resolve domain to IP addresses
        - Get all IPs for a domain (load balancing, CDN, etc.)
        - DNS reconnaissance
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        domain_name: Domain name to resolve (e.g., 'example.com').
                    Should not include protocol (http://) or path.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - domain_name: The resolved domain
        - ip_addresses: List of IP address strings
    
    Examples:
        Basic DNS resolution:
            domain_name="example.com"
            Returns: ip_addresses=["93.184.216.34"] (example IP)
        
        Multiple IPs (load balancing):
            domain_name="google.com"
            Returns: ip_addresses=["142.250.191.14", "2607:f8b0:4004:c1b::71"] (multiple IPs)
    """
    try:
        safe_log_info(logger, "[webc_resolve_domain_ips] Starting resolution", domain_name=domain_name)
        
        # Validate inputs
        if not domain_name or not isinstance(domain_name, str) or len(domain_name.strip()) == 0:
            error_msg = "domain_name must be a non-empty string"
            safe_log_error(logger, "[webc_resolve_domain_ips] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        domain_name = domain_name.strip()
        
        safe_log_debug(logger, "[webc_resolve_domain_ips] Resolving DNS", domain_name=domain_name)
        
        ip_addresses = resolve_domain_ips(domain_name)
        
        result = {
            "status": "success",
            "domain_name": domain_name,
            "ip_addresses": ip_addresses if ip_addresses else []
        }
        
        safe_log_info(logger, "[webc_resolve_domain_ips] Resolution complete", 
                     domain_name=domain_name,
                     ip_count=len(result["ip_addresses"]))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"DNS resolution failed: {str(e)}"
        safe_log_error(logger, "[webc_resolve_domain_ips] Error", 
                     exc_info=True,
                     error=str(e),
                     domain_name=domain_name if 'domain_name' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_get_domain_whois(
    runtime: ToolRuntime,
    domain_name: str
) -> str:
    """
    Perform WHOIS lookup for a domain name.
    
    Queries WHOIS databases to retrieve domain registration information
    including registrar, creation date, expiration date, name servers, etc.
    
    When to use:
        - Need domain registration information
        - Check domain ownership and registration details
        - Domain intelligence gathering
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        domain_name: Domain name to query (e.g., 'example.com').
                    Should not include protocol or path.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - domain_name: The queried domain
        - whois: WHOIS/RDAP information object (serialized as JSON dict)
    
    Examples:
        Basic WHOIS lookup:
            domain_name="example.com"
            Returns: Registration details, registrar, creation/expiration dates
        
        Check domain ownership:
            domain_name="target-domain.com"
            Returns: Owner information, name servers, registration dates
    """
    try:
        safe_log_info(logger, "[webc_get_domain_whois] Starting lookup", domain_name=domain_name)
        
        # Validate inputs
        if not domain_name or not isinstance(domain_name, str) or len(domain_name.strip()) == 0:
            error_msg = "domain_name must be a non-empty string"
            safe_log_error(logger, "[webc_get_domain_whois] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        domain_name = domain_name.strip()
        
        safe_log_debug(logger, "[webc_get_domain_whois] Querying WHOIS", domain_name=domain_name)
        
        whois_data = get_domain_whois(domain_name)
        
        result = {
            "status": "success",
            "domain_name": domain_name,
            "whois": _serialize_domain_whois(whois_data),
            "message": None if whois_data else (
                "WHOIS data not available. This can happen if the WHOIS lookup failed (e.g., "
                "network/port-43 restrictions or rate limiting) or if the registry returns limited data. "
                "Check logs for detailed error diagnostics."
            ),
        }
        
        safe_log_info(logger, "[webc_get_domain_whois] Lookup complete", 
                     domain_name=domain_name,
                     has_whois=bool(whois_data))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"WHOIS lookup failed: {str(e)}"
        safe_log_error(logger, "[webc_get_domain_whois] Error", 
                     exc_info=True,
                     error=str(e),
                     domain_name=domain_name if 'domain_name' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_get_ip_location(
    runtime: ToolRuntime,
    ip: str
) -> str:
    """
    Get geolocation information for an IP address.
    
    Retrieves geolocation data (city, country, coordinates, etc.) for an
    IP address using multiple geolocation services with fallback.
    
    When to use:
        - Need to geolocate an IP address
        - Get location information for network analysis
        - IP intelligence gathering
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        ip: IP address (IPv4 or IPv6) to get geolocation for.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - ip: The queried IP address
        - location: Geolocation data (city, country, coordinates, timezone)
    
    Examples:
        IPv4 geolocation:
            ip="8.8.8.8"
            Returns: location with city="Mountain View", country="United States", coordinates
    
        IPv6 geolocation:
            ip="2001:4860:4860::8888"
            Returns: Location data for IPv6 address
    """
    try:
        safe_log_info(logger, "[webc_get_ip_location] Starting lookup", ip=ip)
        
        # Validate inputs
        if not ip or not isinstance(ip, str) or len(ip.strip()) == 0:
            error_msg = "ip must be a non-empty string"
            safe_log_error(logger, "[webc_get_ip_location] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        ip = ip.strip()
        
        safe_log_debug(logger, "[webc_get_ip_location] Getting location", ip=ip)
        
        location = get_ip_location(ip)
        
        if not location:
            result = {
                "status": "success",
                "ip": ip,
                "location": None,
                "message": "Location data not available for this IP"
            }
        else:
            result = {
                "status": "success",
                "ip": ip,
                "location": {
                    "city": location.city if hasattr(location, 'city') else None,
                    "region": location.region if hasattr(location, 'region') else None,
                    "country": location.country if hasattr(location, 'country') else None,
                    "latitude": location.latitude if hasattr(location, 'latitude') else None,
                    "longitude": location.longitude if hasattr(location, 'longitude') else None,
                    "timezone": location.timezone if hasattr(location, 'timezone') else None
                }
            }
        
        safe_log_info(logger, "[webc_get_ip_location] Lookup complete", 
                     ip=ip,
                     has_location=bool(location))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"IP location lookup failed: {str(e)}"
        safe_log_error(logger, "[webc_get_ip_location] Error", 
                     exc_info=True,
                     error=str(e),
                     ip=ip if 'ip' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_get_ip_whois(
    runtime: ToolRuntime,
    ip: str
) -> str:
    """
    Perform IP WHOIS (RDAP) lookup for an IP address.
    
    Queries RDAP (Registration Data Access Protocol) databases to retrieve
    information about an IP address including ASN, organization, network
    information, and contact details.
    
    When to use:
        - Need IP ownership and network information
        - Get ASN and organization data for an IP
        - IP intelligence gathering
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        ip: IP address to query (IPv4 or IPv6).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - ip: The queried IP address
        - ipwhois: RDAP lookup results (ASN, organization, network info)
    
    Examples:
        IPv4 WHOIS:
            ip="8.8.8.8"
            Returns: ASN, organization="Google LLC", network information
        
        IPv6 WHOIS:
            ip="2001:4860:4860::8888"
            Returns: IPv6 network and ASN information
    """
    try:
        safe_log_info(logger, "[webc_get_ip_whois] Starting lookup", ip=ip)
        
        # Validate inputs
        if not ip or not isinstance(ip, str) or len(ip.strip()) == 0:
            error_msg = "ip must be a non-empty string"
            safe_log_error(logger, "[webc_get_ip_whois] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        ip = ip.strip()
        
        safe_log_debug(logger, "[webc_get_ip_whois] Querying RDAP", ip=ip)
        
        ipwhois_data = get_ip_whois(ip)
        
        result = {
            "status": "success",
            "ip": ip,
            "ipwhois": str(ipwhois_data) if ipwhois_data else None
        }
        
        safe_log_info(logger, "[webc_get_ip_whois] Lookup complete", 
                     ip=ip,
                     has_ipwhois=bool(ipwhois_data))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"IP WHOIS lookup failed: {str(e)}"
        safe_log_error(logger, "[webc_get_ip_whois] Error", 
                     exc_info=True,
                     error=str(e),
                     ip=ip if 'ip' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_get_certificate_info(
    runtime: ToolRuntime,
    hostname: str
) -> str:
    """
    Retrieve SSL/TLS certificate information for a hostname.
    
    Connects to the hostname on port 443 (HTTPS) and retrieves the
    SSL/TLS certificate details including issuer, validity dates,
    subject, and other certificate metadata.
    
    When to use:
        - Need SSL/TLS certificate information
        - Check certificate validity and issuer
        - Certificate intelligence gathering
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        hostname: Hostname or domain name to get certificate for.
                 Should not include protocol or port.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - hostname: The queried hostname
        - certificate: Certificate information (issuer, subject, validity, etc.)
    
    Examples:
        Get SSL certificate:
            hostname="example.com"
            Returns: Certificate details including issuer, validity dates, subject
        
        Invalid hostname:
            hostname="nonexistent-domain-12345.com"
            Returns: Error message if certificate cannot be retrieved
    """
    try:
        safe_log_info(logger, "[webc_get_certificate_info] Starting lookup", hostname=hostname)
        
        # Validate inputs
        if not hostname or not isinstance(hostname, str) or len(hostname.strip()) == 0:
            error_msg = "hostname must be a non-empty string"
            safe_log_error(logger, "[webc_get_certificate_info] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        hostname = hostname.strip()
        
        safe_log_debug(logger, "[webc_get_certificate_info] Retrieving certificate", hostname=hostname)
        
        cert_info = get_certificate_info_for_hostname(hostname)
        
        if isinstance(cert_info, str):
            # Error message returned as string
            result = {
                "status": "error",
                "hostname": hostname,
                "message": cert_info
            }
        else:
            result = {
                "status": "success",
                "hostname": hostname,
                "certificate": str(cert_info) if cert_info else None
            }
        
        safe_log_info(logger, "[webc_get_certificate_info] Lookup complete", 
                     hostname=hostname,
                     has_certificate=bool(cert_info) and not isinstance(cert_info, str))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Certificate lookup failed: {str(e)}"
        safe_log_error(logger, "[webc_get_certificate_info] Error", 
                     exc_info=True,
                     error=str(e),
                     hostname=hostname if 'hostname' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


# ============================================================================
# TEXT SIMILARITY & KEY TERMS TOOLS
# ============================================================================

@tool
def webc_calculate_text_similarity(
    runtime: ToolRuntime,
    text1: str,
    text2: str
) -> str:
    """
    Calculate comprehensive text similarity metrics between two texts.
    
    Computes multiple similarity measures using various algorithms:
    - Semantic similarity (spaCy word vectors)
    - Cosine similarity
    - Bag-of-words similarity
    - Character n-gram similarity
    - Jaccard similarity
    - Levenshtein distance
    - Jaro similarity
    - And more...
    
    When to use:
        - Need to compare two texts for similarity
        - Detect duplicate or similar content
        - Measure text similarity across multiple dimensions
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text1: First text document to compare.
        text2: Second text document to compare.
    
    Returns:
        JSON string containing:
        - status: "success" | "error"
        - similarities: Dictionary with all similarity metrics and scores:
            {
                "spacy": 0.85,  // Semantic similarity
                "cosine": 0.72,  // Cosine similarity
                "jaccard": 0.60,  // Jaccard similarity
                "levenshtein": 0.75,  // Edit distance similarity
                // ... more metrics
            }
    
    Examples:
        Similar texts:
            text1="Hello world", text2="Hello there"
            Returns: High similarity scores across multiple metrics
        
        Different texts:
            text1="Python programming", text2="Cooking recipes"
            Returns: Low similarity scores
    """
    try:
        safe_log_info(logger, "[webc_calculate_text_similarity] Starting calculation", 
                     text1_length=len(text1) if text1 else 0,
                     text2_length=len(text2) if text2 else 0)
        
        # Validate inputs
        if not text1 or not isinstance(text1, str) or len(text1.strip()) == 0:
            error_msg = "text1 must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_text_similarity] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not text2 or not isinstance(text2, str) or len(text2.strip()) == 0:
            error_msg = "text2 must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_text_similarity] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_calculate_text_similarity] Calculating similarities")
        
        similarities = calculate_similarity_all(text1, text2)
        
        result = {
            "status": "success",
            "similarities": {
                "spacy": similarities.spacy if hasattr(similarities, 'spacy') else None,
                "cosine": similarities.cosine if hasattr(similarities, 'cosine') else None,
                "bag": similarities.bag if hasattr(similarities, 'bag') else None,
                "character_ngrams": similarities.character_ngrams if hasattr(similarities, 'character_ngrams') else None,
                "jaccard": similarities.jaccard if hasattr(similarities, 'jaccard') else None,
                "levenshtein": similarities.levenshtein if hasattr(similarities, 'levenshtein') else None,
                "jaro": similarities.jaro if hasattr(similarities, 'jaro') else None,
                "sorensen_dice": similarities.sorensen_dice if hasattr(similarities, 'sorensen_dice') else None
            }
        }
        
        safe_log_info(logger, "[webc_calculate_text_similarity] Calculation complete")
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Similarity calculation failed: {str(e)}"
        safe_log_error(logger, "[webc_calculate_text_similarity] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_extract_keyterms(
    runtime: ToolRuntime,
    text: str,
    topn: int = 10,
    normalize: str = "lemma"
) -> str:
    """
    Extract key terms from text using multiple algorithms.
    
    Applies four different key term extraction algorithms:
    - TextRank: Graph-based ranking algorithm
    - SCAKE: Single-word and compound keyphrase extraction
    - SGRank: Statistical keyphrase extraction
    - YAKE: Yet Another Keyword Extractor (unsupervised)
    
    When to use:
        - Need to identify important terms in text
        - Extract keywords and key phrases
        - Generate tags or topics from content
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to extract key terms from.
        topn: Number of top key terms to return from each algorithm (default: 10).
        normalize: Normalization method - "lemma", "lower", or "none" (default: "lemma").
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - keyterms: Dictionary with results from all four algorithms:
            {
                "textrank": [("term1", 0.95), ("term2", 0.87)],
                "scake": [("term1", 0.92), ("term3", 0.85)],
                "sgrank": [("term2", 0.89), ("term1", 0.83)],
                "yake": [("term1", 0.91), ("term4", 0.78)]
            }
    
    Examples:
        Extract top 10 key terms:
            text="Your text here", topn=10, normalize="lemma"
            Returns: Top 10 terms from each algorithm
        
        Extract with different normalization:
            text="Your text here", topn=5, normalize="lower"
            Returns: Terms normalized to lowercase
    """
    try:
        safe_log_info(logger, "[webc_extract_keyterms] Starting extraction", 
                     text_length=len(text) if text else 0, topn=topn, normalize=normalize)
        
        # Validate inputs
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            error_msg = "text must be a non-empty string"
            safe_log_error(logger, "[webc_extract_keyterms] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if topn < 1 or topn > 100:
            error_msg = "topn must be between 1 and 100"
            safe_log_error(logger, "[webc_extract_keyterms] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if normalize not in ["lemma", "lower", "none"]:
            error_msg = "normalize must be one of: 'lemma', 'lower', 'none'"
            safe_log_error(logger, "[webc_extract_keyterms] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_extract_keyterms] Extracting keyterms", topn=topn, normalize=normalize)
        
        keyterms = extract_keyterms_all(text, topn=topn, normalize=normalize)
        
        result = {
            "status": "success",
            "keyterms": {
                "textrank": keyterms.textrank if hasattr(keyterms, 'textrank') and keyterms.textrank else [],
                "scake": keyterms.scake if hasattr(keyterms, 'scake') and keyterms.scake else [],
                "sgrank": keyterms.sgrank if hasattr(keyterms, 'sgrank') and keyterms.sgrank else [],
                "yake": keyterms.yake if hasattr(keyterms, 'yake') and keyterms.yake else []
            }
        }
        
        safe_log_info(logger, "[webc_extract_keyterms] Extraction complete", 
                     topn=topn)
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Key term extraction failed: {str(e)}"
        safe_log_error(logger, "[webc_extract_keyterms] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_get_readability_stats(
    runtime: ToolRuntime,
    text: str
) -> str:
    """
    Calculate comprehensive readability statistics for text.
    
    Computes multiple readability metrics to assess text complexity:
    - Automated Readability Index (ARI)
    - Coleman-Liau Index
    - Flesch-Kincaid Grade Level
    - Flesch Reading Ease
    - Gunning Fog Index
    - SMOG Index
    - And more...
    
    When to use:
        - Need to assess text readability and complexity
        - Determine reading level required
        - Analyze text difficulty
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to analyze for readability.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - readability_stats: Dictionary with all readability metrics:
            {
                "flesch_reading_ease": 65.5,  // 0-100, higher = easier
                "flesch_kincaid_grade_level": 8.2,  // US grade level
                "gunning_fog_index": 12.3,  // Years of education needed
                // ... more metrics
            }
    
    Examples:
        Analyze article readability:
            text="Your text here"
            Returns: Multiple readability scores indicating text complexity
        
        Check if text is appropriate for audience:
            text="Complex technical documentation"
            Returns: High grade level scores indicating advanced reading level
    """
    try:
        safe_log_info(logger, "[webc_get_readability_stats] Starting calculation", 
                     text_length=len(text) if text else 0)
        
        # Validate inputs
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            error_msg = "text must be a non-empty string"
            safe_log_error(logger, "[webc_get_readability_stats] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_get_readability_stats] Calculating readability")
        
        readability_stats = get_readability_statistics(text)
        
        result = {
            "status": "success",
            "readability_stats": {
                "automated_readability_index": readability_stats.automated_readability_index if hasattr(readability_stats, 'automated_readability_index') else None,
                "coleman_liau_index": readability_stats.coleman_liau_index if hasattr(readability_stats, 'coleman_liau_index') else None,
                "flesch_kincaid_grade_level": readability_stats.flesch_kincaid_grade_level if hasattr(readability_stats, 'flesch_kincaid_grade_level') else None,
                "flesch_reading_ease": readability_stats.flesch_reading_ease if hasattr(readability_stats, 'flesch_reading_ease') else None,
                "gunning_fog_index": readability_stats.gunning_fog_index if hasattr(readability_stats, 'gunning_fog_index') else None,
                "smog_index": readability_stats.smog_index if hasattr(readability_stats, 'smog_index') else None
            }
        }
        
        safe_log_info(logger, "[webc_get_readability_stats] Calculation complete")
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Readability calculation failed: {str(e)}"
        safe_log_error(logger, "[webc_get_readability_stats] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


# ============================================================================
# NETWORK & SERVICE ANALYSIS TOOLS
# ============================================================================

@tool
def webc_scan_service(
    runtime: ToolRuntime,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url: Optional[str] = None,
    https: Optional[bool] = None
) -> str:
    """
    Scan a network service port.
    
    Performs a network port scan on the specified host and port, optionally
    using HTTPS/SSL connection. Can extract host/port from URL if provided.
    
    When to use:
        - Need to check if a port is open
        - Test service availability
        - Network reconnaissance
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        host: Host or IP address to scan. If url is provided, host is extracted from URL.
        port: Port number to scan. If url is provided, port is extracted from URL.
              Defaults to 80 for HTTP, 443 for HTTPS.
        url: Full URL to scan. If provided, host and port are extracted from the URL.
        https: Whether to use HTTPS/SSL connection. If None, determined automatically
               from port (443 = True, 80 = False).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - host: The host or IP address that was scanned
        - port: The port number that was scanned
        - state: The state of the port ("open" or "closed")
        - durations: Timing information for connection operations
    
    Examples:
        Scan using host and port:
            host="example.com", port=443, https=True
            Returns: Port state (open/closed), connection timing
        
        Scan using URL:
            url="https://example.com"
            Returns: Extracts host/port from URL and scans
    """
    try:
        safe_log_info(logger, "[webc_scan_service] Starting scan", 
                     host=host, port=port, url=url, https=https)
        
        # Validate inputs
        if not host and not url:
            error_msg = "Either host or url must be provided"
            safe_log_error(logger, "[webc_scan_service] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_scan_service] Scanning service")
        
        scan_result = scan_service(host=host, port=port, url=url, https=https)
        
        if not scan_result:
            result = {
                "status": "error",
                "message": "Service scan failed or returned no results"
            }
        else:
            result = {
                "status": "success",
                "host": scan_result.get("host") if isinstance(scan_result, dict) else (scan_result.host if hasattr(scan_result, 'host') else None),
                "port": scan_result.get("port") if isinstance(scan_result, dict) else (scan_result.port if hasattr(scan_result, 'port') else None),
                "state": scan_result.get("state") if isinstance(scan_result, dict) else (scan_result.state if hasattr(scan_result, 'state') else None),
                "durations": scan_result.get("durations") if isinstance(scan_result, dict) else (str(scan_result.durations) if hasattr(scan_result, 'durations') else None)
            }
        
        safe_log_info(logger, "[webc_scan_service] Scan complete", 
                     host=result.get("host"),
                     port=result.get("port"),
                     state=result.get("state"))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Service scan failed: {str(e)}"
        safe_log_error(logger, "[webc_scan_service] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_ping_service(
    runtime: ToolRuntime,
    host: Optional[str] = None,
    port: Optional[int] = None,
    url: Optional[str] = None,
    https: Optional[bool] = None
) -> str:
    """
    Ping a network service.
    
    Performs a network ping to the specified host and port, optionally
    using HTTPS/SSL connection. Can extract host/port from URL if provided.
    
    When to use:
        - Need to test service connectivity
        - Check if a service is responding
        - Measure response time
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        host: Host or IP address to ping. If url is provided, host is extracted from URL.
        port: Port number to ping. If url is provided, port is extracted from URL.
              Defaults to 80 for HTTP, 443 for HTTPS.
        url: Full URL to ping. If provided, host and port are extracted from the URL.
        https: Whether to use HTTPS/SSL connection. If None, determined automatically
               from port (443 = True, 80 = False).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - host: The host or IP address that was pinged
        - port: The port number that was pinged
        - response: Ping response object with connection status and timing
    
    Examples:
        Ping using host and port:
            host="example.com", port=443, https=True
            Returns: Connection status and response time
        
        Ping using URL:
            url="https://example.com"
            Returns: Extracts host/port from URL and pings
    """
    try:
        safe_log_info(logger, "[webc_ping_service] Starting ping", 
                     host=host, port=port, url=url, https=https)
        
        # Validate inputs
        if not host and not url:
            error_msg = "Either host or url must be provided"
            safe_log_error(logger, "[webc_ping_service] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_ping_service] Pinging service")
        
        ping_result = ping_service(host=host, port=port, url=url, https=https)
        
        if not ping_result:
            result = {
                "status": "error",
                "message": "Service ping failed or returned no results"
            }
        else:
            result = {
                "status": "success",
                "host": ping_result.host if hasattr(ping_result, 'host') else None,
                "port": ping_result.port if hasattr(ping_result, 'port') else None,
                "response": str(ping_result) if ping_result else None
            }
        
        safe_log_info(logger, "[webc_ping_service] Ping complete", 
                     host=result.get("host"),
                     port=result.get("port"))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Service ping failed: {str(e)}"
        safe_log_error(logger, "[webc_ping_service] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


# ============================================================================
# GEOGRAPHIC ANALYSIS TOOLS
# ============================================================================

@tool
def webc_calculate_geo_distance(
    runtime: ToolRuntime,
    source_lat: float,
    source_long: float,
    dest_lat: float,
    dest_long: float,
    scale: Optional[str] = None
) -> str:
    """
    Calculate geographic distance between two sets of coordinates.
    
    Calculates the distance between two geographic points using their
    latitude and longitude coordinates.
    
    When to use:
        - Need to calculate distance between two locations
        - Geographic analysis
        - Location-based intelligence
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        source_lat: Latitude of the source location.
        source_long: Longitude of the source location.
        dest_lat: Latitude of the destination location.
        dest_long: Longitude of the destination location.
        scale: Distance scale - "metric" (km) or "imperial" (miles).
              If None, defaults to metric (kilometers).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - distance: Distance value
        - unit: Distance unit ("km" or "mi")
        - source_coordinates: Source lat/long
        - dest_coordinates: Destination lat/long
    
    Examples:
        Calculate distance between cities:
            source_lat=37.7749, source_long=-122.4194, dest_lat=40.7128, dest_long=-74.0060
            Returns: Distance between San Francisco and New York (~4135 km)
        
        Metric vs Imperial:
            scale="metric"  // Returns distance in kilometers
            scale="imperial"  // Returns distance in miles
    """
    try:
        safe_log_info(logger, "[webc_calculate_geo_distance] Starting calculation", 
                     source_lat=source_lat, source_long=source_long,
                     dest_lat=dest_lat, dest_long=dest_long, scale=scale)
        
        # Validate inputs
        if not isinstance(source_lat, (int, float)) or not isinstance(source_long, (int, float)):
            error_msg = "source_lat and source_long must be numbers"
            safe_log_error(logger, "[webc_calculate_geo_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not isinstance(dest_lat, (int, float)) or not isinstance(dest_long, (int, float)):
            error_msg = "dest_lat and dest_long must be numbers"
            safe_log_error(logger, "[webc_calculate_geo_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if abs(source_lat) > 90 or abs(dest_lat) > 90:
            error_msg = "Latitude must be between -90 and 90"
            safe_log_error(logger, "[webc_calculate_geo_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if abs(source_long) > 180 or abs(dest_long) > 180:
            error_msg = "Longitude must be between -180 and 180"
            safe_log_error(logger, "[webc_calculate_geo_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_calculate_geo_distance] Calculating distance")
        
        distance_result = calculate_geo_distance(
            source_lat, source_long, dest_lat, dest_long, scale=scale
        )
        
        result = {
            "status": "success",
            "distance": distance_result.get("distance") if isinstance(distance_result, dict) else None,
            "unit": distance_result.get("unit") if isinstance(distance_result, dict) else None,
            "source_coordinates": {"lat": source_lat, "long": source_long},
            "dest_coordinates": {"lat": dest_lat, "long": dest_long}
        }
        
        safe_log_info(logger, "[webc_calculate_geo_distance] Calculation complete", 
                     distance=result.get("distance"),
                     unit=result.get("unit"))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Geographic distance calculation failed: {str(e)}"
        safe_log_error(logger, "[webc_calculate_geo_distance] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_calculate_geoip_distance(
    runtime: ToolRuntime,
    source_ip: str,
    dest_ip: str,
    scale: Optional[str] = None
) -> str:
    """
    Calculate geographic distance between two IP addresses.
    
    Calculates the geographic distance between two IP addresses using
    geolocation data from GeoIP databases.
    
    When to use:
        - Need to calculate distance between two IP addresses
        - Geographic analysis of network traffic
        - IP-based location intelligence
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        source_ip: Source IP address (IPv4 or IPv6).
        dest_ip: Destination IP address (IPv4 or IPv6).
        scale: Distance scale - "metric" (km) or "imperial" (miles).
              If None, defaults to metric (kilometers).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - source_ip: Source IP address
        - dest_ip: Destination IP address
        - distance: Distance value
        - unit: Distance unit ("km" or "mi")
        - source_location: Source IP location data
        - dest_location: Destination IP location data
    
    Examples:
        Calculate distance between IPs:
            source_ip="8.8.8.8", dest_ip="1.1.1.1"
            Returns: Geographic distance between Google DNS and Cloudflare DNS
        
        With scale:
            source_ip="8.8.8.8", dest_ip="1.1.1.1", scale="imperial"
            Returns: Distance in miles instead of kilometers
    """
    try:
        safe_log_info(logger, "[webc_calculate_geoip_distance] Starting calculation", 
                     source_ip=source_ip, dest_ip=dest_ip, scale=scale)
        
        # Validate inputs
        if not source_ip or not isinstance(source_ip, str) or len(source_ip.strip()) == 0:
            error_msg = "source_ip must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_geoip_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not dest_ip or not isinstance(dest_ip, str) or len(dest_ip.strip()) == 0:
            error_msg = "dest_ip must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_geoip_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_calculate_geoip_distance] Calculating distance")
        
        geo_distance = calculate_geoip_distance(source_ip, dest_ip, scale=scale)
        
        result = {
            "status": "success",
            "source_ip": geo_distance.source_ip if hasattr(geo_distance, 'source_ip') else source_ip,
            "dest_ip": geo_distance.dest_ip if hasattr(geo_distance, 'dest_ip') else dest_ip,
            "distance": geo_distance.distance if hasattr(geo_distance, 'distance') else None,
            "unit": geo_distance.unit if hasattr(geo_distance, 'unit') else None,
            "source_location": {
                "latitude": geo_distance.source_location.latitude if hasattr(geo_distance, 'source_location') and geo_distance.source_location and hasattr(geo_distance.source_location, 'latitude') else None,
                "longitude": geo_distance.source_location.longitude if hasattr(geo_distance, 'source_location') and geo_distance.source_location and hasattr(geo_distance.source_location, 'longitude') else None
            } if hasattr(geo_distance, 'source_location') and geo_distance.source_location else None,
            "dest_location": {
                "latitude": geo_distance.dest_location.latitude if hasattr(geo_distance, 'dest_location') and geo_distance.dest_location and hasattr(geo_distance.dest_location, 'latitude') else None,
                "longitude": geo_distance.dest_location.longitude if hasattr(geo_distance, 'dest_location') and geo_distance.dest_location and hasattr(geo_distance.dest_location, 'longitude') else None
            } if hasattr(geo_distance, 'dest_location') and geo_distance.dest_location else None
        }
        
        safe_log_info(logger, "[webc_calculate_geoip_distance] Calculation complete", 
                     distance=result.get("distance"),
                     unit=result.get("unit"))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"GeoIP distance calculation failed: {str(e)}"
        safe_log_error(logger, "[webc_calculate_geoip_distance] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_calculate_geodomain_distance(
    runtime: ToolRuntime,
    source_domain: str,
    dest_domain: str,
    scale: Optional[str] = None
) -> str:
    """
    Calculate geographic distance between two domains.
    
    Resolves both domains to their IP addresses, then calculates the
    geographic distance between all IP pairs using geolocation data.
    
    When to use:
        - Need to calculate distance between two domains
        - Geographic analysis of domain infrastructure
        - Multi-IP domain distance analysis
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        source_domain: Source domain name to resolve and calculate distance from.
        dest_domain: Destination domain name to resolve and calculate distance to.
        scale: Distance scale - "metric" (km) or "imperial" (miles).
              If None, defaults to metric (kilometers).
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - source_domain: Source domain name
        - dest_domain: Destination domain name
        - distances: List of distance objects for each IP pair combination
    
    Examples:
        Calculate distance between domains:
            source_domain="example.com", dest_domain="google.com"
            Returns: Distances for all IP pairs (if domains have multiple IPs)
        
        Single IP per domain:
            source_domain="small-site.com", dest_domain="another-site.com"
            Returns: Single distance object for the IP pair
    """
    try:
        safe_log_info(logger, "[webc_calculate_geodomain_distance] Starting calculation", 
                     source_domain=source_domain, dest_domain=dest_domain, scale=scale)
        
        # Validate inputs
        if not source_domain or not isinstance(source_domain, str) or len(source_domain.strip()) == 0:
            error_msg = "source_domain must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_geodomain_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not dest_domain or not isinstance(dest_domain, str) or len(dest_domain.strip()) == 0:
            error_msg = "dest_domain must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_geodomain_distance] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_calculate_geodomain_distance] Calculating distances")
        
        distances = calculate_geodomain_distance(source_domain, dest_domain, scale=scale)
        
        result = {
            "status": "success",
            "source_domain": source_domain,
            "dest_domain": dest_domain,
            "distances": [
                {
                    "source_ip": d.source_ip if hasattr(d, 'source_ip') else None,
                    "dest_ip": d.dest_ip if hasattr(d, 'dest_ip') else None,
                    "distance": d.distance if hasattr(d, 'distance') else None,
                    "unit": d.unit if hasattr(d, 'unit') else None
                }
                for d in (distances if distances else [])
            ]
        }
        
        safe_log_info(logger, "[webc_calculate_geodomain_distance] Calculation complete", 
                     distances_count=len(result["distances"]))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Geodomain distance calculation failed: {str(e)}"
        safe_log_error(logger, "[webc_calculate_geodomain_distance] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


# ============================================================================
# ADDITIONAL UTILITY TOOLS
# ============================================================================

@tool
def webc_get_domain_tld_info(
    runtime: ToolRuntime,
    url: str
) -> str:
    """
    Extract domain TLD information from a URL.
    
    Parses the URL to extract domain components and returns structured
    TLD information including domain, subdomain, suffix, registered domain, and FQDN.
    
    When to use:
        - Need to parse domain components from a URL
        - Extract TLD information
        - Domain structure analysis
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        url: URL or domain string to extract TLD information from.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - domain: Domain name without subdomain or TLD
        - subdomain: Subdomain part
        - suffix: Top-level domain (TLD)
        - registered_domain: Domain + suffix
        - fqdn: Fully qualified domain name with subdomain
    
    Examples:
        Extract from full URL:
            url="https://www.example.com"
            Returns: domain="example", subdomain="www", suffix="com", registered_domain="example.com", fqdn="www.example.com"
        
        Extract from domain string:
            url="subdomain.example.org"
            Returns: All domain components parsed
    """
    try:
        safe_log_info(logger, "[webc_get_domain_tld_info] Starting extraction", url=url)
        
        # Validate inputs
        if not url or not isinstance(url, str):
            error_msg = "url must be a non-empty string"
            safe_log_error(logger, "[webc_get_domain_tld_info] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        url = url.strip()
        
        safe_log_debug(logger, "[webc_get_domain_tld_info] Extracting TLD info", url=url)
        
        tld_info = get_domain_tld_info(url)
        
        result = {
            "status": "success",
            "url": url,
            "domain": tld_info.domain if hasattr(tld_info, 'domain') else None,
            "subdomain": tld_info.subdomain if hasattr(tld_info, 'subdomain') else None,
            "suffix": tld_info.suffix if hasattr(tld_info, 'suffix') else None,
            "registered_domain": tld_info.registered_domain if hasattr(tld_info, 'registered_domain') else None,
            "fqdn": tld_info.fqdn if hasattr(tld_info, 'fqdn') else None
        }
        
        safe_log_info(logger, "[webc_get_domain_tld_info] Extraction complete", 
                     domain=result.get("domain"),
                     registered_domain=result.get("registered_domain"))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Domain TLD extraction failed: {str(e)}"
        safe_log_error(logger, "[webc_get_domain_tld_info] Error", 
                     exc_info=True,
                     error=str(e),
                     url=url if 'url' in locals() else None)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_extract_keyterms_textrank(
    runtime: ToolRuntime,
    text: str,
    topn: int = 10,
    normalize: str = "lemma"
) -> str:
    """
    Extract key terms from text using TextRank algorithm only.
    
    Uses the TextRank algorithm (similar to PageRank) to identify the most
    important terms in a document based on co-occurrence patterns.
    Faster than webc_extract_keyterms which uses multiple algorithms.
    
    When to use:
        - Need fast key term extraction
        - Only need TextRank results
        - Extract keywords from text
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Text content to extract key terms from.
        topn: Number of top key terms to return (default: 10).
        normalize: Normalization method - "lemma", "lower", or "none" (default: "lemma").
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - keyterms: List of tuples (term, score) sorted by importance
    
    Examples:
        Extract top 10 terms:
            text="Your text here", topn=10, normalize="lemma"
            Returns: Top 10 most important terms with TextRank scores
        
        Extract with different normalization:
            text="Your text here", topn=5, normalize="lower"
            Returns: Terms normalized to lowercase
    """
    try:
        safe_log_info(logger, "[webc_extract_keyterms_textrank] Starting extraction", 
                     text_length=len(text) if text else 0, topn=topn, normalize=normalize)
        
        # Validate inputs
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            error_msg = "text must be a non-empty string"
            safe_log_error(logger, "[webc_extract_keyterms_textrank] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if topn < 1 or topn > 100:
            error_msg = "topn must be between 1 and 100"
            safe_log_error(logger, "[webc_extract_keyterms_textrank] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if normalize not in ["lemma", "lower", "none"]:
            error_msg = "normalize must be one of: 'lemma', 'lower', 'none'"
            safe_log_error(logger, "[webc_extract_keyterms_textrank] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_extract_keyterms_textrank] Extracting keyterms", topn=topn, normalize=normalize)
        
        keyterms = extract_keyterms_textrank(text, topn=topn, normalize=normalize)
        
        result = {
            "status": "success",
            "keyterms": [
                {"term": term, "score": score}
                for term, score in (keyterms if keyterms else [])
            ]
        }
        
        safe_log_info(logger, "[webc_extract_keyterms_textrank] Extraction complete", 
                     keyterms_count=len(result["keyterms"]))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"TextRank key term extraction failed: {str(e)}"
        safe_log_error(logger, "[webc_extract_keyterms_textrank] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_calculate_similarity_spacy(
    runtime: ToolRuntime,
    text1: str,
    text2: str
) -> str:
    """
    Calculate semantic similarity between two texts using spaCy word vectors.
    
    Uses spaCy's pre-trained word vectors to compute semantic similarity
    based on meaning rather than exact word matching.
    
    When to use:
        - Need semantic similarity (meaning-based, not word-based)
        - Compare texts for similar meaning
        - Fast semantic comparison
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text1: First text to compare.
        text2: Second text to compare.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - similarity: Semantic similarity score (0.0 to 1.0, higher is more similar)
        - similarity_percentage: Similarity as percentage (0-100)
    
    Examples:
        Similar texts:
            text1="Hello world", text2="Hi there"
            Returns: High similarity score (e.g., 0.85) - similar meaning
        
        Different texts:
            text1="Python programming", text2="Cooking recipes"
            Returns: Low similarity score (e.g., 0.15) - different topics
    """
    try:
        safe_log_info(logger, "[webc_calculate_similarity_spacy] Starting calculation", 
                     text1_length=len(text1) if text1 else 0,
                     text2_length=len(text2) if text2 else 0)
        
        # Validate inputs
        if not text1 or not isinstance(text1, str) or len(text1.strip()) == 0:
            error_msg = "text1 must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_similarity_spacy] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not text2 or not isinstance(text2, str) or len(text2.strip()) == 0:
            error_msg = "text2 must be a non-empty string"
            safe_log_error(logger, "[webc_calculate_similarity_spacy] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_calculate_similarity_spacy] Calculating semantic similarity")
        
        similarity = calculate_similarity_spacy(text1, text2)
        
        result = {
            "status": "success",
            "similarity": similarity,
            "similarity_percentage": round(similarity * 100, 2) if similarity else 0
        }
        
        safe_log_info(logger, "[webc_calculate_similarity_spacy] Calculation complete", 
                     similarity=similarity)
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Semantic similarity calculation failed: {str(e)}"
        safe_log_error(logger, "[webc_calculate_similarity_spacy] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_remove_stopwords(
    runtime: ToolRuntime,
    text: str,
    filter_alphanum: bool = False
) -> str:
    """
    Remove stop words from text.
    
    Tokenizes the input text, optionally filters out non-alphanumeric tokens,
    then removes all tokens that are in the stop words list.
    
    When to use:
        - Need to clean text by removing common words
        - Preprocess text for analysis
        - Reduce text to meaningful words only
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        text: Input text from which to remove stop words.
        filter_alphanum: If True, removes all tokens that are not alphanumeric
                        (except periods). Default: False.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - original_text: The input text
        - cleaned_text: Text with stop words removed
        - original_length: Character count of original text
        - cleaned_length: Character count of cleaned text
    
    Examples:
        Remove stop words:
            text="The quick brown fox jumps over the lazy dog", filter_alphanum=False
            Returns: "quick brown fox jumps lazy dog" (removed: the, over, the)
        
        With alphanumeric filter:
            text="Hello! World 123", filter_alphanum=True
            Returns: Only alphanumeric tokens, stop words removed
    """
    try:
        safe_log_info(logger, "[webc_remove_stopwords] Starting removal", 
                     text_length=len(text) if text else 0, filter_alphanum=filter_alphanum)
        
        # Validate inputs
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            error_msg = "text must be a non-empty string"
            safe_log_error(logger, "[webc_remove_stopwords] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_remove_stopwords] Removing stopwords", filter_alphanum=filter_alphanum)
        
        cleaned_text = remove_stopwords_from_text(text, filter_alphanum=filter_alphanum)
        
        result = {
            "status": "success",
            "original_text": text,
            "cleaned_text": cleaned_text,
            "original_length": len(text),
            "cleaned_length": len(cleaned_text) if cleaned_text else 0
        }
        
        safe_log_info(logger, "[webc_remove_stopwords] Removal complete", 
                     original_length=result["original_length"],
                     cleaned_length=result["cleaned_length"])
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Stop word removal failed: {str(e)}"
        safe_log_error(logger, "[webc_remove_stopwords] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})


@tool
def webc_validate_credit_card(
    runtime: ToolRuntime,
    cc_number: str
) -> str:
    """
    Validate and analyze a credit card number.
    
    Validates a credit card number using Luhn algorithm and identifies
    the card issuer. Returns formatted card number and issuer information.
    
    When to use:
        - Need to validate credit card numbers
        - Identify card issuer
        - Format card numbers
    
    Args:
        runtime: ToolRuntime instance (automatically injected by LangChain).
        cc_number: Credit card number to validate and analyze.
    
    Returns:
        JSON string containing:
        - status: "success" or "error"
        - valid: Whether the card number is valid
        - formatted_card: Formatted card number
        - issuer: Card issuer information (if valid)
        - message: Validation message
    
    Examples:
        Valid card:
            cc_number="4111111111111111"
            Returns: valid=True, formatted_card="4111 1111 1111 1111", issuer="Visa"
        
        Invalid card:
            cc_number="1234567890123456"
            Returns: valid=False, message="Invalid credit card number"
    """
    try:
        safe_log_info(logger, "[webc_validate_credit_card] Starting validation", 
                     cc_number_length=len(cc_number) if cc_number else 0)
        
        # Validate inputs
        if not cc_number or not isinstance(cc_number, str) or len(cc_number.strip()) == 0:
            error_msg = "cc_number must be a non-empty string"
            safe_log_error(logger, "[webc_validate_credit_card] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        safe_log_debug(logger, "[webc_validate_credit_card] Validating card")
        
        try:
            card_details = get_creditcard_details(cc_number)
            
            result = {
                "status": "success",
                "valid": True,
                "formatted_card": card_details.card_number if hasattr(card_details, 'card_number') else None,
                "issuer": card_details.issuer if hasattr(card_details, 'issuer') else None,
                "message": "Credit card is valid"
            }
        except ValueError as ve:
            # Invalid card number
            result = {
                "status": "success",
                "valid": False,
                "formatted_card": None,
                "issuer": None,
                "message": str(ve)
            }
        
        safe_log_info(logger, "[webc_validate_credit_card] Validation complete", 
                     valid=result.get("valid"))
        
        return json.dumps(result, default=str)
        
    except Exception as e:
        error_msg = f"Credit card validation failed: {str(e)}"
        safe_log_error(logger, "[webc_validate_credit_card] Error", 
                     exc_info=True,
                     error=str(e))
        return json.dumps({"status": "error", "message": error_msg})

