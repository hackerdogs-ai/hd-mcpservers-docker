"""
Constants for AbuseCH (abuse.ch) integrations.

Important:
- This module MUST NOT exit the process on import. It can be imported by:
  - The MCP server (`abusech_mcp.py`) which may rely on env vars
  - LangChain tools, which prefer supplying credentials via ToolRuntime

The API key can be provided in two ways:
- Preferred for LangChain tools: passed explicitly into request helpers
- Fallback for MCP server: read from environment variable ABUSECH_API_KEY
"""

from __future__ import annotations

import os
from typing import Optional

ABUSECH_API_KEY: Optional[str] = os.environ.get("ABUSECH_API_KEY")

MALWAREBAZAAR_API_URL = "https://mb-api.abuse.ch/api/v1"
URLHAUS_API_URL = "https://urlhaus-api.abuse.ch/v1"
THREATFOX_API_URL = "https://threatfox-api.abuse.ch/api/v1"