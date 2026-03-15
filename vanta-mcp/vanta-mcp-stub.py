#!/usr/bin/env python3
"""Stub for vanta-mcp when Vanta API credentials are not configured.

Vanta (https://www.vanta.com) is a paid compliance/security platform. The upstream
VantaInc/vanta-mcp-server is an MCP server that requires VANTA_ENV_FILE with OAuth
client_id and client_secret. This stub allows the Hackerdogs MCP wrapper to start
and expose run_vanta_mcp; without valid Vanta API credentials only this stub runs.
"""

import sys

HELP_TEXT = """Vanta MCP Server (stub — no API credentials)

Vanta is a paid compliance and security platform. Real integration requires:
  - A Vanta account (core package or above)
  - VANTA_ENV_FILE pointing to a JSON file with OAuth client_id and client_secret

This container does not have Vanta API credentials configured. The MCP server
exposes the run_vanta_mcp tool, but calls are handled by this stub.

For full functionality, configure VANTA_ENV_FILE and use the official
VantaInc/vanta-mcp-server (see https://github.com/VantaInc/vanta-mcp-server).

Usage: vanta-mcp [OPTIONS] [ARGS]
  --help    Show this message
  --version Show version (stub 1.0)
"""


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args or not args:
        print(HELP_TEXT)
        sys.exit(0)
    if "--version" in args or "-v" in args:
        print("vanta-mcp (stub) 1.0 - no Vanta API credentials configured")
        sys.exit(0)
    print(
        "vanta-mcp stub: Vanta API credentials required for real use. Use --help for info.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
