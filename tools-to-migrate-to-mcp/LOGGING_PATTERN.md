# Tool Logging Pattern

This document describes the standardized logging pattern for all LangChain tools.

## Required Imports

```python
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import (
    mask_api_key, mask_sensitive_data, safe_log_debug, 
    safe_log_info, safe_log_error
)

# Initialize logger
logger = setup_logger(__name__, log_file_path="logs/tool_name.log")
```

## Standard Function Pattern

Every tool function should follow this pattern:

```python
@tool
def tool_function(runtime: ToolRuntime, param: str) -> str:
    """
    Tool documentation...
    """
    try:
        # 1. Log function entry
        safe_log_debug(logger, f"[tool_function] Starting execution", param=param)
        
        # 2. Get and mask API key
        api_key = runtime.state.get("api_keys", {}).get("API_KEY")
        masked_key = mask_api_key(api_key) if api_key else "[NO_API_KEY]"
        safe_log_debug(logger, f"[tool_function] API key retrieved", api_key_masked=masked_key)
        
        # 3. Validate API key
        if not api_key:
            error_msg = "API key not found in agent state..."
            safe_log_error(logger, f"[tool_function] {error_msg}")
            return json.dumps({
                "status": "error",
                "message": error_msg
            })

        # 4. Prepare request
        endpoint = "..."
        headers = {...}
        safe_log_info(logger, f"[tool_function] Making API request", 
                     endpoint=endpoint, param=param, api_key_masked=masked_key)

        # 5. Make request
        response = requests.get/post(endpoint, headers=headers, timeout=30)
        safe_log_debug(logger, f"[tool_function] API response received", 
                      status_code=response.status_code)

        # 6. Handle response codes
        if response.status_code == 401:
            error_msg = "Invalid API key..."
            safe_log_error(logger, f"[tool_function] {error_msg}", 
                         status_code=401, api_key_masked=masked_key)
            return json.dumps({"status": "error", "message": error_msg})
        # ... other status codes

        # 7. Parse response with error handling
        try:
            data = response.json()
            # ... process data
            safe_log_debug(logger, f"[tool_function] Parsing response data", 
                         data=mask_sensitive_data(data))
            
            result = {...}
            safe_log_info(logger, f"[tool_function] Successfully completed", 
                         result_summary=...)
            return json.dumps(result, indent=2)
            
        except (KeyError, ValueError, json.JSONDecodeError) as parse_error:
            error_msg = f"Error parsing API response: {str(parse_error)}"
            safe_log_error(logger, f"[tool_function] {error_msg}", exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})

    # 8. Exception handling (comprehensive)
    except requests.exceptions.Timeout as timeout_error:
        error_msg = "Request timeout..."
        safe_log_error(logger, f"[tool_function] {error_msg}", exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})
    except requests.exceptions.RequestException as request_error:
        error_msg = f"Request error: {str(request_error)}"
        safe_log_error(logger, f"[tool_function] {error_msg}", exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        safe_log_error(logger, f"[tool_function] {error_msg}", exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})
```

## Key Principles

1. **Never crash**: All exceptions must be caught and return error JSON
2. **Mask API keys**: Always use `mask_api_key()` before logging
3. **Comprehensive logging**: Debug at entry/exit, info for operations, error for failures
4. **Exception details**: Use `exc_info=True` for error logging
5. **Mask sensitive data**: Use `mask_sensitive_data()` for any data structures

## API Key Masking

- Always mask API keys: `masked_key = mask_api_key(api_key)`
- Log masked version: `api_key_masked=masked_key`
- Never log raw API keys

