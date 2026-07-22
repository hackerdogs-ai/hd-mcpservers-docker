# MCP Farm — User Guide

This guide covers day-to-day use of the **MCP Farm web dashboard** (`mcpfarm-ui`). For installing the farm itself, see [mcpfarm/DEPLOY.md](../../mcpfarm/DEPLOY.md). For the full server catalog, see the [repository README](../../README.md#tool-registry).

---

## Accessing the dashboard

After the farm is deployed, open the UI in your browser:

| Deployment | URL |
|------------|-----|
| Local / default | `http://localhost:8485` |
| Behind your own TLS / proxy | `https://<your-hostname>` |

On first load:

- If the farm already has an **admin secret** (normal deploy), the dashboard opens the home page and loads credentials from `/ui-config`.
- If there is **no** admin secret yet, a one-time setup dialog appears. Use **Generate** to create the secret, then **Continue**.

Manage Bearer API keys anytime under **Settings → API key management** (create, refresh, revoke). Rotate the admin secret from Settings as well.

---

## Navigation modes

The top bar has four modes:

| Mode | Purpose |
|------|---------|
| **Catalog** | Browse, start/stop, and run tools from the 400-server marketplace |
| **Chat** | Conversational assistant with dynamic MCP tool binding |
| **Prompt** | Single-shot prompts against selected tools |
| **✦ Nova** | Agentic chat with avatar and multi-step tool execution |

Switch modes without losing server state — running containers stay up across tabs.

---

## Catalog — browse and run tools

The **Catalog** is the primary way to discover and operate MCP servers.

### Finding servers

- **Search** by name or keyword in the search bar.
- **Filter by category** (recon, vuln-scanning, osint, cloud-container, misc, etc.).
- **Status chips** show whether a server is running, stopped, or disabled.

Each card shows the server name, category, whether an API key is required, and quick actions.

### Server lifecycle

| Action | What it does |
|--------|--------------|
| **Start** (▶) | Launches the Docker container for that MCP server |
| **Stop** (■) | Stops the container; routing can remain enabled |
| **Disable** (⊘) | Removes the server from Caddy routing (requests return 404) |
| **Enable** (✓) | Re-adds routing without necessarily starting the container |

> Servers use `restart: no` by default — they only run when you start them. Start only what you need to conserve RAM.

### Server detail view

Click a server card to open **Server Detail**:

- Full README (tools, parameters, examples)
- **Environment variables** — set vendor API keys before starting
- **Tool list** — live `tools/list` from the running server
- **Run tool** — execute a tool with JSON arguments and view formatted results
- **Logs** — recent container stdout/stderr

### Adding custom servers

Use **+ Add Server** to register:

- **Docker image** — a `hackerdogs/*` image or your own registry
- **External URL** — any HTTP MCP endpoint reachable from the farm network

Imported Claude Desktop / Cursor configs are also supported via the admin API (`POST /admin/servers/import`).

---

## Connecting external MCP clients

The farm exposes every running server at a single base URL:

```
http://<farm-host>:8485/<server-name>/mcp
```

Production example:

```
https://mcpservers.example.com/naabu-mcp/mcp
```

All farm requests require an API key:

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

Use this config in **Cursor**, **Claude Desktop**, or the **MCP Inspector** (`npx @modelcontextprotocol/inspector`).

---

## Chat mode

**Chat** provides a conversational interface with **dynamic tool binding** — the farm's vector index suggests relevant MCP tools based on your message.

### How it works

1. You type a natural-language request (e.g. *"find subdomains for example.com"*).
2. The farm searches its Redis vector index for matching tools (`subfinder`, `assetfinder`, etc.).
3. Selected tools appear as chips above the composer.
4. The LLM can call those tools; results stream back into the thread.

### Provider and model

Use the **provider/model bar** above the chat input to choose:

- **OpenAI**, **Claude**, **Ollama** (local), **Bedrock**, **Azure OpenAI**, **OpenRouter**, **Grok**, **Gemini**

Provider API keys are stored **server-side** in the encrypted LLM vault (Settings) — they never sit in browser localStorage.

### Tool picker

Click the **tools button** in the composer to manually pin specific MCP servers for the next turn, overriding auto-selection.

---

## Prompt mode

**Prompt** is for focused, single-request workflows:

1. Select one or more MCP servers from the sidebar.
2. Write a prompt describing what you want.
3. The UI calls the selected tools directly and shows structured results.

Use Prompt when you already know which tool to run and do not need conversational context.

---

## Nova (agent mode)

**✦ Nova** is the agentic interface — multi-step reasoning with live tool execution and an optional HeyGen avatar.

Nova uses the same MCP runtime as Chat but runs a longer agent loop: plan → call tools → interpret results → respond. Configure avatar settings (HeyGen API key, avatar ID) in **Settings** if you want the visual presenter.

---

## Settings

Open **Settings** from the gear icon.

### Connection

| Field | Description |
|-------|-------------|
| **Base URL** | Farm endpoint (e.g. `http://localhost:8485`) |
| **Active API Key** | Bearer token this browser uses for MCP calls |
| **Admin Secret** | Password for admin endpoints (server start/stop, key management) |

### API key management

**Settings → API key management** lists farm Bearer keys in a table. **Create key** issues a new token (plaintext shown once). **Refresh** reloads the list. **Revoke** deletes a key immediately.

### LLM provider keys (server-side vault)

Keys for OpenAI, Claude, Bedrock, Azure, OpenRouter, Grok, and Gemini are sent to the auth gateway and stored **encrypted** (Fernet). The UI only shows masked prefixes (e.g. `sk-…abc`).

To update a key: enter the new value and click **Save**. To remove: clear the field and save, or use the admin API `DELETE /llm-keys/{provider}`.

### Ollama (local LLM)

Set **Ollama URL** (default `http://host.docker.internal:11434`) to use local models without cloud API keys.

### Rotate admin secret

**Rotate** generates a new admin secret. Save it immediately — it is shown only in the Settings field after rotation.

---

## API keys

### Your personal API key

Created automatically on first deploy. Used in:

- MCP client `Authorization: Bearer` headers
- UI API calls (list services, run tools)

### Creating additional keys

Use **Settings → API Keys → Create**, or the admin API:

```bash
curl -X POST "http://localhost:8485/admin/keys" \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "ci-runner", "scopes": "*"}'
```

Keys can be scoped to specific servers and rate-limited. Revoke with `DELETE /admin/keys/{id}`.

---

## Common workflows

### Run a port scan

1. Open **Catalog** → search `naabu`.
2. Click **Start** on `naabu-mcp`.
3. Open the server detail → **Run tool** → `run_naabu` with `{"host": "scanme.nmap.org"}`.

Or ask in **Chat**: *"Use naabu to scan scanme.nmap.org"*.

### Set a vendor API key

1. Open server detail for e.g. `virustotal-mcp`.
2. Under **Environment**, set `VIRUSTOTAL_API_KEY`.
3. **Restart** the server if it was already running.

### Export your farm config

```bash
curl "http://localhost:8485/admin/export" \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Authorization: Bearer $API_KEY" \
  | python3 -m json.tool > farm-backup.json
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| UI shows "failed to load servers" | Check **Base URL** and **API Key** in Settings; verify `curl http://localhost:8485/health` |
| Tool call returns 401 | API key missing or revoked — create a new key |
| Tool call returns 502 | Server not started — go to Catalog and click **Start** |
| Chat has no tool suggestions | Run `POST /admin/vectors/reindex` (operator) or set `VECTOR_AUTO_REINDEX=true` |
| Server requires API key badge | Set env vars in server detail before starting |
| Out of memory | Stop unused servers; avoid `--start-all` on machines with < 16 GB RAM |

### View logs

From the server detail page, or via CLI:

```bash
docker logs naabu-mcp
docker logs mcpfarm-auth
docker logs mcpfarm-caddy
```

---

## Further reading

- [mcpfarm/DEPLOY.md](../../mcpfarm/DEPLOY.md) — deployment, admin API, production checklist
- [README — MCP Farm](../../README.md#mcp-farm) — architecture overview
- [README — Individual servers](../../README.md#deploy-individual-servers-without-the-farm) — run tools without the farm
- Per-tool docs: `<tool>-mcp/README.md` (linked from Catalog server detail)
