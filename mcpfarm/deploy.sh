#!/usr/bin/env bash
# =============================================================================
# Hackerdogs MCP Server Farm — Deployment Script
# =============================================================================
# Usage:
#   ./deploy.sh                        # interactive prompts
#   TUNNEL_TOKEN=xxx ADMIN_SECRET=xxx ./deploy.sh
#   ./deploy.sh --skip-build           # skip image builds (images must exist)
#   ./deploy.sh --start-all            # also start all 386 MCP servers
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SKIP_BUILD=false
START_ALL=false
NO_TUNNEL=false
# Base URL the script uses to reach Caddy for health/reload/stats. Override when
# Caddy is mapped to a non-default host port (e.g. local testing): FARM_HTTP=http://localhost:8485
FARM_PORT="${FARM_PORT:-8485}"
FARM_HTTP="${FARM_HTTP:-http://localhost:${FARM_PORT}}"

for arg in "$@"; do
  case $arg in
    --skip-build) SKIP_BUILD=true ;;
    --start-all)  START_ALL=true ;;
    --no-tunnel|--local) NO_TUNNEL=true ;;
  esac
done

echo ""
echo "============================================================"
echo "   Hackerdogs MCP Server Farm — Deployer"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
info "Checking prerequisites..."
command -v docker  &>/dev/null || error "Docker not found. Install Docker Desktop first."
docker info &>/dev/null        || error "Docker daemon not running."
command -v python3 &>/dev/null || error "python3 not found."
success "Prerequisites OK"

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
if [[ "$NO_TUNNEL" == "true" ]]; then
  # Local/dev mode: no public tunnel. The farm is reachable at http://localhost.
  TUNNEL_TOKEN="${TUNNEL_TOKEN:-local-no-tunnel}"
  warn "Running in --no-tunnel mode: cloudflared will NOT start; farm is local-only (http://localhost)."
elif [[ -z "${TUNNEL_TOKEN:-}" ]]; then
  echo ""
  echo "Enter your Cloudflare Tunnel token (from Zero Trust dashboard):"
  echo "(or re-run with --no-tunnel for a local-only deployment)"
  read -r -s TUNNEL_TOKEN
  [[ -z "$TUNNEL_TOKEN" ]] && error "TUNNEL_TOKEN is required (or use --no-tunnel)."
fi

if [[ -z "${ADMIN_SECRET:-}" ]]; then
  ADMIN_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  warn "ADMIN_SECRET not set — generated: $ADMIN_SECRET"
  warn "Save this — it's your admin API password."
fi

# Write .env
cat > "$SCRIPT_DIR/.env" <<EOF
TUNNEL_TOKEN=${TUNNEL_TOKEN}
ADMIN_SECRET=${ADMIN_SECRET}
FARM_PORT=${FARM_PORT}
EOF
success ".env written"

# ---------------------------------------------------------------------------
# Build images
# ---------------------------------------------------------------------------
cd "$SCRIPT_DIR"

if [[ "$SKIP_BUILD" == "false" ]]; then
  info "Building auth-gateway image..."
  docker compose build auth-gateway
  success "auth-gateway built"

  info "Building mcpfarm-ui image..."
  docker compose build mcpfarm-ui
  success "mcpfarm-ui built"

  info "Building MCP server images (this takes a while)..."
  BUILT=0; FAILED=0; FAIL_LIST=()

  while IFS= read -r name; do
    dir="$REPO_DIR/$name"
    [[ ! -f "$dir/Dockerfile" ]] && continue
    if docker build -t "hackerdogs/${name}:latest" "$dir" \
         > "$SCRIPT_DIR/build-logs/${name}.log" 2>&1; then
      ((BUILT++))
    else
      ((FAILED++))
      FAIL_LIST+=("$name")
    fi
    echo -ne "\r  Built: ${BUILT}  Failed: ${FAILED}  "
  done < <(docker inspect --format '{{.Config.Image}}' \
    $(docker compose config --services 2>/dev/null | grep "\-mcp$") 2>/dev/null \
    | sed 's|hackerdogs/||; s|:latest||' 2>/dev/null \
    || python3 -c "
import json
with open('port-map.json') as f:
    data = json.load(f)
for s in data:
    print(s['name'])
")

  echo ""
  success "Image builds complete — $BUILT built, $FAILED failed"
  if [[ ${#FAIL_LIST[@]} -gt 0 ]]; then
    warn "Failed: ${FAIL_LIST[*]}"
    warn "Check build-logs/ for details. These servers will be skipped."
  fi
else
  info "Skipping image builds (--skip-build)"
fi

# ---------------------------------------------------------------------------
# Start infra
# ---------------------------------------------------------------------------
info "Starting infra (caddy, auth-gateway, cloudflared, ui)..."
docker compose up -d --no-deps auth-gateway
echo -n "  Waiting for auth-gateway to be healthy"
for i in $(seq 1 30); do
  if docker inspect --format '{{.State.Health.Status}}' mcpfarm-auth 2>/dev/null | grep -q "healthy"; then
    break
  fi
  echo -n "."
  sleep 2
done
echo ""
docker inspect --format '{{.State.Health.Status}}' mcpfarm-auth | grep -q "healthy" \
  || error "auth-gateway failed to become healthy. Check: docker logs mcpfarm-auth"
success "auth-gateway healthy"

docker compose up -d --no-deps caddy
echo -n "  Waiting for caddy to be healthy"
for i in $(seq 1 30); do
  if docker inspect --format '{{.State.Health.Status}}' mcpfarm-caddy 2>/dev/null | grep -q "healthy"; then
    break
  fi
  echo -n "."
  sleep 2
done
echo ""
docker inspect --format '{{.State.Health.Status}}' mcpfarm-caddy | grep -q "healthy" \
  || error "Caddy failed to become healthy. Check: docker logs mcpfarm-caddy"
success "caddy healthy"

if [[ "$NO_TUNNEL" == "true" ]]; then
  info "Skipping cloudflared (--no-tunnel)"
else
  docker compose up -d --no-deps cloudflared
  sleep 3
  success "cloudflared started"
fi

docker compose up -d --no-deps mcpfarm-ui
success "mcpfarm-ui started"

# ---------------------------------------------------------------------------
# Seed database
# ---------------------------------------------------------------------------
info "Seeding database..."
SEED_OUT=$(docker exec mcpfarm-auth python seed.py 2>&1)
echo "$SEED_OUT" | tail -5

ADMIN_KEY=$(echo "$SEED_OUT" | grep "Admin API Key:" | awk '{print $NF}')
if [[ -z "$ADMIN_KEY" ]]; then
  warn "Admin key already exists (re-deploy). Skipping key display."
else
  echo ""
  echo -e "${GREEN}============================================================${NC}"
  echo -e "${GREEN}  ADMIN API KEY (save this — shown only once):${NC}"
  echo -e "${GREEN}  $ADMIN_KEY${NC}"
  echo -e "${GREEN}============================================================${NC}"
  echo ""
fi

# ---------------------------------------------------------------------------
# Load Caddy routes
# ---------------------------------------------------------------------------
info "Loading Caddy routes (386 servers)..."
sleep 2
RELOAD=$(curl -s -X POST ${FARM_HTTP}/admin/reload \
  -H "X-Admin-Secret: ${ADMIN_SECRET}" 2>&1)
echo "$RELOAD" | grep -q "reloaded" && success "Routes loaded" \
  || warn "Route reload returned: $RELOAD (Caddy may need a moment)"

# ---------------------------------------------------------------------------
# Optionally start all MCP servers
# ---------------------------------------------------------------------------
if [[ "$START_ALL" == "true" ]]; then
  info "Starting all MCP servers in batches (this may take a few minutes)..."
  # Previously-broken builds (bettercap, gitleaks, horusec, subjack,
  # vulnerability-scanner, x8) have been fixed and now build/test cleanly.
  # Add any server here that still fails to build to skip it on --start-all.
  FAIL_BUILDS=""
  BATCH=(); COUNT=0

  while IFS= read -r svc; do
    echo "$FAIL_BUILDS" | grep -qw "$svc" && continue
    BATCH+=("$svc")
    if [[ ${#BATCH[@]} -ge 10 ]]; then
      docker compose up -d --pull never --no-deps "${BATCH[@]}" >/dev/null 2>&1 || true
      BATCH=(); ((COUNT+=10))
      echo -ne "\r  Started: ~${COUNT}  "
      sleep 2
    fi
  done < <(python3 -c "
import json
with open('port-map.json') as f:
    data = json.load(f)
for s in data:
    print(s['name'])
")

  [[ ${#BATCH[@]} -gt 0 ]] && \
    docker compose up -d --pull never --no-deps "${BATCH[@]}" >/dev/null 2>&1 || true
  echo ""
  success "MCP servers started"
fi

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
info "Verifying deployment..."
HEALTH=$(curl -s ${FARM_HTTP}/health 2>&1)
[[ "$HEALTH" == "OK" ]] && success "http://localhost/health → OK" \
  || warn "Health check returned: $HEALTH"

if [[ "$NO_TUNNEL" == "true" ]]; then
  info "Tunnel check skipped (--no-tunnel). Farm is local-only at http://localhost"
else
  CF_STATUS=$(docker logs mcpfarm-tunnel 2>&1 | grep "Registered tunnel connection" | wc -l | tr -d ' ')
  [[ "$CF_STATUS" -ge 1 ]] && success "Cloudflare tunnel connected ($CF_STATUS connections)" \
    || warn "Cloudflare tunnel may not be connected yet. Check: docker logs mcpfarm-tunnel"
fi

STATS=$(curl -s ${FARM_HTTP}/admin/stats -H "X-Admin-Secret: ${ADMIN_SECRET}" 2>&1)
echo ""
echo "Farm stats:"
echo "$STATS" | python3 -m json.tool 2>/dev/null || echo "$STATS"

echo ""
echo "============================================================"
echo "  Deployment complete!"
echo ""
echo "  Local:    ${FARM_HTTP}/health"
echo "  Tunnel:   check Cloudflare dashboard for public hostname"
echo ""
echo "  Start a server:  docker compose up -d --no-deps <name>-mcp"
echo "  Admin API:       curl ${FARM_HTTP}/admin/stats \\"
echo "                     -H 'X-Admin-Secret: ${ADMIN_SECRET}'"
echo "============================================================"
echo ""
