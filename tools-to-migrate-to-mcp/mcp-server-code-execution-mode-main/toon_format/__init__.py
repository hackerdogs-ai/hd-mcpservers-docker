"""
Local TOON-format shim used by the vendored bridge test-suite.

Why this exists:
- The upstream `toon_format` PyPI package currently ships stubs where `encode()` / `decode()`
  raise NotImplementedError, which breaks our `MCP_BRIDGE_OUTPUT_MODE=toon` contract tests.
- For Hackerdogs, the primary requirement of "toon mode" is a **stable fenced block**
  (` ```toon ... ``` `) plus a **round-tripable structured payload**.

This shim implements encode/decode as JSON. It is intentionally minimal and only supports the
surface used by `tests/test_toon_responses.py` and the bridge itself.
"""

from .decoder import decode
from .encoder import encode
from .types import DecodeOptions, EncodeOptions

__all__ = ["encode", "decode", "EncodeOptions", "DecodeOptions"]


