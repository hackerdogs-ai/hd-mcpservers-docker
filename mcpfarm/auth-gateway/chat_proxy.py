"""
Server-side, single-turn LLM proxy for the Chat page and per-server Chat tab.

The browser keeps the agentic loop and MCP tool execution; it calls this proxy
for each LLM turn so provider API keys stay encrypted server-side and never
touch the browser. This mirrors the provider handling in
``mcpfarm-ui/src/lib/llm.js`` but reads keys from ``secrets_vault``.

Normalized request::

    {
      "provider": "claude",
      "model": "claude-sonnet-4-...",
      "messages": [ {role, content, toolCalls?, tool_call_id?, tool_use_id?} ],
      "tools": [ {name, description, inputSchema} ],
      "max_tokens": 4096
    }

Normalized response::

    { "content": "...", "toolCalls": [ {id, name, arguments} ] }
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

import httpx

import secrets_vault

logger = logging.getLogger(__name__)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434").rstrip("/")

DEFAULT_MODELS = {
    "ollama": "qwen3-coder:latest",
    "claude": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "bedrock": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "azure": "gpt-4o",
    "openrouter": "anthropic/claude-sonnet-4",
    "grok": "grok-3",
    "gemini": "gemini-2.5-flash",
}

TOOL_FORMAT = {
    "ollama": "ollama",
    "claude": "claude",
    "openai": "openai",
    "bedrock": "openai",
    "azure": "openai",
    "openrouter": "openai",
    "grok": "openai",
    "gemini": "openai",
}


class ChatProxyError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# ---------------------------------------------------------------------------
# Tool schema conversion
# ---------------------------------------------------------------------------

def _tool_to_openai(tool: Dict) -> Dict:
    return {
        "type": "function",
        "function": {
            "name": tool.get("name"),
            "description": tool.get("description") or "",
            "parameters": tool.get("inputSchema") or {"type": "object", "properties": {}},
        },
    }


def _tool_to_claude(tool: Dict) -> Dict:
    return {
        "name": tool.get("name"),
        "description": tool.get("description") or "",
        "input_schema": tool.get("inputSchema") or {"type": "object", "properties": {}},
    }


# ---------------------------------------------------------------------------
# Message conversion
# ---------------------------------------------------------------------------

def _messages_to_openai(messages: List[Dict]) -> List[Dict]:
    out = []
    for m in messages:
        role = m.get("role")
        if role == "tool":
            out.append({
                "role": "tool",
                "tool_call_id": m.get("tool_call_id") or "call_0",
                "content": m.get("content") or "",
            })
        elif m.get("toolCalls"):
            out.append({
                "role": "assistant",
                "content": m.get("content") or None,
                "tool_calls": [
                    {
                        "id": tc.get("id") or f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": tc.get("name"),
                            "arguments": json.dumps(tc.get("arguments") or {}),
                        },
                    }
                    for i, tc in enumerate(m["toolCalls"])
                ],
            })
        else:
            out.append({"role": role, "content": m.get("content") or ""})
    return out


def _messages_to_ollama(messages: List[Dict]) -> List[Dict]:
    """Ollama's /api/chat is OpenAI-ish but expects tool-call ``arguments`` as a
    JSON object (not a stringified JSON like the OpenAI spec), and rejects a
    null assistant ``content``.
    """
    out = []
    for m in messages:
        role = m.get("role")
        if role == "tool":
            entry = {"role": "tool", "content": m.get("content") or ""}
            if m.get("name"):
                entry["tool_name"] = m["name"]
            out.append(entry)
        elif m.get("toolCalls"):
            out.append({
                "role": "assistant",
                "content": m.get("content") or "",
                "tool_calls": [
                    {"function": {"name": tc.get("name"), "arguments": tc.get("arguments") or {}}}
                    for tc in m["toolCalls"]
                ],
            })
        else:
            out.append({"role": role, "content": m.get("content") or ""})
    return out


def _messages_to_claude(messages: List[Dict]):
    claude_messages = []
    system = None
    for m in messages:
        role = m.get("role")
        if role == "system":
            system = m.get("content")
            continue
        if role == "tool":
            claude_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_use_id") or "call_0",
                    "content": m.get("content") or "",
                }],
            })
        elif m.get("toolCalls"):
            content = []
            if m.get("content"):
                content.append({"type": "text", "text": m["content"]})
            for i, tc in enumerate(m["toolCalls"]):
                content.append({
                    "type": "tool_use",
                    "id": tc.get("id") or f"call_{i}",
                    "name": tc.get("name"),
                    "input": tc.get("arguments") or {},
                })
            claude_messages.append({"role": "assistant", "content": content})
        else:
            claude_messages.append({"role": role, "content": m.get("content") or ""})
    return claude_messages, system


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_openai_response(data: Dict, label: str) -> Dict:
    choice = (data.get("choices") or [{}])[0].get("message")
    if not choice:
        raise ChatProxyError(502, f"{label}: empty response")
    tool_calls = choice.get("tool_calls") or []
    if tool_calls:
        parsed = []
        for tc in tool_calls:
            fn = tc.get("function") or {}
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            parsed.append({"id": tc.get("id"), "name": fn.get("name"), "arguments": args})
        return {"content": choice.get("content") or "", "toolCalls": parsed}
    return {"content": choice.get("content") or "", "toolCalls": []}


def _parse_claude_response(data: Dict) -> Dict:
    blocks = data.get("content") or []
    tool_uses = [b for b in blocks if b.get("type") == "tool_use"]
    text = "\n".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    if tool_uses:
        return {
            "content": text,
            "toolCalls": [
                {"id": b.get("id"), "name": b.get("name"), "arguments": b.get("input") or {}}
                for b in tool_uses
            ],
        }
    return {"content": text, "toolCalls": []}


# ---------------------------------------------------------------------------
# Provider calls
# ---------------------------------------------------------------------------

async def _post_json(url: str, headers: Dict, body: Dict, label: str, timeout: float = 120.0) -> Dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=body)
    if resp.status_code >= 400:
        raise ChatProxyError(resp.status_code, f"{label} {resp.status_code}: {resp.text[:500]}")
    return resp.json()


async def _require_key(provider: str) -> str:
    key = await secrets_vault.get_secret(provider)
    if not key:
        raise ChatProxyError(400, f"No API key configured for '{provider}'. Add it in Settings.")
    return key


async def _call_openai_compatible(url, headers, req, label) -> Dict:
    body = {
        "model": req.get("model") or DEFAULT_MODELS.get(req["provider"]),
        "messages": _messages_to_openai(req["messages"]),
    }
    if req.get("tools"):
        body["tools"] = [_tool_to_openai(t) for t in req["tools"]]
    data = await _post_json(url, {"Content-Type": "application/json", **headers}, body, label)
    return _parse_openai_response(data, label)


async def _call_claude(req) -> Dict:
    key = await _require_key("claude")
    messages, system = _messages_to_claude(req["messages"])
    body = {
        "model": req.get("model") or DEFAULT_MODELS["claude"],
        "max_tokens": req.get("max_tokens") or 4096,
        "messages": messages,
    }
    if system:
        body["system"] = system
    if req.get("tools"):
        body["tools"] = [_tool_to_claude(t) for t in req["tools"]]
    data = await _post_json(
        "https://api.anthropic.com/v1/messages",
        {"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
        body, "Claude",
    )
    return _parse_claude_response(data)


async def _call_openai(req) -> Dict:
    key = await _require_key("openai")
    return await _call_openai_compatible(
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {key}"}, req, "OpenAI",
    )


async def _call_bedrock(req) -> Dict:
    key = await _require_key("bedrock")
    region = os.environ.get("BEDROCK_REGION", "us-east-1")
    return await _call_openai_compatible(
        f"https://bedrock-runtime.{region}.amazonaws.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {key}"}, req, "AWS Bedrock",
    )


async def _call_azure(req) -> Dict:
    key = await _require_key("azure")
    endpoint = (os.environ.get("AZURE_OPENAI_ENDPOINT", "")).rstrip("/")
    if not endpoint:
        raise ChatProxyError(400, "AZURE_OPENAI_ENDPOINT not configured on the server")
    deployment = req.get("model") or DEFAULT_MODELS["azure"]
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    return await _call_openai_compatible(url, {"api-key": key}, req, "Azure OpenAI")


async def _call_openrouter(req) -> Dict:
    key = await _require_key("openrouter")
    return await _call_openai_compatible(
        "https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {key}", "X-Title": "Hackerdogs MCP Farm"}, req, "OpenRouter",
    )


async def _call_grok(req) -> Dict:
    key = await _require_key("grok")
    return await _call_openai_compatible(
        "https://api.x.ai/v1/chat/completions",
        {"Authorization": f"Bearer {key}"}, req, "Grok",
    )


async def _call_gemini(req) -> Dict:
    key = await _require_key("gemini")
    return await _call_openai_compatible(
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        {"Authorization": f"Bearer {key}"}, req, "Google Gemini",
    )


async def _call_ollama(req) -> Dict:
    body = {
        "model": req.get("model") or DEFAULT_MODELS["ollama"],
        "messages": _messages_to_ollama(req["messages"]),
        "stream": False,
    }
    if req.get("tools"):
        body["tools"] = [_tool_to_openai(t) for t in req["tools"]]
    data = await _post_json(f"{OLLAMA_URL}/api/chat", {"Content-Type": "application/json"}, body, "Ollama")
    msg = data.get("message") or {}
    tool_calls = msg.get("tool_calls") or []
    if tool_calls:
        return {
            "content": msg.get("content") or "",
            "toolCalls": [
                {"id": tc.get("id"), "name": (tc.get("function") or {}).get("name"),
                 "arguments": (tc.get("function") or {}).get("arguments") or {}}
                for tc in tool_calls
            ],
        }
    return {"content": msg.get("content") or "", "toolCalls": []}


_DISPATCH = {
    "ollama": _call_ollama,
    "claude": _call_claude,
    "openai": _call_openai,
    "bedrock": _call_bedrock,
    "azure": _call_azure,
    "openrouter": _call_openrouter,
    "grok": _call_grok,
    "gemini": _call_gemini,
}


async def run_completion(req: Dict) -> Dict:
    provider = (req.get("provider") or "").lower()
    handler = _DISPATCH.get(provider)
    if not handler:
        raise ChatProxyError(400, f"Unknown provider: {provider}")
    req["provider"] = provider
    req.setdefault("messages", [])
    req.setdefault("tools", [])
    return await handler(req)
