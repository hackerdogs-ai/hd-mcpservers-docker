"""
Integration-ish tests for Mermaid + Graphviz LangChain tools.

These tests are intentionally implemented as an executable script (not pytest-only),
since many environments running Hackerdogs execute ad-hoc validation scripts.

It validates:
- input modes: file path, file:// URL, raw content string
- output modes: svg, png

Notes:
- Mermaid rendering requires `mermaid-cli` and Playwright Chromium installed:
    pip install mermaid-cli
    playwright install chromium
- Graphviz rendering requires the `dot` binary available on PATH.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure repo root is importable so `shared.*` imports work when running as a script
# This file lives at: <repo>/shared/modules/tools/tests/<this_file>
# parents[0]=tests, [1]=tools, [2]=modules, [3]=shared, [4]=<repo>
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.modules.tools.mermaid_langchain import mermaid_render_diagram
from shared.modules.tools.graphviz_dot_langchain import graphviz_render_dot


ROOT = REPO_ROOT


def _dummy_runtime():
    # Tool functions only need .state for logging/user_id in most cases.
    return SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})

def _call_tool(tool_obj, **kwargs) -> str:
    """
    Call a LangChain @tool-decorated object in a stable way.

    In LangChain, @tool returns a Tool/StructuredTool object, not a raw callable function.
    For functional tests we call the underlying python function via `.func` when present.
    """
    fn = getattr(tool_obj, "func", None)
    if callable(fn):
        return fn(**kwargs)
    # fallback: try invoke() contract
    inv = getattr(tool_obj, "invoke", None)
    if callable(inv):
        return inv(kwargs)
    raise TypeError(f"Unsupported tool object type: {type(tool_obj).__name__}")


def _assert_success(resp_json: str) -> dict:
    data = json.loads(resp_json)
    assert data.get("status") == "success", f"Expected success, got: {data}"
    assert data.get("image_base64"), "Missing image_base64"
    return data


def _assert_svg(data: dict):
    raw = base64.b64decode(data["image_base64"])
    # SVG may start with XML prolog
    trimmed = raw.lstrip()
    assert (trimmed.startswith(b"<svg") or trimmed.startswith(b"<?xml")) and b"<svg" in trimmed, (
        "SVG output does not contain <svg tag"
    )


def _assert_png(data: dict):
    raw = base64.b64decode(data["image_base64"])
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "PNG signature mismatch"


def test_mermaid_all_modes():
    runtime = _dummy_runtime()
    mmd_file = ROOT / "mermaid" / "transparent_hackerdogs_light.mmd"
    assert mmd_file.exists(), f"Missing test mermaid file: {mmd_file}"

    # file -> svg
    r1 = _call_tool(
        mermaid_render_diagram,
        runtime=runtime,
        input_file=str(mmd_file),
        output_format="svg",
        theme="dark",
        background_color="transparent",
    )
    d1 = _assert_success(r1)
    _assert_svg(d1)

    # file:// url -> png
    r2 = _call_tool(
        mermaid_render_diagram,
        runtime=runtime,
        input_url=mmd_file.as_uri(),
        output_format="png",
        theme="dark",
        background_color="transparent",
    )
    d2 = _assert_success(r2)
    _assert_png(d2)

    # content -> svg
    content = mmd_file.read_text(encoding="utf-8", errors="replace")
    r3 = _call_tool(
        mermaid_render_diagram,
        runtime=runtime,
        content=content,
        output_format="svg",
        theme="dark",
        background_color="transparent",
    )
    d3 = _assert_success(r3)
    _assert_svg(d3)


def test_graphviz_all_modes():
    runtime = _dummy_runtime()
    dot_file = ROOT / "mermaid" / "dot" / "03_microservices_architecture.dot"
    assert dot_file.exists(), f"Missing test dot file: {dot_file}"

    # file -> svg
    r1 = _call_tool(graphviz_render_dot, runtime=runtime, input_file=str(dot_file), output_format="svg", theme="dark")
    d1 = _assert_success(r1)
    _assert_svg(d1)

    # file:// url -> png
    r2 = _call_tool(graphviz_render_dot, runtime=runtime, input_url=dot_file.as_uri(), output_format="png", theme="dark")
    d2 = _assert_success(r2)
    _assert_png(d2)

    # content -> svg
    content = dot_file.read_text(encoding="utf-8", errors="replace")
    r3 = _call_tool(graphviz_render_dot, runtime=runtime, content=content, output_format="svg", theme="light")
    d3 = _assert_success(r3)
    _assert_svg(d3)


def main() -> int:
    test_mermaid_all_modes()
    test_graphviz_all_modes()
    print("OK: Mermaid + Graphviz LangChain tools validated (file/url/content + svg/png).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


