# Deploy the Farm (Simple Steps)

This guide shows how to turn on **three things**:

1. The **Farm** (the boss that watches everything)
2. The **UI** (the pretty web page you click)
3. The **MCP servers** (the little tool helpers)

You only need **Docker** running on your computer.

---

## Before you start

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine).
2. Open Docker and wait until it says it is running.
3. Open a terminal.
4. Go into this project folder:

```bash
cd hd-mcpservers-docker
```

---

## Step 1 — Go into the farm folder

```bash
cd mcpfarm
```

That folder has the buttons (scripts) that start everything.

---

## Step 2 — Start the Farm + UI

Copy and paste this:

```bash
./deploy.sh up --skip-build
```

What this does:

- Downloads the Farm brain (`auth-gateway`)
- Downloads the front door (`caddy`)
- Downloads the web page (`mcpfarm-ui`)
- Turns them all on
- Fills in the list of tools from `port-map.json`

Wait until it finishes. It may take a few minutes the first time.

---

## Step 3 — Open the UI

Open your browser and go to:

**http://localhost:8485**

You should see the Farm dashboard.

- If it asks you to **Generate** an admin secret, click that button.
- Save any **Admin API Key** the script printed — you may need it later.

Health check (optional):

**http://localhost:8485/health**

If you see `OK`, the Farm is happy.

---

## Step 4 — Start some MCP servers (tools)

The Farm is on. The UI is on. The tools are **still sleeping**.

Wake up the ones you want. Examples:

```bash
./deploy.sh start naabu-mcp
```

Or start a few at once:

```bash
./deploy.sh start naabu-mcp whois-mcp nmap-mcp
```

Tool names live in `mcpfarm/port-map.json` (or the big table in the root `README.md`).

Check what is running:

```bash
./deploy.sh status
```

---

## Step 5 — Use a tool

### From the UI

1. Open **http://localhost:8485**
2. Pick a server from the list
3. Start it if it is stopped
4. Run a tool from the page

### From Cursor / Claude (HTTP)

Use the Farm URL + your API key:

```json
{
  "mcpServers": {
    "naabu": {
      "type": "http",
      "url": "http://localhost:8485/naabu-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <API_KEY>"
      }
    }
  }
}
```

Replace `<API_KEY>` with a key you create in the UI (or the seed key from deploy).

---

## How to stop

Stop one tool:

```bash
./deploy.sh stop naabu-mcp
```

Stop all tools:

```bash
./deploy.sh stop --all
```

Turn the whole Farm off (UI + Farm + tools):

```bash
./deploy.sh down
```

---

## Tiny picture of what you started

```
You (browser or Cursor)
        │
        ▼
   UI + Farm door
  http://localhost:8485
        │
        ▼
   MCP tool boxes
  (naabu-mcp, whois-mcp, …)
```

| Piece | What it is | How it starts |
|-------|------------|---------------|
| Farm | Auth + proxy (Caddy + auth-gateway) | `./deploy.sh up --skip-build` |
| UI | Web dashboard | Same command (starts with the Farm) |
| MCP servers | Individual tools | `./deploy.sh start <name>-mcp` |

---

## Optional: run one MCP server alone (no Farm)

Only need one tool? Skip the Farm:

```bash
docker pull hackerdogs/naabu-mcp:latest
docker run -d --name naabu-mcp -p 8105:8105 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8105 \
  hackerdogs/naabu-mcp:latest
```

Then open: `http://localhost:8105/mcp`

(Change the name and port for other tools — see the root `README.md`.)

---

## If something goes wrong

| Problem | Try this |
|---------|----------|
| Docker not found | Install Docker and start it |
| Port busy | Change `FARM_PORT` in `mcpfarm/.env` (default is `8485`) |
| UI blank / not loading | Wait 30 seconds, then refresh. Check `./deploy.sh status` |
| Tool will not start | Check the name spelling. Look in `port-map.json` |
| Need secrets for a tool | Put API keys in `mcpfarm/.env` (see `.env.example`) |

---

## Want more detail?

- Full operator guide: [`mcpfarm/DEPLOY.md`](../mcpfarm/DEPLOY.md)
- How to use the UI: [`mcpfarm-ui/docs/USERS-GUIDE.md`](../mcpfarm-ui/docs/USERS-GUIDE.md)
- Local UI hot-reload (developers): `./start_mcpfarm.sh` from the repo root
