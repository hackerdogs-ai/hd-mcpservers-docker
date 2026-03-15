"""Minimal decoder for the local TOON shim (JSON-backed)."""

from __future__ import annotations

import json

from .types import DecodeOptions, JsonValue


def decode(input: str, options: DecodeOptions | None = None) -> JsonValue:
    """Decode a compact string into a Python value.

    This intentionally parses JSON, not a custom TOON grammar.
    """

    _ = options  # reserved for future compatibility
    return json.loads(input)


