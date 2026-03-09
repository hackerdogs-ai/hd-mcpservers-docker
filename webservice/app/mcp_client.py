"""
MCP client: connect to tool via stdio (docker/npx/uvx), list tools, call tool.
PRD: get_tool_info and run_tool use MCP client; no LLM. Timeouts enforced.
"""
import asyncio
import os
from datetime import timedelta
from typing import Any, Optional

from app.config import get_settings
from app.exceptions import ToolExecutionError, ToolTimeoutError
from app.logging_config import get_logger

logger = get_logger(__name__)

# Lazy import MCP to avoid startup failure if not installed
def _stdio_client():
    from mcp.client.stdio import stdio_client
    return stdio_client


def _stdio_server_params():
    from mcp.client.stdio import StdioServerParameters
    return StdioServerParameters


def _client_session():
    from mcp import ClientSession
    return ClientSession


def _build_env(server_env: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Merge server env with process env so npx/uvx/docker are found."""
    env = os.environ.copy()
    if server_env:
        env.update(server_env)
    return env


def _server_params_from_config(server_name: str, server_config: dict[str, Any]) -> Any:
    """Build StdioServerParameters from tool.configuration.mcpServers[name]."""
    StdioServerParameters = _stdio_server_params()
    command = server_config.get("command") or "docker"
    args = server_config.get("args") or []
    env = server_config.get("env")
    return StdioServerParameters(
        command=command,
        args=list(args),
        env=_build_env(env) if env else None,
    )


async def list_tools_and_resources(
    server_name: str,
    server_config: dict[str, Any],
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """
    Connect to MCP server via stdio, return tools list, resources, prompts.
    Raises ToolExecutionError or ToolTimeoutError on failure.
    """
    timeout_seconds = timeout_seconds or get_settings().tool_run_timeout_seconds
    stdio_client = _stdio_client()
    ClientSession = _client_session()
    params = _server_params_from_config(server_name, server_config)

    async def _run() -> dict[str, Any]:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                tools_result = await session.list_tools()
                tools = [{"name": t.name, "description": getattr(t, "description", None) or "", "input_schema": getattr(t, "inputSchema", None)} for t in tools_result.tools]
                resources: list[dict] = []
                try:
                    res = await session.list_resources()
                    resources = [{"uri": r.uri, "name": getattr(r, "name", None), "description": getattr(r, "description", None)} for r in res.resources]
                except Exception as e:
                    logger.debug("list_resources_not_supported", extra={"server": server_name, "error": str(e)})
                prompts: list[dict] = []
                try:
                    pr = await session.list_prompts()
                    prompts = [{"name": p.name, "description": getattr(p, "description", None)} for p in pr.prompts]
                except Exception as e:
                    logger.debug("list_prompts_not_supported", extra={"server": server_name, "error": str(e)})
                return {"tools": tools, "resources": resources, "prompts": prompts}

    try:
        return await asyncio.wait_for(_run(), timeout=timeout_seconds)
    except asyncio.TimeoutError as e:
        logger.error("mcp_list_tools_timeout", extra={"server": server_name, "timeout": timeout_seconds})
        raise ToolTimeoutError(f"MCP server did not respond within {timeout_seconds}s", details={"server": server_name}) from e
    except Exception as e:
        logger.exception("mcp_list_tools_failed", extra={"server": server_name, "error": str(e)})
        raise ToolExecutionError(f"MCP connection failed: {e}", details={"server": server_name}) from e


async def call_tool(
    server_name: str,
    server_config: dict[str, Any],
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    timeout_seconds: float | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """
    Call MCP tool by name with given arguments. Returns (content_blocks, is_error).
    """
    timeout_seconds = timeout_seconds or get_settings().tool_run_timeout_seconds
    stdio_client = _stdio_client()
    ClientSession = _client_session()
    params = _server_params_from_config(server_name, server_config)

    async def _run() -> tuple[list[dict[str, Any]], bool]:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                result = await session.call_tool(tool_name, arguments or {}, read_timeout_seconds=timedelta(seconds=min(60, int(timeout_seconds))))
                is_error = getattr(result, "isError", False) or (hasattr(result, "content") and any(getattr(c, "type", "") == "error" for c in (result.content or [])))
                content = getattr(result, "content", []) or []
                out = []
                for c in content:
                    if hasattr(c, "model_dump"):
                        out.append(c.model_dump())
                    elif isinstance(c, dict):
                        out.append(c)
                    else:
                        out.append({"type": getattr(c, "type", "text"), "text": getattr(c, "text", str(c))})
                return out, bool(is_error)

    try:
        return await asyncio.wait_for(_run(), timeout=timeout_seconds)
    except asyncio.TimeoutError as e:
        logger.error("mcp_call_tool_timeout", extra={"server": server_name, "tool": tool_name, "timeout": timeout_seconds})
        raise ToolTimeoutError(f"Tool execution did not complete within {timeout_seconds}s", details={"tool": tool_name}) from e
    except Exception as e:
        logger.exception("mcp_call_tool_failed", extra={"server": server_name, "tool": tool_name, "error": str(e)})
        raise ToolExecutionError(f"Tool execution failed: {e}", details={"tool": tool_name}) from e
