#!/usr/bin/env bash
# Run 5-step MCP Docker compliance for github-mcp only (image, stdio, HTTP).
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$ROOT/github-mcp/test.sh"
