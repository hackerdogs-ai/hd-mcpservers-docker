"""
OCSF (Open Cybersecurity Schema Framework) response builder for run_tool.
PRD: return tool execution result in standardized OCSF format. Use existing library where possible.
We build an OCSF-compliant dict (API Activity 6003) with tool output in raw_data/unmapped.
"""
import time
from typing import Any

# OCSF class_uid: 6003 = API Activity; activity_id 1 = Read
CATEGORY_UID = 6  # Application Activity
CLASS_UID = 6003  # API Activity
ACTIVITY_ID = 1   # Read
SEVERITY_ID = 1   # Informational
STATUS_ID = 1     # Success


def build_tool_run_event(
    tool_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    result_content: list[dict[str, Any]] | str,
    is_error: bool = False,
    error_message: str | None = None,
    duration_ms: int | None = None,
) -> dict[str, Any]:
    """
    Build an OCSF API Activity (6003) event for a tool run.
    Puts tool_id, tool_name, arguments, and result in unmapped for downstream use.
    """
    now_ms = int(time.time() * 1000)
    return {
        "metadata": {
            "product": {"name": "ToolsWebService", "vendor_name": "Hackerdogs"},
            "version": "1.0",
            "correlation_uid": f"tool-run-{tool_id}-{now_ms}",
        },
        "category_uid": CATEGORY_UID,
        "category_name": "Application Activity",
        "class_uid": CLASS_UID,
        "class_name": "API Activity",
        "activity_id": ACTIVITY_ID,
        "activity_name": "Read",
        "time": now_ms,
        "severity_id": 6 if is_error else SEVERITY_ID,
        "severity": "Fatal" if is_error else "Informational",
        "status_id": 2 if is_error else STATUS_ID,
        "status": "Failure" if is_error else "Success",
        "message": error_message if is_error else f"Tool {tool_name} executed successfully",
        "duration": duration_ms,
        "unmapped": {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "result_content": result_content,
            "is_error": is_error,
        },
    }
