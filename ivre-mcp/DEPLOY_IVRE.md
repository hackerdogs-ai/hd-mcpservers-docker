# Deploying IVRE with Docker

Step-by-step guide to deploy a standalone IVRE instance using Docker, suitable for use with the ivre-mcp server.

## Prerequisites

- Docker Engine 20.10+ and Docker Compose v2
- At least 2 GB free RAM (MongoDB + IVRE services)
- At least 5 GB free disk space (database + geolocation data)

## Step 1: Create the Docker Compose File

Create a directory for your IVRE deployment and add this `docker-compose.yml`:

```bash
mkdir -p ~/ivre-deployment && cd ~/ivre-deployment
```

```yaml
# docker-compose.yml
version: '3'
services:
  ivredb:
    image: mongo:7
    container_name: ivredb
    volumes:
      - ./var_lib_mongodb:/data/db
    restart: always

  ivreuwsgi:
    image: ivre/web-uwsgi:latest
    container_name: ivreuwsgi
    restart: always
    depends_on:
      - ivredb
    volumes:
      - ./dokuwiki_data:/var/www/dokuwiki/data

  ivredoku:
    image: ivre/web-doku:latest
    container_name: ivredoku
    restart: always
    volumes:
      - ./dokuwiki_data:/var/www/dokuwiki/data

  ivreweb:
    image: ivre/web:latest
    container_name: ivreweb
    restart: always
    ports:
      - "80:80"
    depends_on:
      - ivreuwsgi
      - ivredoku
    volumes:
      - ./dokuwiki_data:/var/www/dokuwiki/data

  ivreclient:
    image: ivre/client:latest
    container_name: ivreclient
    depends_on:
      - ivredb
    volumes:
      - ./ivre-share:/ivre-share
    stdin_open: true
    tty: true
```

## Step 2: Start the Containers

```bash
docker compose up -d
```

Wait about 30 seconds for all services to initialize, then verify they are running:

```bash
docker compose ps
```

You should see five containers running: `ivredb`, `ivreuwsgi`, `ivredoku`, `ivreweb`, `ivreclient`.

## Step 3: Initialize the Databases

Attach to the `ivreclient` container:

```bash
docker exec -it ivreclient bash
```

Inside the container, initialize all IVRE database purposes:

```bash
yes | ivre ipinfo --init
yes | ivre scancli --init
yes | ivre view --init
yes | ivre flowcli --init
yes | ivre runscansagentdb --init
```

Download geolocation and web data:

```bash
ivre ipdata --download
ivre getwebdata
```

The `ipdata --download` step may take a few minutes as it fetches GeoIP databases.

Exit the client container:

```bash
exit
```

## Step 4: Verify the Web API

From your host machine, test the IVRE Web API:

```bash
# Should return JavaScript config
curl -s http://localhost/cgi/config

# Should return a count (0 if no scans imported yet)
curl -s "http://localhost/cgi/view/count"

# Test IP geolocation data (returns JSON)
curl -s "http://localhost/cgi/ipdata/8.8.8.8"
```

Open http://localhost in a browser. The IVRE Web UI should load. Click the HELP button to verify everything is functional.

## Step 5: Import Sample Data (Optional)

To have data to query, you can run a scan and import the results.

Attach to the client container:

```bash
docker exec -it ivreclient bash
```

**Option A: Run a scan against your local network** (adjust the target):

```bash
# Scan 10 hosts on your local network
nmap -A -oX /ivre-share/local-scan.xml 192.168.1.0/24 --max-hostgroup 10

# Import the results
ivre scan2db -c LOCAL-NET -s LocalScanner -r /ivre-share/local-scan.xml

# Create a view
ivre db2view nmap
```

**Option B: Import an existing Nmap XML file:**

```bash
# Copy your scan file to the shared volume on the host
# cp /path/to/scan-results.xml ~/ivre-deployment/ivre-share/

# Then inside the client container:
ivre scan2db -c MY-SCAN -s MySource -r /ivre-share/scan-results.xml
ivre db2view nmap
```

Verify the import:

```bash
# Count imported hosts
ivre scancli --count

# Check the view
ivre view --count
```

Exit the container:

```bash
exit
```

Then verify via the API:

```bash
curl -s "http://localhost/cgi/view/count"
curl -s "http://localhost/cgi/view?format=json&q=limit:3" | python3 -m json.tool
```

## Step 6: Connect the IVRE MCP Server

Now that IVRE is running, connect the ivre-mcp server to it.

**Same Docker network** (recommended when running on the same machine):

```bash
# Find the network IVRE is on
docker network ls | grep ivre

# Run ivre-mcp on the same network
docker run -i --rm \
  --network ivre-deployment_default \
  -e IVRE_WEB_URL=http://ivreweb:80 \
  -e MCP_TRANSPORT=stdio \
  hackerdogs/ivre-mcp:latest
```

**Remote IVRE instance** (when IVRE is on a different machine):

```bash
docker run -i --rm \
  -e IVRE_WEB_URL=http://your-ivre-host:80 \
  -e MCP_TRANSPORT=stdio \
  hackerdogs/ivre-mcp:latest
```

**Cursor / Claude Desktop configuration:**

```json
{
  "mcpServers": {
    "ivre-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--network", "ivre-deployment_default",
        "-e", "IVRE_WEB_URL",
        "-e", "MCP_TRANSPORT",
        "hackerdogs/ivre-mcp:latest"
      ],
      "env": {
        "IVRE_WEB_URL": "http://ivreweb:80",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

## Architecture Overview

```
Host Machine
├── ivreweb     (Nginx)          :80  ← IVRE Web UI + API
├── ivreuwsgi   (uWSGI + IVRE)        ← API request processing
├── ivredoku    (DokuWiki)             ← Notes/documentation
├── ivredb      (MongoDB)        :27017 ← Database storage
├── ivreclient  (CLI + Nmap)           ← Scanning & data import
└── ivre-mcp    (MCP Server)     :8366 ← AI agent interface
```

## Useful Commands

```bash
# Check container status
docker compose ps

# View IVRE web container logs
docker compose logs ivreweb

# Restart all services
docker compose restart

# Stop everything
docker compose down

# Stop and remove all data (destructive)
docker compose down -v && rm -rf var_lib_mongodb dokuwiki_data ivre-share
```

## Troubleshooting

**Web UI shows blank page:**
- Run `ivre getwebdata` inside `ivreclient`
- Check `docker compose logs ivreuwsgi` for errors

**API returns 502 Bad Gateway:**
- The uWSGI container may still be starting. Wait 30 seconds and retry.
- Check `docker compose logs ivreuwsgi`

**`/cgi/ipdata/` returns empty:**
- Run `ivre ipdata --download` inside `ivreclient` to fetch geolocation databases

**MongoDB connection errors in ivreclient:**
- Ensure `ivredb` is running: `docker compose ps ivredb`
- Check MongoDB logs: `docker compose logs ivredb`

**ivre-mcp cannot connect to IVRE:**
- Verify the containers are on the same Docker network
- Test connectivity: `docker exec ivre-mcp-test curl -s http://ivreweb:80/cgi/config`
- If using host networking, use `http://localhost:80` as `IVRE_WEB_URL`

## References

- [IVRE Docker Documentation](https://doc.ivre.rocks/en/latest/install/docker.html)
- [IVRE Fast Install & First Run](https://doc.ivre.rocks/en/latest/install/fast-install-and-first-run.html)
- [IVRE Web API Documentation](https://doc.ivre.rocks/en/latest/dev/web-api.html)
- [Official Docker Images](https://hub.docker.com/u/ivre/)
