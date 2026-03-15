"""
Tool Logging Utility

This module provides standardized logging utilities for all LangChain tools with:
- Comprehensive exception handling
- API key masking
- Debug, info, and error logging
- Safe execution wrappers

All tools should use this module to ensure consistent logging and prevent crashes.
"""

import re
from typing import Any, Dict, Optional, Callable
from functools import wraps
from hd_logging import setup_logger

# Initialize logger for this module
_logger = setup_logger(__name__, log_file_path="logs/tool_logging.log")


def mask_api_key(api_key: Optional[str], show_chars: int = 4) -> str:
    """
    Mask an API key for safe logging.
    
    Args:
        api_key: The API key to mask (can be None)
        show_chars: Number of characters to show at start and end (default: 4)
    
    Returns:
        Masked API key string (e.g., "3956...b11c" or "[NO_API_KEY]")
    """
    if not api_key:
        return "[NO_API_KEY]"
    
    if len(api_key) <= show_chars * 2:
        # If key is too short, mask completely
        return "[MASKED_API_KEY]"
    
    return f"{api_key[:show_chars]}...{api_key[-show_chars:]}"


def mask_sensitive_data(data: Any, show_chars: int = 4) -> Any:
    """
    Recursively mask sensitive data in dictionaries, lists, and strings.
    
    Args:
        data: Data structure to mask (dict, list, str, etc.)
        show_chars: Number of characters to show for masked values
    
    Returns:
        Data structure with sensitive fields masked
    """
    if data is None:
        return None
    
    # Mask strings that look like API keys
    if isinstance(data, str):
        # Check if it looks like an API key (long alphanumeric string)
        if len(data) > 20 and re.match(r'^[a-zA-Z0-9]+$', data):
            return mask_api_key(data, show_chars)
        return data
    
    # Mask dictionaries
    if isinstance(data, dict):
        masked = {}
        sensitive_keys = ['api_key', 'API_KEY', 'apiKey', 'apikey', 'key', 'token', 
                         'password', 'secret', 'credential', 'auth', 'authorization']
        
        for key, value in data.items():
            key_lower = str(key).lower()
            # Check if key contains sensitive terms
            if any(sensitive_term in key_lower for sensitive_term in sensitive_keys):
                masked[key] = mask_api_key(str(value), show_chars) if isinstance(value, str) else "[MASKED]"
            elif isinstance(value, (dict, list)):
                masked[key] = mask_sensitive_data(value, show_chars)
            else:
                masked[key] = value
        return masked
    
    # Mask lists
    if isinstance(data, list):
        return [mask_sensitive_data(item, show_chars) for item in data]
    
    return data


def safe_log_debug(logger, message: str, **kwargs):
    """Safely log debug message with exception handling."""
    try:
        # Mask any sensitive data in kwargs
        safe_kwargs = mask_sensitive_data(kwargs) if kwargs else {}
        
        # Format message with context data (Python logging doesn't accept arbitrary kwargs)
        # Only exc_info, extra, and stack_info are valid logging kwargs
        if safe_kwargs:
            # Format kwargs as key=value pairs in the message string
            context_parts = []
            for k, v in safe_kwargs.items():
                # Handle complex types
                if isinstance(v, dict):
                    context_parts.append(f"{k}=<dict with {len(v)} keys>")
                elif isinstance(v, list):
                    context_parts.append(f"{k}=<list with {len(v)} items>")
                else:
                    context_parts.append(f"{k}={v}")
            context_str = ", ".join(context_parts)
            formatted_message = f"{message} | {context_str}"
        else:
            formatted_message = message
        
        logger.debug(formatted_message)
    except Exception as e:
        _logger.error(f"Error in safe_log_debug: {str(e)}", exc_info=True)


def safe_log_info(logger, message: str, **kwargs):
    """Safely log info message with exception handling."""
    try:
        # Mask any sensitive data in kwargs
        safe_kwargs = mask_sensitive_data(kwargs) if kwargs else {}
        
        # Format message with context data (Python logging doesn't accept arbitrary kwargs)
        if safe_kwargs:
            # Format kwargs as key=value pairs in the message string
            context_parts = []
            for k, v in safe_kwargs.items():
                # Handle complex types
                if isinstance(v, dict):
                    context_parts.append(f"{k}=<dict with {len(v)} keys>")
                elif isinstance(v, list):
                    context_parts.append(f"{k}=<list with {len(v)} items>")
                else:
                    context_parts.append(f"{k}={v}")
            context_str = ", ".join(context_parts)
            formatted_message = f"{message} | {context_str}"
        else:
            formatted_message = message
        
        logger.info(formatted_message)
    except Exception as e:
        _logger.error(f"Error in safe_log_info: {str(e)}", exc_info=True)


def safe_log_error(logger, message: str, exc_info: bool = True, **kwargs):
    """Safely log error message with exception handling."""
    try:
        # Mask any sensitive data in kwargs
        safe_kwargs = mask_sensitive_data(kwargs) if kwargs else {}
        
        # Format message with context data (Python logging doesn't accept arbitrary kwargs)
        # Only exc_info, extra, and stack_info are valid logging kwargs
        if safe_kwargs:
            # Format kwargs as key=value pairs in the message string
            context_parts = []
            for k, v in safe_kwargs.items():
                # Handle complex types
                if isinstance(v, dict):
                    context_parts.append(f"{k}=<dict with {len(v)} keys>")
                elif isinstance(v, list):
                    context_parts.append(f"{k}=<list with {len(v)} items>")
                else:
                    context_parts.append(f"{k}={v}")
            context_str = ", ".join(context_parts)
            formatted_message = f"{message} | {context_str}"
        else:
            formatted_message = message
        
        logger.error(formatted_message, exc_info=exc_info)
    except Exception as e:
        _logger.error(f"Error in safe_log_error: {str(e)}", exc_info=True)


def safe_tool_execution(tool_name: str, logger=None):
    """
    Decorator to wrap tool execution with comprehensive exception handling and logging.
    
    This ensures no tool can crash the application.
    
    Args:
        tool_name: Name of the tool for logging
        logger: Logger instance (if None, creates one)
    
    Usage:
        @safe_tool_execution("my_tool", logger)
        def my_tool_function(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided logger or create one
            tool_logger = logger or setup_logger(f"tool_{tool_name}", log_file_path=f"logs/{tool_name}.log")
            
            # Mask sensitive kwargs before logging
            safe_kwargs = mask_sensitive_data(kwargs) if kwargs else {}
            
            try:
                tool_logger.debug(f"[{tool_name}] Starting execution", extra=safe_kwargs)
                
                # Execute the function
                result = func(*args, **kwargs)
                
                tool_logger.info(f"[{tool_name}] Execution completed successfully")
                return result
                
            except ValueError as ve:
                error_msg = f"[{tool_name}] Validation error: {str(ve)}"
                tool_logger.error(error_msg, exc_info=True)
                # Return error response instead of crashing
                return json.dumps({
                    "status": "error",
                    "message": f"Validation error: {str(ve)}",
                    "tool": tool_name
                })
                
            except KeyError as ke:
                error_msg = f"[{tool_name}] Missing required parameter: {str(ke)}"
                tool_logger.error(error_msg, exc_info=True)
                return json.dumps({
                    "status": "error",
                    "message": f"Missing required parameter: {str(ke)}",
                    "tool": tool_name
                })
                
            except requests.exceptions.Timeout as te:
                error_msg = f"[{tool_name}] Request timeout: {str(te)}"
                tool_logger.error(error_msg, exc_info=True)
                return json.dumps({
                    "status": "error",
                    "message": f"Request timeout: {str(te)}",
                    "tool": tool_name
                })
                
            except requests.exceptions.RequestException as re:
                error_msg = f"[{tool_name}] Request error: {str(re)}"
                tool_logger.error(error_msg, exc_info=True)
                return json.dumps({
                    "status": "error",
                    "message": f"Request error: {str(re)}",
                    "tool": tool_name
                })
                
            except ImportError as ie:
                error_msg = f"[{tool_name}] Import error: {str(ie)}"
                tool_logger.error(error_msg, exc_info=True)
                return json.dumps({
                    "status": "error",
                    "message": f"Import error: {str(ie)}",
                    "tool": tool_name
                })
                
            except Exception as e:
                error_msg = f"[{tool_name}] Unexpected error: {str(e)}"
                tool_logger.error(error_msg, exc_info=True)
                # Return error response instead of crashing
                return json.dumps({
                    "status": "error",
                    "message": f"Unexpected error: {str(e)}",
                    "tool": tool_name
                })
        
        return wrapper
    return decorator


# Import json for error responses
import json
import requests

