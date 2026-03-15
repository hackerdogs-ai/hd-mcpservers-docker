"""
VictoriaLogs Tools for LangChain Agents

This module provides LangChain tools for querying VictoriaLogs using LogsQL syntax.
All tools follow LangChain v1.0 best practices and include comprehensive error handling
and logging.

Reference: 
- LangChain Tools: https://docs.langchain.com/oss/python/langchain/tools
- VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
- LogsQL Syntax: https://docs.victoriametrics.com/victorialogs/logsql/

Key Features:
- Query VictoriaLogs using LogsQL syntax
- Stats queries for aggregations and metrics
- Hits analysis for time-series data
- Multi-tenancy support (tenant isolation)
- Comprehensive error handling and logging
- Resource usage limits and timeout handling
- Support for extra filters, hidden fields, and partial responses

Multi-Tenancy Support:
VictoriaLogs supports multi-tenancy through the tenant parameter. Each tenant has
isolated data and queries. The tenant ID format is "AccountID:ProjectID" (e.g., "0:0").
All tools support the tenant parameter for querying specific tenant data.

Querying Capabilities:
- Standard log queries via /select/logsql/query endpoint
- Stats queries via /select/logsql/stats_query endpoint (single point)
- Stats queries via /select/logsql/stats_query_range endpoint (time range)
- Hits analysis via /select/logsql/hits endpoint
- Facets analysis via /select/logsql/facets endpoint (most frequent values)
- Field discovery via /select/logsql/field_names endpoint
- Field values via /select/logsql/field_values endpoint
- Stream discovery via /select/logsql/streams endpoint
- Stream IDs via /select/logsql/stream_ids endpoint
- Stream field names via /select/logsql/stream_field_names endpoint
- Stream field values via /select/logsql/stream_field_values endpoint
- Tenant listing via /select/logsql/tenants endpoint
- Support for extra filters, hidden fields, and partial responses
- Resource usage limits (max query time range, max query duration, max concurrent requests)
- Timeout support (default 30 seconds, configurable)

Usage:
    from langchain.agents import create_agent
    from shared.modules.tools.victorialogs_tool import (
        victorialogs_query,
        victorialogs_stats,
        victorialogs_hits,
        victorialogs_facets,
        victorialogs_field_names,
        victorialogs_field_values,
        victorialogs_stats_range,
        victorialogs_streams,
        victorialogs_stream_ids,
        victorialogs_stream_field_names,
        victorialogs_stream_field_values,
        victorialogs_tenants
    )
    
    agent = create_agent(
        model=llm,
        tools=[
            victorialogs_query,
            victorialogs_stats,
            victorialogs_hits,
            victorialogs_facets,
            victorialogs_field_names,
            victorialogs_field_values,
            victorialogs_stats_range,
            victorialogs_streams,
            victorialogs_stream_ids,
            victorialogs_stream_field_names,
            victorialogs_stream_field_values,
            victorialogs_tenants
        ],
        system_prompt="You are a log analyst..."
    )
    
    # Single tenant query
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Show me errors from the last hour"}]
    })
    
    # Multi-tenant query (tenant="1:2" for AccountID 1, ProjectID 2)
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Show me errors from tenant 1:2"}]
    })
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from langchain.tools import tool
from pydantic import BaseModel, Field

from hd_logging import setup_logger

logger = setup_logger(__name__, log_file_path="logs/victorialogs_tool.log")


class VictoriaLogsQueryInput(BaseModel):
    """Input schema for VictoriaLogs query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query to execute against VictoriaLogs. "
            "Examples: '_time:1h error', '{job=\"nginx\"} _time:1h', 'level:error _time:1h', "
            "'_time:1h \"failed login\" level:error', '_time:1h | stats count()'. "
            "See tool description for comprehensive LogsQL syntax examples."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format (e.g., '2025-01-01T00:00:00Z'). If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format (e.g., '2025-01-01T23:59:59Z'). If not provided, defaults to now."
    )
    limit: Optional[int] = Field(
        100,
        description="Maximum number of log entries to return (default: 100, max: 10000)"
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant. Multi-tenancy allows isolated data "
            "and queries per tenant. Each tenant has separate log streams and data."
        )
    )


class VictoriaLogsStatsInput(BaseModel):
    """Input schema for VictoriaLogs stats query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL stats query to execute. Must include '| stats' clause. "
            "Examples: '* | stats count()', '_time:1h | stats by (level) count()', "
            "'_time:1h error | stats count() logs, count() if (error) errors'. "
            "Field names in 'stats by' MUST be in parentheses: 'stats by (field_name) count()'. "
            "See tool description for comprehensive stats examples."
        )
    )
    time: Optional[str] = Field(
        None,
        description="Time for the stats query in ISO format. If not provided, defaults to now."
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant. Multi-tenancy allows isolated data "
            "and queries per tenant. Each tenant has separate log streams and data."
        )
    )


class VictoriaLogsHitsInput(BaseModel):
    """Input schema for VictoriaLogs hits query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query for hits analysis. "
            "Examples: '* | hits', '_time:1h | hits', '_time:1d | hits by (level)', "
            "'_time:1d error | hits step=1h'. "
            "See tool description for comprehensive hits examples."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format"
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format"
    )
    step: Optional[str] = Field(
        "1h",
        description="Time step for aggregation (e.g., '1m', '1h', '1d')"
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant. Multi-tenancy allows isolated data "
            "and queries per tenant. Each tenant has separate log streams and data."
        )
    )


class VictoriaLogsFacetsInput(BaseModel):
    """Input schema for VictoriaLogs facets query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query for facets analysis. "
            "Examples: '_time:1h', '_time:1h error', '{job=\"nginx\"} _time:1h'. "
            "Facets return the most frequent values per each log field."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    limit: Optional[int] = Field(
        10,
        description="Maximum number of values per field to return (default: 10)"
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsFieldNamesInput(BaseModel):
    """Input schema for VictoriaLogs field names query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query to filter logs before extracting field names. "
            "Examples: '_time:1h', '_time:1h error', '{job=\"nginx\"} _time:1h'. "
            "Use '*' to get all field names from all logs."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsFieldValuesInput(BaseModel):
    """Input schema for VictoriaLogs field values query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query to filter logs before extracting field values. "
            "Examples: '_time:1h', '_time:1h error', '{job=\"nginx\"} _time:1h'. "
            "Use '*' to get values from all logs."
        )
    )
    field: str = Field(
        ...,
        description="Field name to get unique values for (e.g., 'level', 'host', 'status_code')"
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    limit: Optional[int] = Field(
        100,
        description="Maximum number of unique values to return (default: 100)"
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsStatsRangeInput(BaseModel):
    """Input schema for VictoriaLogs stats query range tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL stats query to execute over a time range. Must include '| stats' clause. "
            "Examples: '* | stats count()', '_time:1h | stats by (level) count()', "
            "'_time:1h error | stats count() logs, count() if (error) errors'. "
            "Field names in 'stats by' MUST be in parentheses: 'stats by (field_name) count()'."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    step: Optional[str] = Field(
        "1h",
        description="Time step for aggregation (e.g., '1m', '1h', '1d')"
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsStreamsInput(BaseModel):
    """Input schema for VictoriaLogs streams query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query to filter streams. "
            "Examples: '*', '{job=\"nginx\"}', '_time:1h'. "
            "Use '*' to get all streams."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    limit: Optional[int] = Field(
        100,
        description="Maximum number of streams to return (default: 100)"
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsStreamIdsInput(BaseModel):
    """Input schema for VictoriaLogs stream IDs query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query to filter streams before extracting stream IDs. "
            "Examples: '*', '{job=\"nginx\"}', '_time:1h'. "
            "Use '*' to get all stream IDs."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsStreamFieldNamesInput(BaseModel):
    """Input schema for VictoriaLogs stream field names query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query to filter streams before extracting field names. "
            "Examples: '*', '{job=\"nginx\"}', '_time:1h'. "
            "Use '*' to get field names from all streams."
        )
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsStreamFieldValuesInput(BaseModel):
    """Input schema for VictoriaLogs stream field values query tool."""
    
    query: str = Field(
        ...,
        description=(
            "LogsQL query to filter streams before extracting field values. "
            "Examples: '*', '{job=\"nginx\"}', '_time:1h'. "
            "Use '*' to get values from all streams."
        )
    )
    field: str = Field(
        ...,
        description="Stream field name to get unique values for (e.g., 'job', 'instance', 'level')"
    )
    start: Optional[str] = Field(
        None,
        description="Start time for the query in ISO format. If not provided, defaults to 1 hour ago."
    )
    end: Optional[str] = Field(
        None,
        description="End time for the query in ISO format. If not provided, defaults to now."
    )
    limit: Optional[int] = Field(
        100,
        description="Maximum number of unique values to return (default: 100)"
    )
    tenant: Optional[str] = Field(
        "0:0",
        description=(
            "VictoriaLogs tenant ID in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "Default is '0:0' for the default tenant."
        )
    )


class VictoriaLogsTenantsInput(BaseModel):
    """Input schema for VictoriaLogs tenants query tool."""
    
    tenant: Optional[str] = Field(
        None,
        description=(
            "Optional tenant ID filter in format 'AccountID:ProjectID' (e.g., '0:0', '1:2'). "
            "If not provided, returns all tenants."
        )
    )


def _get_default_times() -> tuple[str, str]:
    """Get default start and end times (1 hour ago to now)."""
    now = datetime.now()
    start = (now - timedelta(hours=1)).isoformat() + "Z"
    end = now.isoformat() + "Z"
    return start, end


def _get_victorialogs_url() -> str:
    """Get VictoriaLogs URL from environment variable."""
    url = os.getenv('VICTORIALOGS_URL', 'http://localhost:9428')
    return url.rstrip('/')


def _execute_query(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a query against VictoriaLogs.
    
    This helper function handles HTTP requests to VictoriaLogs API endpoints,
    parses NDJSON responses, and returns structured data with error handling.
    
    Args:
        endpoint: The API endpoint path (e.g., '/select/logsql/query')
        params: Query parameters as a dictionary
        
    Returns:
        Dictionary with 'status' ('success' or 'error'), 'data' (list of parsed JSON objects),
        'count' (number of entries), and 'error' (error message if status is 'error')
    """
    try:
        base_url = _get_victorialogs_url()
        url = f"{base_url}{endpoint}"
        
        logger.debug(f"Executing VictoriaLogs query: {url}")
        logger.debug(f"Query parameters: {params}")
        
        session = requests.Session()
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        response = session.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            # VictoriaLogs returns newline-delimited JSON (NDJSON)
            # Parse each line as a separate JSON object
            lines = response.text.strip().split('\n')
            data = []
            for line in lines:
                if line.strip():  # Skip empty lines
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        # If a line fails to parse, include it as raw text
                        logger.warning(f"Failed to parse JSON line: {line[:100]}... Error: {str(e)}")
                        data.append({"raw_line": line, "parse_error": str(e)})
            
            logger.info(f"Successfully executed query, returned {len(data)} entries")
            return {
                "status": "success",
                "data": data,
                "count": len(data)
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"VictoriaLogs API error: {error_msg}")
            return {
                "status": "error",
                "error": error_msg
            }
    except requests.exceptions.Timeout:
        error_msg = "Request to VictoriaLogs timed out after 30 seconds"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Failed to connect to VictoriaLogs: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error executing VictoriaLogs query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "error": error_msg
        }


@tool(args_schema=VictoriaLogsQueryInput)
def victorialogs_query(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: Optional[int] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Query VictoriaLogs using LogsQL syntax to retrieve log entries.
    
    This tool enables the agent to query VictoriaLogs for log entries matching specific
    criteria. It supports time-based filtering, field filtering, stream filtering, and
    various LogsQL operations for log analysis.
    
    References:
    - LogsQL Syntax: https://docs.victoriametrics.com/victorialogs/logsql/
    - Querying API: https://docs.victoriametrics.com/victorialogs/querying/
    
    **Multi-Tenancy Support:**
    VictoriaLogs supports multi-tenancy through the tenant parameter. Each tenant has
    isolated data and queries. The tenant ID format is "AccountID:ProjectID" (e.g., "0:0").
    - Default tenant: "0:0" (used if tenant not specified)
    - Custom tenant: "1:2" (AccountID 1, ProjectID 2)
    - Tenant isolation ensures data security and query separation
    - All queries are scoped to the specified tenant
    
    **When to use this tool:**
    - To retrieve specific log entries matching search criteria
    - To analyze logs within a time range
    - To filter logs by severity, level, source, or other fields
    - To search for specific error messages or patterns
    - To investigate security incidents by querying relevant logs
    - To perform log analysis for troubleshooting or forensics
    - To query logs from specific tenants in multi-tenant deployments
    
    **When NOT to use this tool:**
    - For aggregations or statistics (use victorialogs_stats instead)
    - For time-series analysis (use victorialogs_hits instead)
    - If you need to discover available fields (use field discovery tools if available)
    - For queries that don't require log entry details
    
    **Input requirements:**
    - query: LogsQL query string (required)
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - limit: Maximum number of results (optional, default: 100, max: 10000)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of log entry objects
      - "count": Number of entries returned
      - "error": Error message (if status is "error")
    
    **Querying Capabilities:**
    - Standard log queries via /select/logsql/query endpoint
    - Supports extra filters, hidden fields, and partial responses
    - Resource usage limits: max query time range, max query duration, max concurrent requests
    - Timeout support: default 30 seconds (configurable via timeout query arg)
    - Streaming response: results are returned as NDJSON (newline-delimited JSON)
    
    **Limitations:**
    - Maximum limit of 10000 entries per query
    - Query timeout of 30 seconds (configurable)
    - Requires VICTORIALOGS_URL environment variable to be configured
    - Large result sets may be truncated
    - Always include _time filter for performance (e.g., '_time:1h')
    - Queries without time filters may be disallowed depending on server configuration
    - Resource limits may apply based on VictoriaLogs server settings
    
    **LogsQL Query Examples (from official docs):**
    
    **Time Filters:**
    - Recent logs: '_time:5m', '_time:1h', '_time:1d', '_time:1w'
    - Working hours: '_time:4w _time:week_range[Mon, Fri] _time:day_range[08:00, 18:00)'
    
    **Word & Phrase Filters:**
    - Single word: 'login', 'auth', 'access', 'failed'
    - Multiple words (AND): 'failed login', 'authentication failure'
    - OR logic: '(login or auth or access)'
    - Exclude: '-INFO', '-debug'
    - Phrases: '"authentication failed"', '"unauthorized access"', '"brute force"'
    
    **Stream & Field Filters:**
    - Stream filter: '{job="nginx", instance="host-123:5678"}'
    - Field filters: 'level:error', 'status:404', 'severity:critical'
    - Range filters: 'response_time:>1000', 'status_code:>=400'
    - Exact match: 'level:=error', 'host:=api-server-01'
    
    **Common Query Patterns:**
    - Recent errors: '_time:1h error'
    - App-specific: '{job="nginx"} _time:1h'
    - Field filter: 'level:error _time:1h'
    - Multiple conditions: '_time:1h "failed login" level:error'
    - Stream + word: '{app="api"} _time:5m error'
    - Exclude patterns: '_time:1h -INFO -debug error'
    
    **With Pipes (for basic operations):**
    - Count: '_time:1h error | count()'
    - Sort: '_time:1h error | sort by (_time)'
    - Limit: '_time:1h error | limit 10'
    - First N: '_time:5m error | first 10 by (_time desc)'
    - Extract fields: '_time:5m | extract "user_id=(<uid>)"'
    - Unique values: '_time:5m | uniq by (ip)'
    
    **Example use cases:**
    1. "Show me all error logs from the last hour": '_time:1h error'
    2. "Find logs containing 'authentication failed'": '_time:1h "authentication failed"'
    3. "Query nginx logs from the last day": '{job="nginx"} _time:1d'
    4. "Get critical level logs": 'level:critical _time:2h'
    5. "Find failed login attempts": '_time:1h "failed login" or "authentication failure"'
    """
    try:
        logger.info(f"Executing VictoriaLogs query: {query}")
        
        # Set defaults
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if limit is None:
            limit = 100
        if tenant is None:
            tenant = "0:0"
        
        # Validate limit
        limit = min(max(limit, 1), 10000)
        logger.debug(f"Query parameters: start={start}, end={end}, limit={limit}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "limit": limit,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/query", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsStatsInput)
def victorialogs_stats(
    query: str,
    time: Optional[str] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Execute a stats query against VictoriaLogs to get aggregations and metrics.
    
    This tool enables the agent to perform statistical analysis on log data using
    LogsQL stats operations. It's designed for aggregations, counts, averages, and
    other statistical computations.
    
    References:
    - LogsQL Syntax: https://docs.victoriametrics.com/victorialogs/logsql/
    - Querying API: https://docs.victoriametrics.com/victorialogs/querying/
    
    **Multi-Tenancy Support:**
    VictoriaLogs supports multi-tenancy through the tenant parameter. Each tenant has
    isolated data and queries. The tenant ID format is "AccountID:ProjectID" (e.g., "0:0").
    - Default tenant: "0:0" (used if tenant not specified)
    - Custom tenant: "1:2" (AccountID 1, ProjectID 2)
    - Tenant isolation ensures data security and query separation
    - All stats queries are scoped to the specified tenant
    
    **When to use this tool:**
    - To count log entries matching criteria
    - To calculate averages, sums, min/max values
    - To group statistics by fields (e.g., by severity, by source)
    - To calculate error rates or ratios
    - To get performance metrics from logs
    - To analyze log volume trends
    - To get statistics from specific tenants in multi-tenant deployments
    
    **When NOT to use this tool:**
    - To retrieve individual log entries (use victorialogs_query instead)
    - For time-series analysis (use victorialogs_hits instead)
    - If the query doesn't include '| stats' clause
    - For simple log retrieval without aggregation
    
    **Input requirements:**
    - query: LogsQL query with '| stats' clause (required)
    - time: ISO format timestamp (optional, defaults to now)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of stats result objects
      - "count": Number of stats results
      - "error": Error message (if status is "error")
    
    **Querying Capabilities:**
    - Stats queries via /select/logsql/stats_query endpoint
    - Supports stats at a specific time point
    - Supports extra filters, hidden fields, and partial responses
    - Resource usage limits: max query time range, max query duration, max concurrent requests
    - Timeout support: default 30 seconds (configurable via timeout query arg)
    
    **Limitations:**
    - Query must include '| stats' clause
    - Query timeout of 30 seconds (configurable)
    - Requires VICTORIALOGS_URL environment variable
    - Complex aggregations may be slow
    - ⚠️ CRITICAL: Field names in 'stats by' MUST be in parentheses: 'stats by (field_name) count()'
    - Resource limits may apply based on VictoriaLogs server settings
    
    **LogsQL Stats Query Examples (from official docs):**
    
    **Basic Counts:**
    - Total count: '* | stats count()'
    - Count by field: '_time:5m | stats by (level) count()'
    - Count by multiple fields: '_time:5m | stats by (level, host) count()'
    - Count with conditions: '_time:5m | stats count() logs, count() if (error) errors'
    
    **Aggregations:**
    - Sum: '_time:5m | stats sum(response_time)'
    - Average: '_time:5m | stats by (level) avg(response_time)'
    - Min/Max: '_time:5m | stats by (level) min(_time), max(_time)'
    - Unique counts: '_time:5m | stats by (level) count_uniq(user_id)'
    - Combined: '_time:5m | stats by (level) count(), sum(response_time), avg(response_time)'
    
    **Time-Based Stats:**
    - Per-hour: '_time:1d error | stats by (_time:1h) count() | sort by (_time)'
    - Per-minute: '_time:1h | stats by (_time:1m) count()'
    - Working hours: '_time:4w _time:week_range[Mon, Fri] _time:day_range[08:00, 18:00) | stats count()'
    
    **Network & IP Stats:**
    - IPv4 subnets: '_time:5m | stats by (ip:/24) count() rows | first 10 by (rows)'
    - IPv6 subnets: '_time:5m | stats by (ip:/64) count() rows'
    - Top IPs: '_time:5m | stats by (ip) count() | sort by (count() desc) | limit 10'
    
    **Error Analysis:**
    - Error ratio: '_time:5m | stats count() logs, count() if (error) errors | math errors / logs'
    - Error trends: '_time:1d error | stats by (_time:1h) count() | sort by (_time)'
    - Error by source: '_time:1h error | stats by (_stream) count() | sort by (count() desc)'
    
    **Filtered Stats:**
    - High-volume streams: '_time:5m | stats by (_stream) count() rows | filter rows:>1000'
    - Error streams only: '_time:1h error | stats by (_stream) count()'
    - App-specific: '{job="nginx"} _time:1h | stats by (level) count()'
    
    **Common Patterns:**
    - Top error sources: '_time:5m error | stats by (_stream) count() | sort by (count() desc) | limit 10'
    - Error rate over time: '_time:1h | stats by (_time:5m) count() logs, count() if (error) errors'
    - Performance metrics: '_time:1h | stats by (level) avg(response_time), max(response_time)'
    
    **Example use cases:**
    1. "Count all errors from the last hour": '_time:1h error | stats count()'
    2. "Show error counts by severity": '_time:1h | stats by (level) count()'
    3. "Calculate average response time by app": '_time:1h | stats by (_stream) avg(response_time)'
    4. "Get error rate statistics": '_time:1h | stats count() logs, count() if (error) errors'
    """
    try:
        logger.info(f"Executing VictoriaLogs stats query: {query}")
        
        if not time:
            time = datetime.now().isoformat() + "Z"
            logger.debug(f"Using default time: {time}")
        if not tenant:
            tenant = "0:0"
        
        # Validate that query includes stats
        if '| stats' not in query.lower():
            error_msg = "Stats query must include '| stats' clause. Example: '* | stats count()'"
            logger.warning(error_msg)
            return json.dumps({
                "status": "error",
                "error": error_msg
            }, indent=2)
        
        logger.debug(f"Stats query parameters: time={time}, tenant={tenant}")
        
        params = {
            "query": query,
            "time": time,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/stats_query", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs stats query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsHitsInput)
def victorialogs_hits(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    step: Optional[str] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Analyze log hits over time in VictoriaLogs for time-series analysis.
    
    This tool enables the agent to perform time-series analysis on log data, showing
    how log volume or patterns change over time. It's ideal for trend analysis,
    spike detection, and temporal pattern identification.
    
    References:
    - LogsQL Syntax: https://docs.victoriametrics.com/victorialogs/logsql/
    - Querying API: https://docs.victoriametrics.com/victorialogs/querying/
    
    **Multi-Tenancy Support:**
    VictoriaLogs supports multi-tenancy through the tenant parameter. Each tenant has
    isolated data and queries. The tenant ID format is "AccountID:ProjectID" (e.g., "0:0").
    - Default tenant: "0:0" (used if tenant not specified)
    - Custom tenant: "1:2" (AccountID 1, ProjectID 2)
    - Tenant isolation ensures data security and query separation
    - All hits queries are scoped to the specified tenant
    
    **When to use this tool:**
    - To analyze log volume trends over time
    - To detect spikes or anomalies in log patterns
    - To group hits by fields over time periods
    - To analyze error trends
    - To identify peak activity periods
    - To perform time-based correlation analysis
    - To analyze hits from specific tenants in multi-tenant deployments
    
    **When NOT to use this tool:**
    - To retrieve individual log entries (use victorialogs_query instead)
    - For single-point statistics (use victorialogs_stats instead)
    - If you don't need time-series data
    - For simple counts without time dimension
    
    **Input requirements:**
    - query: LogsQL query for hits analysis (required)
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - step: Time step for aggregation (optional, default: "1h")
      Examples: "1m", "5m", "1h", "1d"
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of hits result objects with time buckets
      - "count": Number of time buckets
      - "error": Error message (if status is "error")
    
    **Querying Capabilities:**
    - Hits queries via /select/logsql/hits endpoint
    - Supports time-based grouping and field-based grouping
    - Supports extra filters, hidden fields, and partial responses
    - Resource usage limits: max query time range, max query duration, max concurrent requests
    - Timeout support: default 30 seconds (configurable via timeout query arg)
    
    **Limitations:**
    - Query timeout of 30 seconds (configurable)
    - Requires VICTORIALOGS_URL environment variable
    - Large time ranges with small steps may be slow
    - Maximum step resolution depends on VictoriaLogs configuration
    - Resource limits may apply based on VictoriaLogs server settings
    
    **LogsQL Hits Query Examples (from official docs):**
    
    **Time-Based Hits:**
    - Basic hits: '* | hits'
    - Recent hits: '_time:1h | hits'
    - Hourly steps: '_time:1d | hits step=1h'
    - Minute steps: '_time:1h | hits step=1m'
    - Working hours: '_time:4w _time:week_range[Mon, Fri] _time:day_range[08:00, 18:00) | hits'
    
    **Grouped Hits:**
    - By field: '_time:1d | hits by (level)'
    - By stream: '_time:5m | hits by (_stream)'
    - By multiple fields: '_time:1h | hits by (level, host)'
    - By time and field: '_time:1d | hits step=1h by (level)'
    
    **Filtered Hits:**
    - Error hits: '_time:1d error | hits step=1h'
    - App-specific: '_time:1h {job="nginx"} | hits by (level)'
    - Error by source: '_time:1h error | hits by (_stream)'
    - Combined filters: '_time:1h {job="nginx"} error | hits by (level)'
    
    **Context & Patterns:**
    - Stacktrace context: '_time:5m stacktrace | stream_context before 10 after 100'
    - Error patterns: '_time:1h error | hits step=5m by (level)'
    - Volume spikes: '_time:1d | hits step=1h | filter hits:>1000'
    
    **Common Patterns:**
    - Error trends: '_time:1d error | hits step=1h'
    - Volume by app: '_time:1h | hits by (_stream) | sort by (hits desc)'
    - Peak hours: '_time:1d | hits step=1h | sort by (hits desc)'
    - Error spikes: '_time:1h error | hits step=1m by (level)'
    
    **Example use cases:**
    1. "Show log volume trends for the last day": '_time:1d | hits step=1h'
    2. "Analyze error hits per hour": '_time:1d error | hits step=1h'
    3. "Detect spikes in authentication failures": '_time:1h "authentication failed" | hits step=1m'
    4. "Show hits grouped by severity over time": '_time:1d | hits step=1h by (level)'
    """
    try:
        logger.info(f"Executing VictoriaLogs hits query: {query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if not step:
            step = "1h"
        if not tenant:
            tenant = "0:0"
        
        logger.debug(f"Hits query parameters: start={start}, end={end}, step={step}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/hits", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs hits query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsFacetsInput)
def victorialogs_facets(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: Optional[int] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Get the most frequent values per each log field (facets) from VictoriaLogs.
    
    This tool enables the agent to discover data distribution and common patterns
    in log data. It returns the most frequent values for each field, helping to
    understand what data is available and what values are common.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Facets API: https://docs.victoriametrics.com/victorialogs/querying/#querying-facets
    
    **When to use this tool:**
    - To discover the most common values in log fields
    - To understand data distribution and patterns
    - To find top IP addresses, error levels, status codes, etc.
    - To analyze field value frequencies
    - To discover what values exist in specific fields
    
    **When NOT to use this tool:**
    - To get individual log entries (use victorialogs_query instead)
    - To get statistics (use victorialogs_stats instead)
    - To get time-series data (use victorialogs_hits instead)
    
    **Input requirements:**
    - query: LogsQL query to filter logs (required)
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - limit: Maximum values per field (optional, default: 10)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": Dictionary with field names as keys and lists of {value, count} as values
      - "count": Number of fields with facets
      - "error": Error message (if status is "error")
    
    **Example use cases:**
    1. "What are the most common error levels?": '_time:1h | facets' (then check 'level' field)
    2. "Show top IP addresses": '_time:1h | facets' (then check 'ip' field)
    3. "What are the most frequent status codes?": '_time:1h | facets' (then check 'status_code' field)
    4. "Get facets for nginx logs": '{job="nginx"} _time:1h | facets'
    """
    try:
        logger.info(f"Executing VictoriaLogs facets query: {query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if limit is None:
            limit = 10
        if tenant is None:
            tenant = "0:0"
        
        logger.debug(f"Facets query parameters: start={start}, end={end}, limit={limit}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "limit": limit,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/facets", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs facets query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsFieldNamesInput)
def victorialogs_field_names(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Get available field names from logs matching the query in VictoriaLogs.
    
    This tool enables the agent to discover the schema of log data by listing
    all available field names. This is critical for building valid queries
    when the LLM doesn't know what fields exist in the logs.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Field Names API: https://docs.victoriametrics.com/victorialogs/querying/#querying-field-names
    
    **When to use this tool:**
    - To discover what fields are available in logs
    - To understand the log schema before building queries
    - To find field names for filtering or grouping
    - To validate that a field exists before using it in a query
    - To explore log structure
    
    **When NOT to use this tool:**
    - To get log entries (use victorialogs_query instead)
    - To get field values (use victorialogs_field_values instead)
    - If you already know the field names
    
    **Input requirements:**
    - query: LogsQL query to filter logs (required)
      Use '*' to get field names from all logs
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of field name objects with field name and count
      - "count": Number of unique field names
      - "error": Error message (if status is "error")
    
    **Example use cases:**
    1. "What fields are available in the logs?": '* | field_names'
    2. "Show fields in error logs": '_time:1h error | field_names'
    3. "What fields exist in nginx logs?": '{job="nginx"} _time:1h | field_names'
    """
    try:
        logger.info(f"Executing VictoriaLogs field names query: {query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if tenant is None:
            tenant = "0:0"
        
        logger.debug(f"Field names query parameters: start={start}, end={end}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/field_names", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs field names query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsFieldValuesInput)
def victorialogs_field_values(
    query: str,
    field: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: Optional[int] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Get unique values for a specific field from logs matching the query in VictoriaLogs.
    
    This tool enables the agent to discover what values exist for a specific field,
    which is critical for building accurate queries with valid field values.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Field Values API: https://docs.victoriametrics.com/victorialogs/querying/#querying-field-values
    
    **When to use this tool:**
    - To discover what values exist for a specific field
    - To find valid values for filtering (e.g., error levels, status codes)
    - To understand possible field values before building queries
    - To list all unique values in a field
    - To validate field values
    
    **When NOT to use this tool:**
    - To get log entries (use victorialogs_query instead)
    - To get field names (use victorialogs_field_names instead)
    - To get most frequent values (use victorialogs_facets instead)
    
    **Input requirements:**
    - query: LogsQL query to filter logs (required)
    - field: Field name to get values for (required, e.g., 'level', 'host', 'status_code')
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - limit: Maximum number of values to return (optional, default: 100)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of field value objects with value and count
      - "count": Number of unique values returned
      - "error": Error message (if status is "error")
    
    **Example use cases:**
    1. "What are the possible error levels?": field='level', query='_time:1h'
    2. "List all hosts": field='host', query='_time:1h'
    3. "What status codes exist?": field='status_code', query='_time:1h'
    4. "Get values for 'job' field in nginx logs": field='job', query='{job="nginx"} _time:1h'
    """
    try:
        logger.info(f"Executing VictoriaLogs field values query: field={field}, query={query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if limit is None:
            limit = 100
        if tenant is None:
            tenant = "0:0"
        
        logger.debug(f"Field values query parameters: field={field}, start={start}, end={end}, limit={limit}, tenant={tenant}")
        
        params = {
            "query": query,
            "field": field,
            "start": start,
            "end": end,
            "limit": limit,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/field_values", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs field values query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsStatsRangeInput)
def victorialogs_stats_range(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    step: Optional[str] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Execute a stats query over a time range in VictoriaLogs to get time-series statistics.
    
    This tool enables the agent to perform statistical analysis on log data over time,
    showing how statistics change across time buckets. It's designed for time-series
    aggregations, counts, averages, and other statistical computations over ranges.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Stats Query Range API: https://docs.victoriametrics.com/victorialogs/querying/#querying-log-range-stats
    
    **When to use this tool:**
    - To get statistics over a time range (not just a single point)
    - To analyze trends in log metrics over time
    - To calculate time-series aggregations (counts, averages, etc. per time bucket)
    - To track error rates, response times, or other metrics over time
    - To get statistics grouped by time periods
    
    **When NOT to use this tool:**
    - For single-point statistics (use victorialogs_stats instead)
    - To retrieve individual log entries (use victorialogs_query instead)
    - For simple time-series hits (use victorialogs_hits instead)
    - If the query doesn't include '| stats' clause
    
    **Input requirements:**
    - query: LogsQL query with '| stats' clause (required)
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - step: Time step for aggregation (optional, default: "1h")
      Examples: "1m", "5m", "1h", "1d"
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of stats result objects with time buckets
      - "count": Number of time buckets
      - "error": Error message (if status is "error")
    
    **Example use cases:**
    1. "Show error count trends over the last 24 hours": '_time:1d error | stats count()', step='1h'
    2. "Average response time per hour": '_time:1d | stats by (_time:1h) avg(response_time)'
    3. "Error rate over time": '_time:1h | stats by (_time:5m) count() logs, count() if (error) errors'
    """
    try:
        logger.info(f"Executing VictoriaLogs stats range query: {query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if not step:
            step = "1h"
        if tenant is None:
            tenant = "0:0"
        
        # Validate that query includes stats
        if '| stats' not in query.lower():
            error_msg = "Stats range query must include '| stats' clause. Example: '* | stats count()'"
            logger.warning(error_msg)
            return json.dumps({
                "status": "error",
                "error": error_msg
            }, indent=2)
        
        logger.debug(f"Stats range query parameters: start={start}, end={end}, step={step}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/stats_query_range", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs stats range query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsStreamsInput)
def victorialogs_streams(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: Optional[int] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Get log streams matching the query in VictoriaLogs.
    
    This tool enables the agent to discover available log streams (log sources),
    which helps understand what log sources are available for querying.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Streams API: https://docs.victoriametrics.com/victorialogs/querying/#querying-streams
    
    **When to use this tool:**
    - To discover available log streams (log sources)
    - To find streams matching specific criteria
    - To understand what log sources are available
    - To list streams for a specific application or service
    - To explore log stream structure
    
    **When NOT to use this tool:**
    - To get log entries (use victorialogs_query instead)
    - To get stream IDs only (use victorialogs_stream_ids instead)
    - To get field names (use victorialogs_field_names instead)
    
    **Input requirements:**
    - query: LogsQL query to filter streams (required)
      Use '*' to get all streams
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - limit: Maximum number of streams to return (optional, default: 100)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of stream objects with stream fields and counts
      - "count": Number of streams returned
      - "error": Error message (if status is "error")
    
    **Example use cases:**
    1. "What log streams are available?": '* | streams'
    2. "Show nginx streams": '{job="nginx"} | streams'
    3. "List streams from the last hour": '_time:1h | streams'
    """
    try:
        logger.info(f"Executing VictoriaLogs streams query: {query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if limit is None:
            limit = 100
        if tenant is None:
            tenant = "0:0"
        
        logger.debug(f"Streams query parameters: start={start}, end={end}, limit={limit}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "limit": limit,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/streams", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs streams query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsStreamIdsInput)
def victorialogs_stream_ids(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Get stream IDs (_stream_id values) for log streams matching the query in VictoriaLogs.
    
    This tool enables the agent to get stream IDs, which can be used for advanced
    stream filtering and identification.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Stream IDs API: https://docs.victoriametrics.com/victorialogs/querying/#querying-stream_ids
    
    **When to use this tool:**
    - To get stream IDs for filtering by specific streams
    - To identify unique log streams
    - To work with stream IDs in advanced queries
    
    **When NOT to use this tool:**
    - To get full stream information (use victorialogs_streams instead)
    - To get log entries (use victorialogs_query instead)
    
    **Input requirements:**
    - query: LogsQL query to filter streams (required)
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of stream ID objects with _stream_id and count
      - "count": Number of stream IDs returned
      - "error": Error message (if status is "error")
    """
    try:
        logger.info(f"Executing VictoriaLogs stream IDs query: {query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if tenant is None:
            tenant = "0:0"
        
        logger.debug(f"Stream IDs query parameters: start={start}, end={end}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/stream_ids", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs stream IDs query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsStreamFieldNamesInput)
def victorialogs_stream_field_names(
    query: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Get stream field names from log streams matching the query in VictoriaLogs.
    
    This tool enables the agent to discover field names specific to log streams,
    which helps understand the structure of stream fields.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Stream Field Names API: https://docs.victoriametrics.com/victorialogs/querying/#querying-stream-field-names
    
    **When to use this tool:**
    - To discover stream field names (fields in stream labels)
    - To understand stream structure
    - To find stream-specific fields
    
    **When NOT to use this tool:**
    - To get log field names (use victorialogs_field_names instead)
    - To get log entries (use victorialogs_query instead)
    
    **Input requirements:**
    - query: LogsQL query to filter streams (required)
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of stream field name objects with field name and count
      - "count": Number of unique stream field names
      - "error": Error message (if status is "error")
    """
    try:
        logger.info(f"Executing VictoriaLogs stream field names query: {query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if tenant is None:
            tenant = "0:0"
        
        logger.debug(f"Stream field names query parameters: start={start}, end={end}, tenant={tenant}")
        
        params = {
            "query": query,
            "start": start,
            "end": end,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/stream_field_names", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs stream field names query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsStreamFieldValuesInput)
def victorialogs_stream_field_values(
    query: str,
    field: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: Optional[int] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Get unique values for a specific stream field from log streams matching the query in VictoriaLogs.
    
    This tool enables the agent to discover what values exist for stream fields,
    which helps understand possible stream field values.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Stream Field Values API: https://docs.victoriametrics.com/victorialogs/querying/#querying-stream-field-values
    
    **When to use this tool:**
    - To discover stream field values (e.g., job names, instance names)
    - To find valid values for stream filtering
    - To understand possible stream field values
    
    **When NOT to use this tool:**
    - To get log field values (use victorialogs_field_values instead)
    - To get log entries (use victorialogs_query instead)
    
    **Input requirements:**
    - query: LogsQL query to filter streams (required)
    - field: Stream field name to get values for (required, e.g., 'job', 'instance')
    - start: ISO format timestamp (optional, defaults to 1 hour ago)
    - end: ISO format timestamp (optional, defaults to now)
    - limit: Maximum number of values to return (optional, default: 100)
    - tenant: Tenant ID in format "AccountID:ProjectID" (optional, default: "0:0")
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of stream field value objects with value and count
      - "count": Number of unique values returned
      - "error": Error message (if status is "error")
    """
    try:
        logger.info(f"Executing VictoriaLogs stream field values query: field={field}, query={query}")
        
        if not start or not end:
            start, end = _get_default_times()
            logger.debug(f"Using default time range: {start} to {end}")
        if limit is None:
            limit = 100
        if tenant is None:
            tenant = "0:0"
        
        logger.debug(f"Stream field values query parameters: field={field}, start={start}, end={end}, limit={limit}, tenant={tenant}")
        
        params = {
            "query": query,
            "field": field,
            "start": start,
            "end": end,
            "limit": limit,
            "tenant": tenant
        }
        
        result = _execute_query("/select/logsql/stream_field_values", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs stream field values query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


@tool(args_schema=VictoriaLogsTenantsInput)
def victorialogs_tenants(
    tenant: Optional[str] = None
) -> str:
    """
    Get list of available tenants in VictoriaLogs.
    
    This tool enables the agent to discover available tenants in multi-tenant
    VictoriaLogs deployments, which helps understand the tenant structure.
    
    References:
    - VictoriaLogs Querying: https://docs.victoriametrics.com/victorialogs/querying/
    - Tenants API: https://docs.victoriametrics.com/victorialogs/querying/#querying-tenants
    
    **When to use this tool:**
    - To discover available tenants
    - To list all tenants in the system
    - To understand multi-tenant structure
    - To validate tenant IDs
    
    **When NOT to use this tool:**
    - To query logs (use other victorialogs tools with tenant parameter)
    - If you already know the tenant ID
    
    **Input requirements:**
    - tenant: Optional tenant ID filter in format "AccountID:ProjectID" (optional)
      If not provided, returns all tenants
    
    **Output:**
    - JSON string containing:
      - "status": "success" or "error"
      - "data": List of tenant objects with tenant ID and metadata
      - "count": Number of tenants returned
      - "error": Error message (if status is "error")
    """
    try:
        logger.info(f"Executing VictoriaLogs tenants query: tenant={tenant}")
        
        params = {}
        if tenant:
            params["tenant"] = tenant
        
        result = _execute_query("/select/logsql/tenants", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_msg = f"Error executing VictoriaLogs tenants query: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "error": error_msg
        }, indent=2)


# Usage with LangChain Agent
if __name__ == "__main__":
    from langchain.agents import create_agent
    
    # Example usage
    tools = [
        victorialogs_query,
        victorialogs_stats,
        victorialogs_hits,
        victorialogs_facets,
        victorialogs_field_names,
        victorialogs_field_values,
        victorialogs_stats_range,
        victorialogs_streams,
        victorialogs_stream_ids,
        victorialogs_stream_field_names,
        victorialogs_stream_field_values,
        victorialogs_tenants
    ]
    
    print("VictoriaLogs tools initialized:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:100]}...")

