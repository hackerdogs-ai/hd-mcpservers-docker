#!/usr/bin/env python3
"""Stub for threat-hunting CLI when the real binary is not installed in the image.

The hackerdogs threat-hunting-mcp image wraps a 'threat-hunting' binary. The upstream
THORCollective/threat-hunting-mcp-server is an MCP server, not a CLI. This stub allows
the MCP tool to run and return helpful output for --help; for full functionality
the real threat-hunting CLI would need to be installed in the image.
"""
import sys

HELP_TEXT = """Threat Hunting MCP Server (stub)

This container does not include the full threat-hunting CLI binary.
The threat-hunting-mcp server is connected and can invoke this stub.

For full threat-hunting capabilities, the image would need to install
the actual threat-hunting executable (see THORCollective documentation).

Usage: threat-hunting [OPTIONS] [ARGS]
  --help    Show this message
  --version Show version (stub 1.0)
"""

def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args or not args:
        print(HELP_TEXT)
        sys.exit(0)
    if "--version" in args or "-v" in args:
        print("threat-hunting (stub) 1.0 - MCP server placeholder")
        sys.exit(0)
    print("threat-hunting stub: no real binary installed. Use --help for info.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
