"""
OpenCTI (Open Cyber Threat Intelligence) Threat Intelligence Tools for LangChain Agents

This module provides LangChain tools for querying OpenCTI threat intelligence platforms.
All tools use ToolRuntime to securely access API keys and configuration from agent state,
following LangChain v1.0 best practices for tools with state access.

Reference: https://docs.langchain.com/oss/python/langchain/tools
OpenCTI Python Client: https://github.com/OpenCTI-Platform/opencti/tree/master/client-python

Key Features:
- Secure API key and URL management via ToolRuntime (keys never exposed to LLM)
- Comprehensive threat intelligence queries (indicators, malware, threat actors, reports)
- STIX 2.1 compliant data structures
- User tracking and audit logging via agent state

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.ti.opencti import (
        opencti_search_indicators,
        opencti_search_malware,
        opencti_search_threat_actors,
        opencti_get_report,
        opencti_list_attack_patterns
    )
    
    agent = create_agent(
        model=llm,
        tools=[opencti_search_indicators, opencti_search_malware, ...],
        system_prompt="You are a threat intelligence analyst..."
    )
    
    # Initialize state with API key and OpenCTI URL
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Search for indicators related to APT28"}],
        "api_keys": {"API_KEY": "your_api_key"},
        "opencti_url": "https://your-opencti-instance.com",
        "user_id": "analyst_001"
    })
"""

import os
import json
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field

# Try to import pycti, handle gracefully if libmagic is not available
try:
    from pycti import OpenCTIApiClient
    PYCTI_AVAILABLE = True
except ImportError as e:
    PYCTI_AVAILABLE = False
    OpenCTIApiClient = None
    IMPORT_ERROR = str(e)


class OpenCTISecurityAgentState(AgentState):
    """
    Extended agent state schema for OpenCTI threat intelligence operations.
    
    This state schema extends the base AgentState to include:
    - Security credentials (API keys stored securely in state)
    - OpenCTI instance URL configuration
    - User identification for audit trails
    - Threat context for maintaining analysis history
    
    Attributes:
        user_id: Identifier for the user running the analysis (for audit logging)
        api_keys: Dictionary mapping service names to API keys, e.g., {"API_KEY": "key123"}
        opencti_url: URL of the OpenCTI instance (e.g., "https://opencti.example.com")
        threat_context: Dictionary storing threat intelligence context and analysis history
    
    Example:
        state = {
            "messages": [...],
            "user_id": "analyst_001",
            "api_keys": {"API_KEY": "opencti_api_key_here"},
            "opencti_url": "https://opencti.example.com",
            "threat_context": {"last_analysis": {...}}
        }
    """
    user_id: str = ""
    api_keys: Dict[str, str] = {}  # Store API keys securely in state
    opencti_url: str = ""  # OpenCTI instance URL
    threat_context: Dict[str, Any] = {}  # Store threat intelligence context


def _get_opencti_client(runtime: ToolRuntime) -> Optional[Any]:
    """
    Get OpenCTI API client from runtime state.
    
    Args:
        runtime: ToolRuntime instance providing access to agent state
    
    Returns:
        OpenCTIApiClient instance or None if configuration is missing
    """
    if not PYCTI_AVAILABLE:
        return None
    
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    opencti_url = runtime.state.get("opencti_url", "")
    
    if not api_key or not opencti_url:
        return None
    
    try:
        return OpenCTIApiClient(opencti_url, api_key)
    except Exception as e:
        return None


def _format_opencti_result(data: Any, result_type: str = "data") -> str:
    """
    Format OpenCTI API response for JSON serialization.
    
    Args:
        data: OpenCTI API response data
        result_type: Type of result ("data", "error", etc.)
    
    Returns:
        JSON string representation of the result
    """
    try:
        if isinstance(data, dict):
            return json.dumps(data, indent=2, default=str)
        elif isinstance(data, list):
            return json.dumps({"results": data, "count": len(data)}, indent=2, default=str)
        else:
            return json.dumps({"result": str(data)}, indent=2, default=str)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error formatting result: {str(e)}"
        })


@tool
def opencti_search_indicators(runtime: ToolRuntime, query: str, limit: int = 10) -> str:
    """
    Search for indicators of compromise (IOCs) in OpenCTI.
    
    This tool queries OpenCTI for indicators matching the search query. Indicators can include
    IP addresses, domains, URLs, file hashes (MD5, SHA1, SHA256), email addresses, and other
    observable patterns. Results are returned in STIX 2.1 format.
    
    When to use:
        - User asks to search for indicators, IOCs, or observables
        - Need to find IP addresses, domains, or URLs associated with threats
        - Looking for file hashes related to malware
        - Checking if specific indicators exist in OpenCTI
        - Incident response: searching for IOCs related to an incident
    
    When NOT to use:
        - User wants to search for malware families (use opencti_search_malware instead)
        - User wants to search for threat actors (use opencti_search_threat_actors instead)
        - User wants to search for attack patterns (use opencti_list_attack_patterns instead)
        - Query is empty or invalid
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM. Provides secure access to
            API keys via runtime.state.get("api_keys", {}).get("API_KEY") and
            OpenCTI URL via runtime.state.get("opencti_url")
        query: Search query for indicators. Can be:
            - Indicator value (e.g., "192.168.1.1", "example.com", "malware.exe")
            - Search term (e.g., "APT28", "ransomware")
            - Pattern (e.g., "file:hashes.MD5 = 'abc123'")
        limit: Maximum number of results to return (default: 10, max: 100)
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "count": int (number of results),
            "indicators": list (STIX 2.1 indicator objects),
            "user_id": str
        }
    
    Errors:
        - "OpenCTI client not available" - pycti library not installed or libmagic missing
        - "OpenCTI API key or URL not found in agent state" - Configuration missing
        - "OpenCTI API error: {message}" - API request failed
        - "Unexpected error: {message}" - Other errors
    
    Example:
        User: "Search for indicators related to APT28"
        Tool call: opencti_search_indicators(query="APT28", limit=10)
        Returns: JSON with list of indicators associated with APT28
    """
    if not PYCTI_AVAILABLE:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI client not available: {IMPORT_ERROR}. Please install pycti and libmagic."
        })
    
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    opencti_url = runtime.state.get("opencti_url", "")
    
    if not api_key or not opencti_url:
        return json.dumps({
            "status": "error",
            "message": "OpenCTI API key or URL not found in agent state. Ensure 'api_keys.API_KEY' and 'opencti_url' are set in agent state."
        })
    
    try:
        client = OpenCTIApiClient(opencti_url, api_key)
        
        # Search for indicators using the query
        filters = [{"key": "value", "values": [query]}]
        indicators = client.indicator.list(filters=filters, first=limit)
        # Return the exact OpenCTI API response
        return _format_opencti_result(indicators)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI API error: {str(e)}"
        })


@tool
def opencti_search_malware(runtime: ToolRuntime, query: str, limit: int = 10) -> str:
    """
    Search for malware families and samples in OpenCTI.
    
    This tool queries OpenCTI for malware objects matching the search query. Malware objects
    can include malware families, variants, and samples with their associated indicators,
    attack patterns, and threat actors.
    
    When to use:
        - User asks to search for malware, malware families, or samples
        - Need to find information about specific malware (e.g., "Emotet", "TrickBot")
        - Looking for malware variants or aliases
        - Checking malware relationships to indicators or threat actors
        - Incident response: identifying malware involved in an incident
    
    When NOT to use:
        - User wants to search for indicators (use opencti_search_indicators instead)
        - User wants to search for threat actors (use opencti_search_threat_actors instead)
        - Query is empty or invalid
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM.
        query: Search query for malware. Can be:
            - Malware name (e.g., "Emotet", "TrickBot", "WannaCry")
            - Malware family (e.g., "Trojan", "Ransomware")
            - Alias or variant name
        limit: Maximum number of results to return (default: 10, max: 100)
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "count": int,
            "malware": list (STIX 2.1 malware objects),
            "query": str,
            "user_id": str
        }
    
    Errors:
        - "OpenCTI client not available" - pycti library not installed
        - "OpenCTI API key or URL not found" - Configuration missing
        - "OpenCTI API error: {message}" - API request failed
    
    Example:
        User: "Search for Emotet malware in OpenCTI"
        Tool call: opencti_search_malware(query="Emotet", limit=10)
        Returns: JSON with Emotet malware information and relationships
    """
    if not PYCTI_AVAILABLE:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI client not available: {IMPORT_ERROR}. Please install pycti and libmagic."
        })
    
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    opencti_url = runtime.state.get("opencti_url", "")
    
    if not api_key or not opencti_url:
        return json.dumps({
            "status": "error",
            "message": "OpenCTI API key or URL not found in agent state. Ensure 'api_keys.API_KEY' and 'opencti_url' are set in agent state."
        })
    
    try:
        client = OpenCTIApiClient(opencti_url, api_key)
        
        # Search for malware using the query
        filters = [{"key": "name", "values": [query]}]
        malware = client.malware.list(filters=filters, first=limit)
        # Return the exact OpenCTI API response
        return _format_opencti_result(malware)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI API error: {str(e)}"
        })


@tool
def opencti_search_threat_actors(runtime: ToolRuntime, query: str, limit: int = 10) -> str:
    """
    Search for threat actors and intrusion sets in OpenCTI.
    
    This tool queries OpenCTI for threat actor objects matching the search query. Threat actors
    can include APT groups, cybercriminal organizations, and intrusion sets with their associated
    malware, attack patterns, campaigns, and indicators.
    
    When to use:
        - User asks to search for threat actors, APT groups, or intrusion sets
        - Need to find information about specific threat actors (e.g., "APT28", "Lazarus", "FIN7")
        - Looking for threat actor aliases or identifiers
        - Checking threat actor relationships to malware or attack patterns
        - Attribution: identifying threat actors behind an attack
    
    When NOT to use:
        - User wants to search for indicators (use opencti_search_indicators instead)
        - User wants to search for malware (use opencti_search_malware instead)
        - Query is empty or invalid
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM.
        query: Search query for threat actors. Can be:
            - Threat actor name (e.g., "APT28", "Lazarus", "FIN7")
            - Alias or identifier (e.g., "Fancy Bear", "Cozy Bear")
            - Intrusion set name
        limit: Maximum number of results to return (default: 10, max: 100)
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "count": int,
            "threat_actors": list (STIX 2.1 threat actor objects),
            "query": str,
            "user_id": str
        }
    
    Errors:
        - "OpenCTI client not available" - pycti library not installed
        - "OpenCTI API key or URL not found" - Configuration missing
        - "OpenCTI API error: {message}" - API request failed
    
    Example:
        User: "Search for APT28 threat actor in OpenCTI"
        Tool call: opencti_search_threat_actors(query="APT28", limit=10)
        Returns: JSON with APT28 threat actor information and relationships
    """
    if not PYCTI_AVAILABLE:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI client not available: {IMPORT_ERROR}. Please install pycti and libmagic."
        })
    
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    opencti_url = runtime.state.get("opencti_url", "")
    
    if not api_key or not opencti_url:
        return json.dumps({
            "status": "error",
            "message": "OpenCTI API key or URL not found in agent state. Ensure 'api_keys.API_KEY' and 'opencti_url' are set in agent state."
        })
    
    try:
        client = OpenCTIApiClient(opencti_url, api_key)
        
        # Search for threat actors using the query
        filters = [{"key": "name", "values": [query]}]
        threat_actors = client.threat_actor.list(filters=filters, first=limit)
        # Return the exact OpenCTI API response
        return _format_opencti_result(threat_actors)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI API error: {str(e)}"
        })


@tool
def opencti_get_report(runtime: ToolRuntime, report_id: Optional[str] = None, query: Optional[str] = None, limit: int = 10) -> str:
    """
    Get a threat intelligence report from OpenCTI by ID or search for reports.
    
    This tool retrieves threat intelligence reports from OpenCTI. Reports can contain
    detailed analysis, indicators, malware information, threat actor attribution, and
    other threat intelligence data in STIX 2.1 format.
    
    When to use:
        - User asks to get a specific report by ID
        - Need to search for reports related to a topic or threat
        - Looking for recent threat intelligence reports
        - Need detailed analysis and context about a threat
        - Incident response: retrieving relevant threat intelligence reports
    
    When NOT to use:
        - User wants to search for indicators (use opencti_search_indicators instead)
        - User wants to search for malware (use opencti_search_malware instead)
        - Both report_id and query are None
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM.
        report_id: Optional OpenCTI report ID to retrieve a specific report
        query: Optional search query to find reports by name or content
        limit: Maximum number of results when searching (default: 10, max: 100)
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "report": dict (STIX 2.1 report object) or list of reports,
            "user_id": str
        }
    
    Errors:
        - "OpenCTI client not available" - pycti library not installed
        - "OpenCTI API key or URL not found" - Configuration missing
        - "Either report_id or query must be provided" - Missing parameters
        - "OpenCTI API error: {message}" - API request failed
    
    Example:
        User: "Get report with ID abc123 from OpenCTI"
        Tool call: opencti_get_report(report_id="abc123")
        Returns: JSON with report details
    """
    if not PYCTI_AVAILABLE:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI client not available: {IMPORT_ERROR}. Please install pycti and libmagic."
        })
    
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    opencti_url = runtime.state.get("opencti_url", "")
    
    if not api_key or not opencti_url:
        return json.dumps({
            "status": "error",
            "message": "OpenCTI API key or URL not found in agent state. Ensure 'api_keys.API_KEY' and 'opencti_url' are set in agent state."
        })
    
    if not report_id and not query:
        return json.dumps({
            "status": "error",
            "message": "Either report_id or query must be provided."
        })
    
    try:
        client = OpenCTIApiClient(opencti_url, api_key)
        
        if report_id:
            # Get specific report by ID
            report = client.report.read(id=report_id)
            # Return the exact OpenCTI API response
            return _format_opencti_result(report)
        else:
            # Search for reports
            filters = [{"key": "name", "values": [query]}]
            reports = client.report.list(filters=filters, first=limit)
            # Return the exact OpenCTI API response
            return _format_opencti_result(reports)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI API error: {str(e)}"
        })


@tool
def opencti_list_attack_patterns(runtime: ToolRuntime, query: Optional[str] = None, limit: int = 20) -> str:
    """
    List attack patterns (MITRE ATT&CK techniques) from OpenCTI.
    
    This tool retrieves MITRE ATT&CK attack patterns from OpenCTI. Attack patterns represent
    techniques and tactics used by adversaries, mapped to the MITRE ATT&CK framework.
    
    When to use:
        - User asks to list or search for MITRE ATT&CK techniques
        - Need to find attack patterns related to a specific technique ID (e.g., "T1055")
        - Looking for techniques used by specific malware or threat actors
        - Threat modeling: identifying attack patterns
        - Incident response: mapping observed behaviors to ATT&CK techniques
    
    When NOT to use:
        - User wants to search for indicators (use opencti_search_indicators instead)
        - User wants to search for malware (use opencti_search_malware instead)
        - Query is invalid
    
    Args:
        runtime: ToolRuntime instance providing access to agent state.
            Automatically injected and hidden from the LLM.
        query: Optional search query for attack patterns. Can be:
            - Technique ID (e.g., "T1055", "T1059.001")
            - Technique name (e.g., "Process Injection", "Command and Scripting Interpreter")
        limit: Maximum number of results to return (default: 20, max: 100)
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "count": int,
            "attack_patterns": list (STIX 2.1 attack pattern objects),
            "query": str (if provided),
            "user_id": str
        }
    
    Errors:
        - "OpenCTI client not available" - pycti library not installed
        - "OpenCTI API key or URL not found" - Configuration missing
        - "OpenCTI API error: {message}" - API request failed
    
    Example:
        User: "List MITRE ATT&CK techniques in OpenCTI"
        Tool call: opencti_list_attack_patterns(limit=20)
        Returns: JSON with list of attack patterns
    """
    if not PYCTI_AVAILABLE:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI client not available: {IMPORT_ERROR}. Please install pycti and libmagic."
        })
    
    api_key = runtime.state.get("api_keys", {}).get("API_KEY")
    opencti_url = runtime.state.get("opencti_url", "")
    
    if not api_key or not opencti_url:
        return json.dumps({
            "status": "error",
            "message": "OpenCTI API key or URL not found in agent state. Ensure 'api_keys.API_KEY' and 'opencti_url' are set in agent state."
        })
    
    try:
        client = OpenCTIApiClient(opencti_url, api_key)
        
        # List attack patterns, optionally filtered by query
        filters = []
        if query:
            filters = [{"key": "name", "values": [query]}]
        
        attack_patterns = client.attack_pattern.list(filters=filters, first=limit)
        # Return the exact OpenCTI API response
        return _format_opencti_result(attack_patterns)
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"OpenCTI API error: {str(e)}"
        })


# Usage with LangChain Agent

if __name__ == "__main__":
    from langchain.agents import create_agent

    # Initialize agent with OpenCTI tools
    tools = [
        opencti_search_indicators,
        opencti_search_malware,
        opencti_search_threat_actors,
        opencti_get_report,
        opencti_list_attack_patterns
    ]

    # Create agent with custom state
    agent = create_agent(
        model="claude-sonnet-4-5-20250929",
        tools=tools,
        system_prompt="""You are a cybersecurity threat intelligence analyst. 
        Use the OpenCTI tools to search for indicators, malware, threat actors, reports, 
        and attack patterns. Provide detailed threat assessments and recommendations based on OpenCTI data.""",
        state_schema=OpenCTISecurityAgentState
    )

    # Initialize state with API key and URL
    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": "Search for indicators related to APT28"
            }
        ],
        "user_id": "analyst_001",
        "api_keys": {
            "API_KEY": os.getenv("OPENCTI_API_KEY", "your_api_key_here")
        },
        "opencti_url": os.getenv("OPENCTI_URL", "https://your-opencti-instance.com"),
        "threat_context": {}
    }

