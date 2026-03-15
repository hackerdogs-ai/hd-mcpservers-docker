"""Types used by the local TOON shim."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Union

JsonPrimitive = Union[str, int, float, bool, None]
JsonValue = Union[JsonPrimitive, Dict[str, "JsonValue"], List["JsonValue"]]


@dataclass(frozen=True)
class EncodeOptions:
    # Placeholder for compatibility with the upstream API surface.
    indent: int = 2


@dataclass(frozen=True)
class DecodeOptions:
    # Placeholder for compatibility with the upstream API surface.
    indent: int = 2
    strict: bool = True


