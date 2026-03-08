# Hackerdogs API & MCP Server User Guide

This guide covers two ways to interact with Hackerdogs programmatically:

1. **MCP Server** -- Connect from Claude, Cursor, or any MCP-compatible client. The AI calls Hackerdogs tools directly.
2. **REST API** -- Call the Scheduled Prompts, Conversation, Briefings, and Chat Completions endpoints over HTTP with an API key.

Both methods require a Hackerdogs API key.

---

## Prerequisites: Creating an API Key

1. Log in to Hackerdogs at [https://preview.hackerdogs.ai](https://preview.hackerdogs.ai).
2. Navigate to **API Keys** (sidebar or User Settings).
3. Click **Create API Key**, give it a name, and copy the key (format: `hd-...`).
4. Store it securely -- it is shown only once.

---

# Section 1: Using the Hackerdogs MCP Server

The MCP (Model Context Protocol) server lets AI assistants call Hackerdogs tools -- schedule prompts, retrieve conversations, search intelligence briefings, and manage schedules -- through a standardized protocol.

**MCP Server URL:** `https://preview.hackerdogs.ai/mcp/`
**Transport:** streamable-http
**Authentication:** `Authorization: Bearer hd-YOUR_API_KEY` header on every request.

## MCP Tools Reference

### Scheduled Prompts Tools

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `get_llm_options` | `enabled_only` (bool, default `true`) | List LLM provider/model pairs available for scheduling. Call first when creating a schedule to discover valid models. Returns `items` (list of `{provider, model}`) and `default`. |
| `get_schedule_types` | *(none)* | List schedule types allowed by the user's subscription plan (e.g. `once`, `daily`, `weekly`). **Always call before creating/updating a schedule** -- the API returns 403 if the type is not allowed. |
| `list_schedules` | `search` (str, optional), `status_filter` (`all`/`active`/`inactive`), `order_by` (`next_run_asc`/`next_run_desc`/`prompt_asc`/`prompt_desc`), `limit` (1-500), `offset` (int) | List the user's scheduled prompts with optional filters. Returns `items`, `total`, `limit`, `offset`. |
| `get_schedule` | `schedule_id` (str, required) | Fetch full details of a single schedule (prompt text, LLM config, next run, conversation_id). |
| `create_schedule` | `llm_prompt_template` (str, required), `schedule_type` (str, default `"once"`), `start_at` (ISO 8601, required), `llm_config` (object, optional), `system_prompt` (str, optional), `tool_config` (object, optional), `use_agentic_mode` (bool, optional), `conversation_id` (str, optional) | Create a schedule for a future or recurring run. Returns `id` and `next_run_at`. Pass `conversation_id` to continue in an existing conversation. |
| `schedule_now` | `prompt` (str, required), `llm_config` (object, optional), `schedule_type` (str, default `"once"`), `system_prompt` (str, optional), `conversation_id` (str, optional) | Create a schedule and run it immediately. Returns `schedule_id`, `task_id`, `conversation_id`, `message`. The run executes in the background. Pass `conversation_id` to continue in an existing conversation. |
| `run_schedule_now` | `schedule_id` (str, required) | Trigger an existing schedule to run immediately. Returns `task_id`, `conversation_id`. |
| `update_schedule` | `schedule_id` (str, required), plus any of: `llm_prompt_template`, `schedule_type`, `start_at`, `llm_config`, `system_prompt`, `tool_config`, `use_agentic_mode` | Partial update of an existing schedule. Send only the fields to change. Note: to update `conversation_id`, use the REST API PATCH endpoint directly (not exposed in the MCP tool). |
| `delete_schedule` | `schedule_id` (str, required) | Permanently delete a scheduled prompt. |

### Conversation Tools

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `list_conversations` | `limit` (int, 1-250, default 250), `offset` (int, default 0), `search` (str, optional), `from_date` (ISO 8601, optional), `to_date` (ISO 8601, optional) | List the user's conversations (chat history feed). Returns conversation_id, session_name, message_count, latest_message_time, and up to 5 message previews per conversation. Use `search` to filter by session name or message content. |
| `get_conversation` | `conversation_id` (str, required) | Fetch the full conversation packet from storage: `files`, `deliverable_groups` (docs/reports with full URLs), `evidence_items` (tool output links with full URLs), `evidence_files` (all tool/evidence blobs with direct URLs), and `execution_complete` (bool — `true` when the run is finished). **Poll until `execution_complete` is `true`** before treating the run as complete. Call after `schedule_now` or `run_schedule_now`. |
| `delete_conversation` | `conversation_id` (str, required) | Delete a conversation and all stored files. |

### Briefings Tools

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `list_briefings` | `limit` (int, 1-100, default 10), `offset` (int, default 0) | List intelligence briefing documents ordered by newest first. Paged via limit/offset. |
| `search_briefings` | `query` (str, required), `query_type` (`keyword_search`/`vector_search`/`hybrid_search`, default `hybrid_search`), `limit` (int, 1-100), `offset` (int), `alpha` (float 0-1, hybrid only), `category` (str, optional), `classification` (str, optional) | Search intelligence briefings by keyword (BM25), semantic similarity (vector), or both (hybrid). Filter by category or classification. |
| `get_similar_briefings` | `query` (str, optional), `message_id` (str, optional), `brief_id` (str, optional), `query_type` (`vector_search`/`hybrid_search`), `limit` (int, 1-100), `offset` (int), `alpha` (float 0-1) | Find briefings similar to a query, a chat message, or another briefing. Provide at least one of query/message_id/brief_id. |

### MCP Resources (Read-Only References)

| Resource URI | Name | Description |
|--------------|------|-------------|
| `hackerdogs://docs/workflow` | Schedule workflow guide | Guidance for using Hackerdogs schedule tools: tool order, when to call `get_schedule_types`, and `schedule_now` vs `create_schedule`. |

Resources are read-only documents that LLMs can fetch for context. They do not perform actions.

### MCP Prompts (Reusable Templates)

| Prompt Name | Parameters | Description |
|-------------|-----------|-------------|
| `schedule_run_now` | `prompt` (str, required), `schedule_type` (str, default `"once"`) | Template for running a prompt immediately via `schedule_now`. |
| `create_schedule_later` | `prompt` (str), `schedule_type` (str), `start_at` (ISO 8601) | Template for creating a schedule at a future time via `create_schedule`. |
| `list_schedules_help` | `search` (str, optional), `status_filter` (str, default `"all"`), `limit` (int, default 20) | Template for listing schedules, optionally with a search filter. |

Prompts are reusable message templates that LLMs can invoke to structure tool-calling workflows.

### MCP Server Configuration

**Environment variables** (optional -- only needed for standalone/stdio mode; streamable-http clients send `Authorization: Bearer` instead):

| Variable | Default | Description |
|----------|---------|-------------|
| `HACKERDOGS_API_KEY` (or `API_KEY`) | -- | API key for backend calls. Not needed when the client sends `Authorization: Bearer <key>`. |
| `HACKERDOGS_API_BASE_URL` (or `BACKEND_URL`) | `http://localhost:8000` | Backend base URL. |
| `HACKERDOGS_MCP_HTTP_TIMEOUT` | `60` | HTTP timeout in seconds for backend calls. |
| `HACKERDOGS_MCP_HTTP_RETRIES` | `1` | Number of retries on 5xx backend errors. |

## Installing in Claude Desktop

Add to your `claude_desktop_config.json` (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "hackerdogs": {
      "url": "https://preview.hackerdogs.ai/mcp/",
      "headers": {
        "Authorization": "Bearer hd-YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Restart Claude Desktop. The Hackerdogs tools will appear in the tools panel.

## Installing in Cursor

Add to `.cursor/mcp.json` in your project root (or global settings):

```json
{
  "mcpServers": {
    "hackerdogs": {
      "url": "https://preview.hackerdogs.ai/mcp/",
      "headers": {
        "Authorization": "Bearer hd-YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Restart Cursor. The tools will appear as MCP tools available to the AI.

## Installing via Hackerdogs Tools Catalog

1. Log in to Hackerdogs at [https://preview.hackerdogs.ai](https://preview.hackerdogs.ai).
2. Go to **API Keys** and create a key (if you haven't already). Copy the key.
3. Go to **Tools Catalog** (sidebar).
4. Find the **Hackerdogs MCP Server** entry.
5. Paste your API key and click **Install**.
6. The config snippet is generated for you -- copy it into Claude or Cursor as shown above.

## Sample Prompts & Use Cases

### Basic: Attack Surface Analysis

> Run a comprehensive attack surface analysis on hackerdogs.ai. Identify all exposed services, open ports, subdomains, and potential entry points. Create a risk report.

The AI will call `schedule_now` with this prompt. Hackerdogs runs the analysis using its OSINT tools and returns a conversation_id. The AI then calls `get_conversation` to retrieve the full report with deliverables.

### Basic: User Enumeration

> Enumerate all publicly discoverable users, emails, and social profiles associated with the domain example.com. Check for credential leaks and breached accounts.

### Scheduled: Daily Threat Monitoring

> "Schedule a daily check: find today's top 10 cybersecurity incidents and breaches. Correlate with our infrastructure and create a risk report."

The AI calls `get_schedule_types` to confirm `daily` is allowed, then `create_schedule` with `schedule_type="daily"` and `start_at` set to tomorrow at 8:00 AM UTC.

### Advanced: Continuing an Existing Conversation

When you want to build on a previous analysis instead of starting fresh, pass the `conversation_id` from a prior run:

> "Using the conversation from our last attack surface scan (conversation_id: 01KJVJ4FHWEV43MR1A9YKCG3NB), now run a deeper analysis on the 3 highest-risk findings. Add port scanning and vulnerability assessment."

The AI calls:
```
schedule_now(
  prompt="Deeper analysis on the 3 highest-risk findings...",
  conversation_id="01KJVJ4FHWEV43MR1A9YKCG3NB"
)
```

The new run continues in the same conversation thread, with access to the prior context.

### Advanced: Multi-Step Recursive Analysis

This pattern chains multiple Hackerdogs runs, where each step feeds the next:

**Step 1 -- Initial reconnaissance:**
> "Run an initial reconnaissance on target.com: subdomains, DNS records, WHOIS, tech stack detection."

The AI calls `schedule_now`, waits for completion, calls `get_conversation` to get results, and extracts the conversation_id (e.g., `01KJX...`).

**Step 2 -- Deep dive using step 1's conversation:**
> "Continue the investigation in conversation 01KJX... -- for each subdomain found, run port scanning and service fingerprinting. Focus on anything that looks like a staging or dev environment."

The AI calls `schedule_now` with the same `conversation_id`, building on the previous findings.

**Step 3 -- Vulnerability assessment:**
> "Still in conversation 01KJX... -- take the exposed services from step 2 and check for known CVEs, misconfigurations, and default credentials. Generate a prioritized vulnerability report."

Each step enriches the same conversation, creating a comprehensive investigation thread.

### Advanced: Creating a New Conversation for Comparison

> "Run the same attack surface analysis as conversation 01KJX... but against staging.target.com. I want a separate conversation so I can compare them side by side."

Here, the AI omits `conversation_id` so Hackerdogs creates a fresh one. The user ends up with two independent conversation threads to compare.

---

# Section 2: Using the Hackerdogs REST API

The REST API provides direct HTTP access to four API groups:

- **Scheduled Prompts API** (`/scheduled-prompts-api`) -- Create, manage, and run scheduled prompts.
- **Conversation API** (`/conversation-api`) -- List, retrieve, or delete conversation results. Includes `execution_complete` flag for reliable polling.
- **Briefings API** (`/briefings-api`) -- List, search (keyword/vector/hybrid), and find similar intelligence briefings stored in the vector database.
- **Chat Completions API** (`/v1`) -- OpenAI-compatible streaming chat endpoint.

**Base URL:** `https://preview.hackerdogs.ai`
**Authentication:** `X-API-Key: hd-YOUR_KEY` header (all endpoints), or `Authorization: Bearer hd-YOUR_KEY` (Chat Completions).

## 2.1 Scheduled Prompts API

Base path: `/scheduled-prompts-api`

### Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/llm-options` | List available LLM provider/model pairs | 200 |
| GET | `/schedule-types` | List schedule types allowed by plan | 200 |
| GET | `/schedules` | List scheduled prompts (with filters) | 200 |
| GET | `/schedules/{id}` | Get one schedule by ID | 200 |
| POST | `/schedules` | Create a schedule (future/recurring) | 201 |
| PATCH | `/schedules/{id}` | Partial update of a schedule | 200 |
| DELETE | `/schedules/{id}` | Delete a schedule | 200 |
| POST | `/schedule-now` | Create + run immediately | 202 |
| POST | `/schedules/{id}/run-now` | Run existing schedule now | 202 |

### POST /schedule-now (Create + Run Immediately)

The most common endpoint. Creates a schedule and runs it in one call.

**Request:**

```bash
curl -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Find today'\''s top 10 cybersecurity attacks and breaches. Summarize the findings.",
    "schedule_type": "once"
  }'
```

**Response (202):**

```json
{
  "schedule_id": "01KJVJ4FHFTEH1F1YZGHEB6C4W",
  "task_id": "01KJVJ4FHWEV43MR1A9YKCG3N9",
  "conversation_id": "01KJVJ4FHWEV43MR1A9YKCG3NB",
  "message": "Schedule triggered; conversation will appear in Chat."
}
```

The run executes in the background. Use the `conversation_id` to retrieve results.

**Request body fields:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `prompt` | Yes | string | The prompt to execute (or `llm_prompt_template`). |
| `llm_config` | No | object | `{"provider": "openai", "model": "gpt-4o-mini"}`. If omitted, uses your default LLM from User Settings. |
| `schedule_type` | No | string | Default `"once"`. Must be allowed by your plan (call GET `/schedule-types` first). |
| `system_prompt` | No | string | Custom system prompt for this run. |
| `conversation_id` | No | string | Continue in an existing conversation instead of creating a new one. |
| `tool_config` | No | object | Tool configuration for agentic mode. |
| `use_agentic_mode` | No | bool | Enable/disable tools. Defaults to your User Settings value. |

### POST /schedule-now with conversation_id (Continue Existing Conversation)

```bash
# Step 1: Initial run (new conversation)
RESULT=$(curl -s -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Reconnaissance on target.com: subdomains, DNS, WHOIS."}')

CONV_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['conversation_id'])")
echo "Conversation ID: $CONV_ID"

# Step 2: Continue in the same conversation
curl -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"Now run port scanning on the subdomains found. Focus on staging environments.\",
    \"conversation_id\": \"$CONV_ID\"
  }"
```

### POST /schedules (Create for Future/Recurring)

```bash
curl -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_prompt_template": "Daily threat intel: top cybersecurity incidents in the last 24 hours.",
    "schedule_type": "daily",
    "start_at": "2026-03-05T08:00:00Z"
  }'
```

**Request body fields:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `llm_prompt_template` | Yes | string | The prompt template to execute on each run. |
| `schedule_type` | Yes | string | Must be allowed by your plan (call GET `/schedule-types` first). |
| `start_at` | Yes | string | ISO 8601 datetime for first run (e.g. `2026-03-05T08:00:00Z`). |
| `llm_config` | No | object | `{"provider": "...", "model": "..."}`. Uses your default LLM if omitted. |
| `system_prompt` | No | string | Custom system prompt. |
| `conversation_id` | No | string | Continue in an existing conversation on each run. |
| `tool_config` | No | object | Tool configuration for agentic mode. |
| `use_agentic_mode` | No | bool | Enable/disable tools. Defaults to your User Settings value. |

**Response (201):**

```json
{
  "id": "01KJXYZ...",
  "next_run_at": "2026-03-05T08:00:00+00:00"
}
```

### GET /schedules (List)

```bash
curl "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules?status_filter=active&limit=10" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Query parameters:** `search` (text filter), `status_filter` (`all`|`active`|`inactive`), `order_by` (`next_run_asc`|`next_run_desc`|`prompt_asc`|`prompt_desc`), `limit` (1-500), `offset`.

### GET /schedules/{id} (Get One)

```bash
curl "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules/01KJXYZ..." \
  -H "X-API-Key: hd-YOUR_KEY"
```

Returns the full schedule object including `conversation_id`, `llm_config`, `next_run_at`, etc.

### PATCH /schedules/{id} (Partial Update)

Send only the fields you want to change.

```bash
curl -X PATCH "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules/01KJXYZ..." \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_prompt_template": "Updated prompt: include ransomware incidents only.",
    "conversation_id": "01KJVJ4FHWEV43MR1A9YKCG3NB"
  }'
```

**Updatable fields:** `llm_prompt_template`, `schedule_type`, `start_at`, `llm_config`, `tool_config`, `use_agentic_mode`, `system_prompt`, `conversation_id`.

**Response (200):** `{"id": "01KJXYZ...", "updated": true}`

### DELETE /schedules/{id}

```bash
curl -X DELETE "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules/01KJXYZ..." \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Response (200):** `{"message": "Schedule 01KJXYZ... has been successfully deleted."}`

### POST /schedules/{id}/run-now (Trigger Existing)

```bash
curl -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules/01KJXYZ.../run-now" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Response (202):** `{"id": "01KJXYZ...", "task_id": "...", "conversation_id": "...", "message": "..."}`

### Error Codes

| Code | Meaning |
|------|---------|
| 401 | Missing or invalid API key |
| 402 | Insufficient credits or tenant credit limit reached |
| 403 | Plan does not support the requested `schedule_type` (upgrade required) |
| 404 | Schedule or endpoint not found |
| 422 | Validation error (missing prompt, invalid schedule_type, etc.) |
| 503 | Service unavailable (backend, DB, or credit check) |

---

## 2.2 Conversation API

Base path: `/conversation-api`

Conversations are the output of scheduled prompt runs. Each run produces files, deliverables (reports/documents), and evidence items (tool outputs) stored in the conversation.

### Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/conversations` | List conversations (chat history) | 200 |
| GET | `/conversations/{conversation_id}` | Get full conversation packet | 200 |
| DELETE | `/conversations/{conversation_id}` | Delete conversation + stored files | 200 |

### GET /conversations (List)

```bash
curl "https://preview.hackerdogs.ai/conversation-api/conversations?limit=10&search=target.com" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Query parameters:** `limit` (1-250, default 250), `offset`, `search` (ILIKE over session name and message content), `from_date` (ISO 8601), `to_date` (ISO 8601).

Returns an array of conversation summaries, each with `conversation_id`, `session_name`, `message_count`, `latest_message_time`, and up to 5 message previews.

### GET /conversations/{conversation_id}

Retrieve the complete conversation output after a run completes.

```bash
curl "https://preview.hackerdogs.ai/conversation-api/conversations/01KJVJ4FHWEV43MR1A9YKCG3NB" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Response (200):**

```json
{
  "conversation_id": "01KJVJ4FHWEV43MR1A9YKCG3NB",
  "user_id": "...",
  "tenant_id": "...",
  "files": [
    {"path": "chat/user_id/conv_id/content.json", "content": {...}},
    {"path": "chat/user_id/conv_id/report.md", "content": "..."}
  ],
  "deliverable_groups": [
    {
      "title": "Reports",
      "deliverables": [
        {"display_name": "Risk Report", "url": "https://...signed-url..."}
      ]
    }
  ],
  "evidence_items": [
    {"tool_name": "nmap_scan", "url": "https://...signed-url..."}
  ],
  "evidence_files": [
    {"blob_name": "...", "url": "https://...signed-url..."}
  ],
  "execution_complete": true
}
```

**Fields:**

| Field | Description |
|-------|-------------|
| `files` | All objects stored for this conversation (path + content). |
| `deliverable_groups` | Grouped documents/reports with presigned download URLs. Same structure as webhooks and email notifications. |
| `evidence_items` | Tool output references extracted from content files, with presigned URLs. |
| `evidence_files` | All tool/evidence blobs with direct download URLs. |
| `execution_complete` | `true` when the run is finished (the txtanalytics completed marker exists in storage). **Poll until this is `true`** before treating the run as complete. |

### DELETE /conversations/{conversation_id}

```bash
curl -X DELETE "https://preview.hackerdogs.ai/conversation-api/conversations/01KJVJ4FHWEV43MR1A9YKCG3NB" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Response (200):**

```json
{
  "success": true,
  "conversation_id": "01KJVJ4FHWEV43MR1A9YKCG3NB",
  "deleted_count": 15,
  "storage_deleted_count": 8
}
```

### Full Workflow: Schedule + Wait + Get Conversation

**Important:** A conversation returns 200 as soon as the first file is written, but deliverables and evidence may still be arriving. Poll until `execution_complete` is `true` before considering the result final. The Python clients (`schedule_now_and_wait`) handle this automatically.

```bash
# 1. Schedule and run
RESULT=$(curl -s -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Enumerate subdomains for example.com and check for takeover vulnerabilities."}')

echo "$RESULT"
CONV_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['conversation_id'])")

# 2. Wait for completion (poll until execution_complete is true)
echo "Waiting for conversation $CONV_ID..."
for i in $(seq 1 30); do
  sleep 10
  RESP=$(curl -s \
    "https://preview.hackerdogs.ai/conversation-api/conversations/$CONV_ID" \
    -H "X-API-Key: hd-YOUR_KEY")
  COMPLETE=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('execution_complete', False))" 2>/dev/null || echo "False")
  echo "  Poll $i: execution_complete=$COMPLETE"
  if [ "$COMPLETE" = "True" ]; then
    echo "  Execution complete. Done."
    break
  fi
done

# 3. Get the full packet
curl -s "https://preview.hackerdogs.ai/conversation-api/conversations/$CONV_ID" \
  -H "X-API-Key: hd-YOUR_KEY" | python3 -m json.tool
```

---

## 2.3 Briefings API

Base path: `/briefings-api`

Intelligence briefings are auto-generated threat intelligence documents produced during conversation runs (via the txtanalytics pipeline) and stored in a vector database (Weaviate). You can list, search (keyword, semantic, or hybrid), and find similar briefings.

### Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/briefings` | List briefings (paged, newest first) | 200 |
| GET | `/briefings/search` | Search briefings by keyword, semantic, or hybrid | 200 |
| GET | `/briefings/similar` | Find briefings similar to a query, message, or another briefing | 200 |

### Briefing Item Fields

Each briefing item in the response `items` array contains:

| Field | Type | Description |
|-------|------|-------------|
| `brief_id` | string | Unique identifier for the briefing document. |
| `message_id` | string | ID of the chat message that generated this briefing. |
| `conversation_id` | string | ID of the conversation the briefing belongs to. |
| `title` | string | Title of the intelligence briefing. |
| `classification` | string | Classification level (e.g. `"UNCLASSIFIED"`, `"CONFIDENTIAL"`). |
| `category` | string | Category of the briefing (e.g. `"Threat Intelligence"`, `"Vulnerability Assessment"`). |
| `time_sensitivity` | string | Time sensitivity indicator (e.g. `"HIGH"`, `"MEDIUM"`, `"LOW"`). |
| `created_at` | string | ISO 8601 timestamp of when the briefing was created. |
| `storage_path` | string | Storage path of the original briefing document. |
| `content` | string | Full text content of the intelligence briefing (Markdown). |
| `user_id` | string | Owner user ID. |
| `tenant_id` | string | Owner tenant ID. |

### GET /briefings (List)

```bash
curl "https://preview.hackerdogs.ai/briefings-api/briefings?limit=5" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Query parameters:** `limit` (1-100, default 10), `offset` (default 0).

**Response (200):**

```json
{
  "items": [
    {
      "brief_id": "abc123",
      "message_id": "01KJVJ...",
      "conversation_id": "01KJVJ...",
      "title": "Critical Ransomware Campaign Targeting Healthcare Sector",
      "classification": "UNCLASSIFIED",
      "category": "Threat Intelligence",
      "time_sensitivity": "HIGH",
      "created_at": "2026-03-04T14:30:00Z",
      "storage_path": "chat/.../intelligence_brief.md",
      "content": "# Intelligence Brief\n\n## Executive Summary\n..."
    }
  ],
  "limit": 5,
  "offset": 0,
  "has_more": true
}
```

### GET /briefings/search

```bash
curl "https://preview.hackerdogs.ai/briefings-api/briefings/search?query=ransomware+2026&query_type=hybrid_search&limit=5" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Query parameters:**

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `query` | Yes | string | -- | Search query text. |
| `query_type` | No | string | `hybrid_search` | One of `keyword_search` (BM25), `vector_search` (semantic), or `hybrid_search` (both). |
| `limit` | No | int | 10 | Results per page (1-100). |
| `offset` | No | int | 0 | Pagination offset. |
| `alpha` | No | float | 0.5 | Hybrid weighting (0 = pure keyword, 1 = pure vector). Only applies to `hybrid_search`. |
| `category` | No | string | -- | Filter by briefing category. |
| `classification` | No | string | -- | Filter by classification level. |

**Response (200):**

```json
{
  "items": [
    {
      "brief_id": "abc123",
      "title": "Ransomware-as-a-Service Ecosystem Analysis",
      "classification": "UNCLASSIFIED",
      "category": "Threat Intelligence",
      "time_sensitivity": "HIGH",
      "created_at": "2026-03-04T14:30:00Z",
      "content": "# Intelligence Brief\n\n## Executive Summary\n..."
    }
  ],
  "limit": 5,
  "offset": 0,
  "has_more": false,
  "query_type": "hybrid_search"
}
```

### GET /briefings/similar

```bash
curl "https://preview.hackerdogs.ai/briefings-api/briefings/similar?query=APT29+campaign+tactics&limit=5" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Query parameters:** At least one of `query`, `message_id`, or `brief_id` is required. Also: `query_type` (`vector_search`|`hybrid_search`), `limit`, `offset`, `alpha`.

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `query` | One of three | string | -- | Free-text query for similarity matching. |
| `message_id` | One of three | string | -- | Find briefings similar to this chat message's briefing. |
| `brief_id` | One of three | string | -- | Find briefings similar to this briefing. |
| `query_type` | No | string | `hybrid_search` | `vector_search` or `hybrid_search`. |
| `limit` | No | int | 10 | Results per page (1-100). |
| `offset` | No | int | 0 | Pagination offset. |
| `alpha` | No | float | 0.5 | Hybrid weighting (0 = pure keyword, 1 = pure vector). |

**Response (200):** Same shape as search — `items`, `limit`, `offset`, `has_more`, `query_type`.

### Error Codes (Briefings)

| Code | Meaning |
|------|---------|
| 400 | Missing required parameter (e.g. no `query` and no `message_id`/`brief_id` for similar) |
| 401 | Missing or invalid API key |
| 500 | Internal server error (Weaviate unavailable, serialization failure, etc.) |

---

## 2.4 Chat Completions API (OpenAI-compatible)

Base path: `/v1`

Drop-in replacement for the OpenAI Chat Completions API. Compatible with Open WebUI, LangChain, and any OpenAI SDK client. Supports streaming (SSE) and non-streaming modes.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat/completions` | Chat completion (stream or non-stream) |
| GET | `/v1/models` | List available models |

### Authentication

Use `Authorization: Bearer hd-YOUR_KEY` (preferred) or `X-API-Key: hd-YOUR_KEY`.

### POST /v1/chat/completions (Streaming)

```bash
curl -X POST "https://preview.hackerdogs.ai/v1/chat/completions" \
  -H "Authorization: Bearer hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a cybersecurity analyst."},
      {"role": "user", "content": "Analyze the attack surface of example.com"}
    ],
    "stream": true
  }'
```

Streams Server-Sent Events (SSE) in OpenAI format:

```
data: {"id":"chatcmpl-01KJX...","object":"chat.completion.chunk","model":"gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":"Based on"},"finish_reason":null}]}

data: {"id":"chatcmpl-01KJX...","object":"chat.completion.chunk","model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":" my analysis"},"finish_reason":null}]}

...

data: {"id":"chatcmpl-01KJX...","object":"chat.completion.chunk","model":"gpt-4o-mini","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":25,"completion_tokens":150,"total_tokens":175}}

data: [DONE]
```

### POST /v1/chat/completions (Non-streaming)

```bash
curl -X POST "https://preview.hackerdogs.ai/v1/chat/completions" \
  -H "Authorization: Bearer hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What are the OWASP Top 10 for 2025?"}
    ],
    "stream": false
  }'
```

**Response:**

```json
{
  "id": "chatcmpl-01KJX...",
  "object": "chat.completion",
  "model": "gpt-4o-mini",
  "created": 1709510400,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The OWASP Top 10 for 2025..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 200,
    "total_tokens": 212
  }
}
```

### Request Body

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `messages` | array (required) | -- | Array of `{role, content}` objects. Roles: `system`, `user`, `assistant`, `tool`. |
| `stream` | bool | `true` | Stream SSE chunks or return single JSON response. |
| `model` | string | user's default | Override the model (must be available in your account). |
| `temperature` | float | user's default | Sampling temperature. |
| `max_tokens` | int | user's default | Maximum tokens to generate. |
| `tools` | array/bool | `true` (all tools) | Pass `false` or `[]` to disable tools. Pass `null` or omit for all tools. |

### GET /v1/models

```bash
curl "https://preview.hackerdogs.ai/v1/models" \
  -H "Authorization: Bearer hd-YOUR_KEY"
```

**Response:**

```json
{
  "object": "list",
  "data": [
    {"id": "openai/gpt-4o-mini", "object": "model", "created": 0, "owned_by": "hackerdogs"},
    {"id": "anthropic/claude-sonnet-4-20250514", "object": "model", "created": 0, "owned_by": "hackerdogs"}
  ]
}
```

### Using with OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="hd-YOUR_KEY",
    base_url="https://preview.hackerdogs.ai/v1",
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a cybersecurity analyst with access to OSINT tools."},
        {"role": "user", "content": "Run a subdomain enumeration on example.com"},
    ],
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Using with Open WebUI

In Open WebUI settings, add a new connection:

- **API Base URL:** `https://preview.hackerdogs.ai/v1`
- **API Key:** `hd-YOUR_KEY`

Models will auto-populate from the `/v1/models` endpoint.

---

## Python Client Libraries

Hackerdogs ships Python clients for programmatic use:

### SchedulePromptNowClient

```python
from api_clients.sch.schedule_prompt_now_client import SchedulePromptNowClient

client = SchedulePromptNowClient(
    api_key="hd-YOUR_KEY",
    base_url="https://preview.hackerdogs.ai",
)

# Schedule and run now
result = client.schedule_now(prompt="Analyze attack surface of example.com")
print(result["conversation_id"])

# Schedule and run now, continuing an existing conversation
result = client.schedule_now(
    prompt="Now scan the top 3 subdomains for vulnerabilities.",
    conversation_id="01KJVJ4FHWEV43MR1A9YKCG3NB",
)

# Schedule and wait for full results
result = client.schedule_now_and_wait(
    prompt="Full OSINT report on target.com",
    wait_secs=300,
    poll_interval_sec=10,
)
print(result["conversation"])  # Full packet with deliverables and evidence
```

### ConversationClient

```python
from api_clients.conversation.conversation_client import ConversationClient

client = ConversationClient(
    api_key="hd-YOUR_KEY",
    base_url="https://preview.hackerdogs.ai",
)

# Get conversation
conv = client.get_conversation("01KJVJ4FHWEV43MR1A9YKCG3NB")
print(f"Files: {len(conv['files'])}")
print(f"Deliverables: {len(conv['deliverable_groups'])}")
print(f"Evidence: {len(conv['evidence_items'])}")

# Delete conversation
client.delete_conversation("01KJVJ4FHWEV43MR1A9YKCG3NB")
```

---

## Use Case Examples

### Automated Daily Threat Brief

```bash
# Create a daily schedule at 8 AM UTC
curl -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_prompt_template": "Generate a daily cybersecurity threat brief: top incidents in the last 24 hours, new CVEs affecting our tech stack (React, Python, PostgreSQL, nginx), and any relevant threat actor activity. Format as an executive summary.",
    "schedule_type": "daily",
    "start_at": "2026-03-05T08:00:00Z"
  }'
```

### Incident Response: Multi-Step Investigation

```bash
# Step 1: Initial triage
R1=$(curl -s -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Investigate IP 203.0.113.42: reverse DNS, geolocation, ASN, reputation checks, and any associated threat intelligence."}')
CONV=$(echo "$R1" | python3 -c "import sys,json; print(json.load(sys.stdin)['conversation_id'])")

# Step 2: Deeper investigation in same conversation
curl -s -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"Based on the findings, check if this IP has been involved in any botnets, C2 infrastructure, or scanning campaigns. Cross-reference with recent CVE exploits.\",
    \"conversation_id\": \"$CONV\"
  }"

# Step 3: Generate incident report
curl -s -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"Compile all findings into a formal incident report with timeline, IOCs, risk assessment, and recommended mitigations.\",
    \"conversation_id\": \"$CONV\"
  }"
```

### Competitive Intelligence

```bash
curl -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedule-now" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Perform OSINT on competitor.com: tech stack, infrastructure, recent changes, employee LinkedIn profiles in engineering roles, GitHub repos, and any public security disclosures. Create a competitive intelligence brief."
  }'
```

### Searching Intelligence Briefings

After runs produce intelligence briefings, use the Briefings API to search across them.

**Keyword search (BM25) for a specific CVE:**

```bash
curl "https://preview.hackerdogs.ai/briefings-api/briefings/search?query=CVE-2026-1234&query_type=keyword_search&limit=10" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Semantic search for a concept:**

```bash
curl "https://preview.hackerdogs.ai/briefings-api/briefings/search?query=supply+chain+attacks+on+npm+packages&query_type=vector_search&limit=5" \
  -H "X-API-Key: hd-YOUR_KEY"
```

**Hybrid search with category filter:**

```bash
curl "https://preview.hackerdogs.ai/briefings-api/briefings/search?query=ransomware+healthcare&query_type=hybrid_search&alpha=0.7&category=Threat+Intelligence&limit=10" \
  -H "X-API-Key: hd-YOUR_KEY"
```

### Finding Related Briefings

Find briefings similar to one you've already seen:

```bash
# By brief_id (from a previous list/search result)
curl "https://preview.hackerdogs.ai/briefings-api/briefings/similar?brief_id=abc123&limit=5" \
  -H "X-API-Key: hd-YOUR_KEY"

# By free-text query
curl "https://preview.hackerdogs.ai/briefings-api/briefings/similar?query=APT29+lateral+movement+techniques&limit=5" \
  -H "X-API-Key: hd-YOUR_KEY"
```

### Briefings + Scheduled Prompts Workflow

Combine scheduled prompts with briefing search for continuous threat monitoring:

```bash
# 1. Schedule a daily threat analysis that generates briefings
curl -X POST "https://preview.hackerdogs.ai/scheduled-prompts-api/schedules" \
  -H "X-API-Key: hd-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_prompt_template": "Analyze the top 10 cybersecurity incidents from the last 24 hours. For each, provide threat actor attribution, TTPs, IOCs, and recommended mitigations. Generate a comprehensive intelligence brief.",
    "schedule_type": "daily",
    "start_at": "2026-03-06T08:00:00Z"
  }'

# 2. Later, search across all generated briefings
curl "https://preview.hackerdogs.ai/briefings-api/briefings/search?query=critical+zero-day&query_type=hybrid_search&limit=10" \
  -H "X-API-Key: hd-YOUR_KEY"

# 3. Find briefings similar to a concerning finding
curl "https://preview.hackerdogs.ai/briefings-api/briefings/similar?query=nation-state+threat+actor+targeting+financial+sector&limit=5" \
  -H "X-API-Key: hd-YOUR_KEY"
```
