#!/bin/sh

# stripe-mcp is a remote proxy to Stripe's API; it requires valid credentials.
# When placeholder keys are used, fall back to a lightweight mock server
# so the container can pass protocol-level health checks.
is_placeholder() {
  case "$STRIPE_SECRET_KEY" in
    *PLACEHOLDER*|""|sk_test_PLACEHOLDER) return 0 ;;
    *) return 1 ;;
  esac
}

if is_placeholder; then
  MOCK_CMD="python3 /mock_mcp.py stripe-mcp 'Stripe payment, billing, and subscription management tools' 8669"
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec $MOCK_CMD
  else
    exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8669} -- $MOCK_CMD
  fi
else
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec npx -y @stripe/mcp
  else
    exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8669} -- npx -y @stripe/mcp
  fi
fi
