#!/bin/bash

# Tor Proxy Test Script
# Tests the standalone Tor proxy service independently
#
# Usage:
#   ./tor_test.sh
#   ./tor_test.sh --quick    # Skip .onion site test (faster)
#   ./tor_test.sh --verbose  # Show detailed output

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose-tor-proxy.yaml"
CONTAINER_NAME="tor-proxy"
SOCKS5_PORT="127.0.0.1:9050"
HTTP_PORT="127.0.0.1:8118"
TEST_URL="https://check.torproject.org/api/ip"
ONION_URL="http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/"

# Parse arguments
QUICK_MODE=false
VERBOSE=false
for arg in "$@"; do
    case $arg in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Use docker compose (v2) if available, otherwise docker-compose (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header "Tor Proxy Test Script"

# Test 1: Check if container is running
print_header "Test 1: Container Status"
if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_NAME")
    HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "no-healthcheck")
    
    print_success "Container is running (Status: $CONTAINER_STATUS)"
    
    if [ "$HEALTH_STATUS" != "no-healthcheck" ]; then
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            print_success "Health check: $HEALTH_STATUS"
        else
            print_warning "Health check: $HEALTH_STATUS (Tor may still be bootstrapping)"
        fi
    fi
else
    print_error "Container '$CONTAINER_NAME' is not running"
    print_info "Start it with: $DOCKER_COMPOSE -f $COMPOSE_FILE up -d"
    exit 1
fi

# Test 2: Wait for Tor to bootstrap
print_header "Test 2: Tor Bootstrap Status"
print_info "Checking if Tor is bootstrapped (this may take 30-60 seconds)..."

BOOTSTRAP_READY=false
MAX_WAIT=90
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if docker exec "$CONTAINER_NAME" curl -f --socks5-hostname 127.0.0.1:9050 "$TEST_URL" &>/dev/null; then
        BOOTSTRAP_READY=true
        break
    fi
    if [ $((WAIT_COUNT % 10)) -eq 0 ]; then
        echo -n "."
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

echo ""

if [ "$BOOTSTRAP_READY" = true ]; then
    print_success "Tor is bootstrapped and ready"
else
    print_warning "Tor may still be bootstrapping (waited ${WAIT_COUNT}s)"
    print_info "Continuing with tests..."
fi

# Test 3: Test SOCKS5 proxy from host
print_header "Test 3: SOCKS5 Proxy Test (from host)"
print_info "Testing connection through Tor proxy at $SOCKS5_PORT..."

RESPONSE=$(curl -s --socks5-hostname "$SOCKS5_PORT" --max-time 30 "$TEST_URL" || echo "")

if [ -z "$RESPONSE" ]; then
    print_error "Failed to connect through Tor proxy"
    exit 1
fi

if [ "$VERBOSE" = true ]; then
    echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi

# Check if IsTor is true
if echo "$RESPONSE" | grep -q '"IsTor":true'; then
    TOR_IP=$(echo "$RESPONSE" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4)
    print_success "Connected through Tor (Exit Node IP: $TOR_IP)"
else
    print_error "Not connected through Tor (IsTor: false)"
    echo "Response: $RESPONSE"
    exit 1
fi

# Test 4: Compare with real IP
print_header "Test 4: IP Comparison"
print_info "Getting your real IP address (without Tor)..."

REAL_IP_RESPONSE=$(curl -s --max-time 10 "$TEST_URL" || echo "")
REAL_IP=$(echo "$REAL_IP_RESPONSE" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4)

if [ -n "$REAL_IP" ] && [ -n "$TOR_IP" ]; then
    if [ "$REAL_IP" != "$TOR_IP" ]; then
        print_success "IP addresses differ (Tor is working)"
        echo "  Real IP:   $REAL_IP"
        echo "  Tor IP:    $TOR_IP"
    else
        print_warning "IP addresses are the same (may indicate Tor is not routing correctly)"
        echo "  Real IP:   $REAL_IP"
        echo "  Tor IP:    $TOR_IP"
    fi
else
    print_warning "Could not compare IP addresses"
fi

# Test 5: Test HTTP proxy
print_header "Test 5: HTTP Proxy Test (port 8118)"
print_info "Testing HTTP proxy at $HTTP_PORT..."

HTTP_RESPONSE=$(curl -s --proxy "http://$HTTP_PORT" --max-time 30 "$TEST_URL" || echo "")

if [ -z "$HTTP_RESPONSE" ]; then
    print_warning "HTTP proxy test failed (may not be configured)"
else
    if echo "$HTTP_RESPONSE" | grep -q '"IsTor":true'; then
        print_success "HTTP proxy is working through Tor"
    else
        print_warning "HTTP proxy may not be routing through Tor"
    fi
fi

# Test 6: Test from Docker container (if network exists)
print_header "Test 6: Container Network Test"
NETWORK_NAME=$(docker inspect "$CONTAINER_NAME" --format='{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}{{end}}' | head -1)

if [ -n "$NETWORK_NAME" ]; then
    print_info "Testing from container on network: $NETWORK_NAME"
    
    # Try to test from a temporary container
    if docker run --rm --network "$NETWORK_NAME" --name tor-test-temp curlimages/curl:latest \
        curl -s --socks5-hostname "${CONTAINER_NAME}:9050" --max-time 30 "$TEST_URL" > /tmp/tor_test_output.txt 2>&1; then
        CONTAINER_RESPONSE=$(cat /tmp/tor_test_output.txt)
        if echo "$CONTAINER_RESPONSE" | grep -q '"IsTor":true'; then
            print_success "Container network test passed"
        else
            print_warning "Container network test: Tor connection may not be working"
        fi
        rm -f /tmp/tor_test_output.txt
    else
        print_warning "Could not test from container (network may not be accessible)"
    fi
else
    print_warning "Could not determine network name"
fi

# Test 7: Test .onion site access (skip in quick mode)
if [ "$QUICK_MODE" = false ]; then
    print_header "Test 7: .onion Site Access Test"
    print_info "Testing access to DuckDuckGo .onion site (this may take 10-30 seconds)..."
    print_warning "This test may timeout if the .onion site is slow or unavailable"
    
    ONION_RESPONSE=$(curl -s --socks5-hostname "$SOCKS5_PORT" --max-time 45 "$ONION_URL" || echo "")
    
    if [ -n "$ONION_RESPONSE" ]; then
        # Check if we got HTML content
        if echo "$ONION_RESPONSE" | grep -qi "html\|duckduckgo"; then
            print_success "Successfully accessed .onion site"
            if [ "$VERBOSE" = true ]; then
                echo "Response preview:"
                echo "$ONION_RESPONSE" | head -5
            fi
        else
            print_warning "Got response from .onion site but content is unexpected"
        fi
    else
        print_warning ".onion site test timed out or failed (this is common due to Tor latency)"
    fi
else
    print_header "Test 7: .onion Site Access Test"
    print_info "Skipped (--quick mode)"
fi

# Test 8: Exit node rotation test
print_header "Test 8: Exit Node Rotation Test"
print_info "Making 3 requests to check if Tor rotates exit nodes..."

EXIT_NODES=()
for i in {1..3}; do
    RESPONSE=$(curl -s --socks5-hostname "$SOCKS5_PORT" --max-time 30 "$TEST_URL" || echo "")
    IP=$(echo "$RESPONSE" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$IP" ]; then
        EXIT_NODES+=("$IP")
        echo "  Request $i: $IP"
    fi
    sleep 2
done

UNIQUE_IPS=$(printf '%s\n' "${EXIT_NODES[@]}" | sort -u | wc -l)
if [ "$UNIQUE_IPS" -gt 1 ]; then
    print_success "Tor is rotating exit nodes ($UNIQUE_IPS unique IPs)"
else
    print_info "All requests used the same exit node (normal for short time window)"
fi

# Test 9: Check logs
print_header "Test 9: Container Logs Check"
print_info "Checking recent logs for errors..."

RECENT_LOGS=$(docker logs --tail 20 "$CONTAINER_NAME" 2>&1)

if echo "$RECENT_LOGS" | grep -qi "error\|failed\|exception"; then
    print_warning "Found potential errors in logs:"
    echo "$RECENT_LOGS" | grep -i "error\|failed\|exception" | head -5
else
    print_success "No obvious errors in recent logs"
fi

if [ "$VERBOSE" = true ]; then
    echo "Recent logs:"
    echo "$RECENT_LOGS"
fi

# Summary
print_header "Test Summary"
print_success "All critical tests passed!"
echo ""
print_info "Tor proxy is working correctly at:"
echo "  - SOCKS5: $SOCKS5_PORT"
echo "  - HTTP:   $HTTP_PORT"
echo ""
print_info "Use it with OnionSearch:"
echo "  onionsearch \"query\" --proxy $SOCKS5_PORT"
echo ""
print_info "Or from Docker containers on the same network:"
echo "  --proxy tor-proxy:9050"
echo ""

exit 0

