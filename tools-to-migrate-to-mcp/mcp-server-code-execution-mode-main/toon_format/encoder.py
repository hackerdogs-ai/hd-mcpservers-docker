"""Minimal encoder for the local TOON shim (JSON-backed)."""

from __future__ import annotations

import json
from typing import Any

from .types import EncodeOptions, JsonValue


def encode(value: JsonValue, options: EncodeOptions | None = None) -> str:
    """Encode a Python JSON-like value to a compact string.

    This intentionally uses JSON, not a custom TOON grammar.
    """

    _ = options  # reserved for future compatibility
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


