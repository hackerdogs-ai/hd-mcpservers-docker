"""
Tools API: list, search, get_tool_info, run_tool.
All endpoints wrapped for resiliency; exceptions mapped to HTTP responses.
"""
import time
from typing import Any, Optional

from fastapi import APIRouter, Query

from app.catalog import get_catalog, get_first_mcp_server_config, get_tool_by_id
from app.exceptions import (
    CatalogLoadError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError,
    ValidationError,
)
from app.logging_config import get_logger
from app.mcp_client import call_tool, list_tools_and_resources
from app.ocsf import build_tool_run_event

logger = get_logger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


def _search_tools(catalog: dict, q: str, category: Optional[str], vendor: Optional[str], limit: int, offset: int) -> tuple[list[dict], int]:
    """Simple in-memory search over name, description, search_terms, id."""
    tools = catalog.get("tools") or []
    q_lower = (q or "").strip().lower()
    if not q_lower:
        filtered = list(tools)
    else:
        filtered = []
        for t in tools:
            name = (t.get("name") or "").lower()
            desc = (t.get("description") or "").lower()
            terms = " ".join(t.get("search_terms") or []).lower()
            tid = (t.get("id") or "").lower()
            config = t.get("configuration") or {}
            servers = (config.get("mcpServers") or {}).keys()
            server_names = " ".join(s.lower() for s in servers)
            if q_lower in name or q_lower in desc or q_lower in terms or q_lower in tid or q_lower in server_names:
                filtered.append(t)
    if category:
        filtered = [t for t in filtered if (t.get("category") or "").lower() == category.lower()]
    if vendor:
        filtered = [t for t in filtered if (t.get("vendor") or "").lower() == vendor.lower()]
    total = len(filtered)
    return filtered[offset : offset + limit], total


@router.get("")
async def list_tools(
    active_only: bool = Query(True, alias="active_only"),
    category: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List all tools from catalog. Configuration passed as-is."""
    try:
        catalog = get_catalog()
        tools = catalog.get("tools") or []
        if active_only:
            tools = [t for t in tools if t.get("is_active", True)]
        if category:
            tools = [t for t in tools if (t.get("category") or "").lower() == category.lower()]
        if vendor:
            tools = [t for t in tools if (t.get("vendor") or "").lower() == vendor.lower()]
        total = len(tools)
        page = tools[offset : offset + limit]
        return {"tools": page, "total": total}
    except CatalogLoadError as e:
        logger.warning("list_tools_catalog_error", extra={"error": e.message})
        raise
    except Exception as e:
        logger.exception("list_tools_error", extra={"error": str(e)})
        raise


@router.get("/search")
async def search_tools(
    q: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Search tools by query string. Configuration passed as-is."""
    try:
        catalog = get_catalog()
        page, total = _search_tools(catalog, q, category, vendor, limit, offset)
        return {"tools": page, "total": total}
    except CatalogLoadError as e:
        logger.warning("search_tools_catalog_error", extra={"error": e.message})
        raise
    except Exception as e:
        logger.exception("search_tools_error", extra={"error": str(e)})
        raise


@router.get("/{tool_id}")
async def get_tool_info(tool_id: str) -> dict[str, Any]:
    """Return full tool info including MCP tools, resources, prompts. Configuration as-is."""
    try:
        tool = get_tool_by_id(tool_id)
        if not tool:
            raise ToolNotFoundError(f"Tool not found: {tool_id}", details={"tool_id": tool_id})
        pair = get_first_mcp_server_config(tool)
        if not pair:
            return {
                "tool_id": tool_id,
                "name": tool.get("name"),
                "description": tool.get("description"),
                "configuration": tool.get("configuration"),
                "tools": [],
                "resources": [],
                "prompts": [],
            }
        server_name, server_config = pair
        info = await list_tools_and_resources(server_name, server_config)
        return {
            "tool_id": tool_id,
            "name": tool.get("name"),
            "description": tool.get("description"),
            "configuration": tool.get("configuration"),
            "tools": info.get("tools", []),
            "resources": info.get("resources", []),
            "prompts": info.get("prompts", []),
        }
    except ToolNotFoundError:
        raise
    except (ToolExecutionError, ToolTimeoutError) as e:
        logger.warning("get_tool_info_execution_error", extra={"tool_id": tool_id, "error": e.message})
        raise
    except Exception as e:
        logger.exception("get_tool_info_error", extra={"tool_id": tool_id, "error": str(e)})
        raise


@router.post("/run")
async def run_tool(body: dict[str, Any]) -> dict[str, Any]:
    """
    Execute tool by name with arguments. Returns OCSF-formatted event.
    No LLM; direct MCP call_tool.
    """
    start = time.perf_counter()
    tool_id = body.get("tool_id")
    tool_name = body.get("tool_name")
    arguments = body.get("arguments")
    if not tool_id or not tool_name:
        raise ValidationError("tool_id and tool_name are required", details={"body": body})
    if arguments is not None and not isinstance(arguments, dict):
        raise ValidationError("arguments must be a JSON object", details={})

    try:
        tool = get_tool_by_id(tool_id)
        if not tool:
            raise ToolNotFoundError(f"Tool not found: {tool_id}", details={"tool_id": tool_id})
        pair = get_first_mcp_server_config(tool)
        if not pair:
            raise ToolExecutionError(f"Tool has no MCP server config: {tool_id}", details={"tool_id": tool_id})
        server_name, server_config = pair

        content, is_error = await call_tool(server_name, server_config, tool_name, arguments or {})
        duration_ms = int((time.perf_counter() - start) * 1000)
        ocsf = build_tool_run_event(
            tool_id=tool_id,
            tool_name=tool_name,
            arguments=arguments or {},
            result_content=content,
            is_error=is_error,
            error_message=None if not is_error else "Tool returned error content",
            duration_ms=duration_ms,
        )
        return ocsf
    except (ToolNotFoundError, ValidationError, ToolTimeoutError, ToolExecutionError):
        raise
    except Exception as e:
        logger.exception("run_tool_error", extra={"tool_id": tool_id, "tool_name": tool_name, "error": str(e)})
        raise
