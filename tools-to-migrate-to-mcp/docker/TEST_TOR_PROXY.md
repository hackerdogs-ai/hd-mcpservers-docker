# Testing Tor Proxy Independently

This guide explains how to test the standalone Tor proxy service using `docker-compose-tor-proxy.yaml`.

## Prerequisites

- Docker and Docker Compose installed
- `curl` installed (for testing)
- Network access to download Tor proxy image

## Step 1: Start Tor Proxy

```bash
cd shared/modules/tools/docker
docker-compose -f docker-compose-tor-proxy.yaml up -d
```

**Expected Output:**
```
Creating network "docker_hd-tools" ... done
Creating tor-proxy ... done
```

## Step 2: Check Container Status

```bash
# Check if container is running
docker-compose -f docker-compose-tor-proxy.yaml ps

# Or using docker directly
docker ps | grep tor-proxy
```

**Expected Output:**
```
NAME        IMAGE                    STATUS
tor-proxy   dperson/torproxy:latest  Up X seconds (health: starting)
```

**Note:** Wait 30-60 seconds for Tor to bootstrap. The health check will show `(healthy)` when ready.

## Step 3: Check Health Status

```bash
# Check health status
docker inspect tor-proxy | grep -A 10 Health

# Or check logs for bootstrap progress
docker-compose -f docker-compose-tor-proxy.yaml logs tor-proxy
```

**Look for:**
- `"Status": "healthy"` in health check output
- Log messages indicating Tor is connected to the network

## Step 4: Test from Host (SOCKS5 Proxy)

### Test 1: Check Your IP Through Tor

```bash
# Test SOCKS5 proxy (port 9050)
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```

**Expected Output:**
```json
{
  "IsTor": true,
  "IP": "xxx.xxx.xxx.xxx"  # Your Tor exit node IP (different from your real IP)
}
```

**Success Indicators:**
- `"IsTor": true` - Confirms you're using Tor
- IP address is different from your real IP
- IP address changes on each request (Tor rotates exit nodes)

### Test 2: Check Your Real IP (Without Tor)

```bash
# Compare with your real IP
curl https://check.torproject.org/api/ip
```

**Expected:** Different IP address than the Tor test above.

### Test 3: Test HTTP Proxy (Port 8118)

```bash
# Test HTTP proxy (port 8118)
curl --proxy http://127.0.0.1:8118 https://check.torproject.org/api/ip
```

**Expected:** Same as SOCKS5 test - `"IsTor": true`

### Test 4: Access .onion Site (Dark Web)

```bash
# Test accessing a .onion site (example: DuckDuckGo's Tor search)
curl --socks5-hostname 127.0.0.1:9050 http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/
```

**Expected:** HTML content from DuckDuckGo's .onion site

**Note:** This may take longer (10-30 seconds) due to Tor network latency.

## Step 5: Test from Docker Container

If you have `osint-tools` or another container on the same network:

```bash
# Test from osint-tools container (if running)
docker exec osint-tools curl --socks5-hostname tor-proxy:9050 https://check.torproject.org/api/ip

# Or test from any container on hd-tools network
docker run --rm --network docker_hd-tools curlimages/curl:latest \
  curl --socks5-hostname tor-proxy:9050 https://check.torproject.org/api/ip
```

**Expected:** Same as host test - `"IsTor": true`

## Step 6: Monitor Tor Logs

```bash
# Follow logs in real-time
docker-compose -f docker-compose-tor-proxy.yaml logs -f tor-proxy

# Or using docker directly
docker logs -f tor-proxy
```

**Look for:**
- `"Bootstrapped 100%"` - Tor is fully connected
- Connection messages
- Any error messages

## Step 7: Test Connection Speed

```bash
# Test download speed through Tor (will be slower than direct)
time curl --socks5-hostname 127.0.0.1:9050 -o /dev/null https://www.google.com

# Compare with direct connection
time curl -o /dev/null https://www.google.com
```

**Expected:** Tor connection will be significantly slower (2-10x) due to routing through multiple nodes.

## Step 8: Test Multiple Requests (Exit Node Rotation)

```bash
# Make multiple requests to see different exit nodes
for i in {1..5}; do
  echo "Request $i:"
  curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip | grep -o '"IP":"[^"]*"'
  sleep 2
done
```

**Expected:** Different IP addresses for each request (Tor rotates exit nodes).

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose -f docker-compose-tor-proxy.yaml logs tor-proxy

# Check if port 9050 is already in use
lsof -i :9050
# or
netstat -an | grep 9050

# Stop conflicting service or change port in docker-compose-tor-proxy.yaml
```

### Health Check Failing

```bash
# Check if curl is available in container
docker exec tor-proxy which curl

# Manually test health check command
docker exec tor-proxy curl -f --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip

# Check Tor bootstrap status
docker exec tor-proxy cat /var/log/tor/tor.log | grep -i bootstrap
```

### Connection Timeout

```bash
# Check if Tor is bootstrapped (takes 30-60 seconds)
docker exec tor-proxy curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip

# If it fails, wait longer and check logs
docker logs tor-proxy | tail -20
```

### "Connection Refused" Error

```bash
# Verify container is running
docker ps | grep tor-proxy

# Verify port is exposed
docker port tor-proxy

# Test from inside container
docker exec tor-proxy netstat -tlnp | grep 9050
```

## Quick Test Script

Save this as `test-tor-proxy.sh`:

```bash
#!/bin/bash

echo "=== Testing Tor Proxy ==="
echo ""

# Check container status
echo "1. Container Status:"
docker ps | grep tor-proxy || echo "❌ Container not running"
echo ""

# Wait for bootstrap
echo "2. Waiting for Tor to bootstrap (30 seconds)..."
sleep 30
echo ""

# Test IP check
echo "3. Testing IP through Tor:"
curl -s --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip | jq .
echo ""

# Test .onion access
echo "4. Testing .onion site access:"
curl -s --socks5-hostname 127.0.0.1:9050 --max-time 30 \
  http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/ | head -20
echo ""

echo "=== Test Complete ==="
```

Make it executable and run:
```bash
chmod +x test-tor-proxy.sh
./test-tor-proxy.sh
```

## Cleanup

```bash
# Stop and remove Tor proxy
docker-compose -f docker-compose-tor-proxy.yaml down

# Remove network (if not used by other containers)
docker network rm docker_hd-tools
```

## Success Criteria

✅ **Tor proxy is working correctly if:**
1. Container shows `(healthy)` status
2. `curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip` returns `"IsTor": true`
3. IP address is different from your real IP
4. Can access .onion sites (with longer timeouts)
5. Logs show "Bootstrapped 100%"

## Next Steps

Once Tor proxy is verified working:
- Use it with OnionSearch: `onionsearch "query" --proxy 127.0.0.1:9050`
- Connect other tools to `tor-proxy:9050` (from Docker network)
- Monitor logs for any issues during usage

