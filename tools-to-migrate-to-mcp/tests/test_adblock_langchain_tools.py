"""
Functional-ish test for AdBlock LangChain tool.

This is implemented as an executable script (similar to other tools tests).
It uses a small local ABP-style blocklist via file:// to avoid network.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Ensure repo root is importable so `shared.*` imports work when running as a script
# This file lives at: <repo>/shared/modules/tools/tests/<this_file>
# parents[0]=tests, [1]=tools, [2]=modules, [3]=shared, [4]=<repo>
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.modules.tools.osint.adblock_langchain import adblock_check_url


def _dummy_runtime():
    return SimpleNamespace(state={"user_id": "test_user", "environment_variables": {}, "api_keys": {}})


def _call_tool(tool_obj, **kwargs) -> str:
    fn = getattr(tool_obj, "func", None)
    if callable(fn):
        return fn(**kwargs)
    inv = getattr(tool_obj, "invoke", None)
    if callable(inv):
        return inv(kwargs)
    raise TypeError(f"Unsupported tool object type: {type(tool_obj).__name__}")


def test_adblock_offline_blocklist():
    runtime = _dummy_runtime()
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # Very small ABP-style list:
        # - block any URL containing /ads/
        # - allowlist an exception for example.com/ads/ok
        blocklist = d / "list.txt"
        blocklist.write_text(
            """
! Title: TestList
||example.com/ads/
@@||example.com/ads/ok
""".lstrip(),
            encoding="utf-8",
        )

        url_blocked = "https://example.com/ads/bad.js"
        url_allowed = "https://example.com/ads/ok"

        r1 = _call_tool(
            adblock_check_url,
            runtime=runtime,
            url=url_blocked,
            third_party=True,
            resource_type="script",
            blocklist_url=f"file://{blocklist}",
            timeout_seconds=5,
        )
        d1 = json.loads(r1)
        assert d1.get("status") == "ok", d1
        assert d1.get("blocked") is True, d1

        r2 = _call_tool(
            adblock_check_url,
            runtime=runtime,
            url=url_allowed,
            third_party=True,
            resource_type="script",
            blocklist_url=f"file://{blocklist}",
            timeout_seconds=5,
        )
        d2 = json.loads(r2)
        assert d2.get("status") == "ok", d2
        assert d2.get("blocked") is False, d2


def main() -> int:
    test_adblock_offline_blocklist()
    print("OK: adblock_check_url tool validated with offline blocklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


