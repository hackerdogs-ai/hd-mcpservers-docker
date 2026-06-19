# Nova — AI Security Analyst Agent

Nova is the AI agent tab in the Hackerdogs MCP Security Farm UI. It combines a photorealistic talking avatar (HeyGen LiveAvatar) with Claude as the reasoning engine and the full MCP server farm as its toolset. When you ask Nova a security question, it selects the right tools, runs them, and explains the findings in plain English — both in text and through the avatar's voice.

---

## How It Works

```
User prompt
    │
    ▼
AgentChat.jsx
    │  builds system prompt with running + available server catalog
    │  loads tool schemas from all healthy MCP servers
    ▼
Claude API  (proxied through auth-gateway /claude)
    │  reasons about the task
    │  selects tools
    ▼
Tool calls → mcpClient → MCP servers (nmap, subfinder, nuclei, shodan, ...)
    │
    ▼
Tool results returned to Claude
    │
    ▼
Claude synthesises findings → plain-English response
    │
    ├── displayed in chat panel
    └── spoken by HeyGen LiveAvatar
```

The loop repeats (up to 10 iterations) until Claude signals `end_turn` — allowing multi-step investigations that chain tools automatically.

---

## Components

### `mcpfarm-ui/src/components/AgentChat.jsx`
The main Nova UI. Responsibilities:
- Splits `servers` prop into running (healthy) and available (not running)
- Builds a dynamic system prompt at query time that tells Claude which tools it can use now and which servers to suggest starting
- Loads tool schemas from all healthy servers via `mcpClient.listTools`
- Drives the `runChatTurn` agentic loop
- Renders the avatar panel (left) and chat panel (right)
- Calls `avatarRef.current.speak(text)` to make the avatar voice each response
- Shows live tool call cards with arguments and results (expandable)

### `mcpfarm-ui/src/components/HeyGenAvatar.jsx`
Streaming video avatar powered by the HeyGen LiveAvatar SDK.
- Creates a `LiveAvatarSession` (FULL mode) using the token endpoint at `https://api.liveavatar.com/v1/sessions/token`
- Attaches the WebRTC video stream to a `<video>` element on `SESSION_STREAM_READY`
- Exposes `speak(text)` and `interrupt()` via `forwardRef` / `useImperativeHandle`
- Sends a `keepAlive()` ping every 30 seconds to prevent session timeout
- Shows connecting / error / idle placeholder states when not streaming

### `mcpfarm-ui/src/lib/claude.js` — `runChatTurn`
Multi-turn agentic loop:
1. Appends the user message to the conversation history
2. Calls Claude with all available MCP tools in Anthropic tool format
3. On `tool_use` stop reason: routes each tool call to the correct MCP server via `mcpClient.callTool`, collects results, feeds them back to Claude
4. Repeats until `end_turn` or 10-iteration safety limit
5. Returns the updated message history for the next turn

### `mcpfarm-ui/src/lib/mcp.js` — `McpClient`
Thin MCP-over-HTTP client:
- `initialize(serverName)` — opens an MCP session (JSON-RPC `initialize` + `notifications/initialized`)
- `listTools(serverName)` — fetches available tools; auto-initialises if no session
- `callTool(serverName, toolName, args)` — executes a tool and returns the result
- Sessions are cached per server name and reused across calls
- All requests go through `{baseUrl}/{serverName}/mcp` (routed by Caddy → auth-gateway → MCP server)

### `mcpfarm/auth-gateway/main.py` — `/claude` proxy
Proxies Claude API calls from the browser to `api.anthropic.com` to avoid CORS restrictions.
- Accepts `POST /claude` with the standard Anthropic messages payload
- Reads the API key from the `x-claude-key` request header
- Forwards to `https://api.anthropic.com/v1/messages` and streams the response back

### `mcpfarm/auth-gateway/caddy_reload.py`
Contains the Caddy routing template. The `/claude` route is defined here so Caddy forwards POST requests to auth-gateway rather than serving a 404/405.

---

## System Prompt Design

Nova's system prompt is built dynamically on every request from two parts:

**1. Base instructions (`BASE_SYSTEM_PROMPT`)**
- Tool-use rules: call a tool first for any technical task; one sentence intro then act
- Explicit ban on text-only answers for security/investigation tasks
- Instructions for when tools are not running: name the specific servers needed

**2. Server catalog (built at runtime)**
```
## MCP SERVERS IN THIS FARM

### Currently running (you can call these now):
- nmap-mcp
- subfinder-mcp
- shodan-mcp
...

### Available but not running (suggest starting these when relevant):
- nuclei-mcp
- metasploit-mcp
- burpsuite-mcp
...
```

This means Nova knows your full server inventory even before any tool calls are made. If you ask "how do I find subdomains?" and subfinder-mcp is not running, Nova will tell you to start it by name rather than giving a generic "no tools available" error.

---

## Setup

### 1. Claude API Key
Go to **Settings → Claude API Key** and paste your `sk-ant-...` key. Nova proxies all Claude calls through the auth-gateway so the key never leaves your network.

### 2. HeyGen LiveAvatar (optional)
The talking avatar requires a LiveAvatar account (separate from HeyGen).

1. Sign up at [app.liveavatar.com](https://app.liveavatar.com)
2. Go to **Developers** → copy your API key
3. Create or pick an avatar → copy the Avatar ID
4. Go to **Settings → HeyGen API Key** and **Settings → HeyGen Avatar ID** in the UI

If no LiveAvatar credentials are set, Nova still works — the avatar panel shows a placeholder and chat functions normally.

### 3. Start MCP Servers
Go to the **Servers** tab and start the tools you want Nova to use. Nova will automatically pick up any healthy server. You don't need to restart Nova or refresh the page — the server list is queried fresh on every prompt.

---

## Behaviour Reference

| Scenario | Nova behaviour |
|---|---|
| User asks a technical question, tools running | Calls the most relevant tool immediately, reports findings |
| User asks a technical question, no tools running | Names the specific MCP servers needed and tells user to start them |
| User asks a general question | Answers directly, mentions which tools could provide deeper analysis |
| Tool call fails (error / timeout) | Shows error card, continues with remaining tools, reports partial findings |
| Avatar not configured | Chat works normally, no voice output |
| Claude key not set | Warning banner shown, no API calls made |

---

## Tool Call UI

Each tool call Nova makes is shown as a collapsible card in the chat:

- **Yellow spinner** — tool is running
- **Green ✓** — completed successfully (click to expand arguments + result)
- **Red ✗** — tool returned an error (click to see error message)

The avatar speaks Nova's text responses but does not read out raw tool output.

---

## Architecture Notes

- The browser never calls `api.anthropic.com` directly. All Claude traffic goes through `POST /claude` on the auth-gateway to avoid CORS errors.
- Caddy routes `/claude` to auth-gateway via the config pushed on startup. If the `/claude` route is missing after a reboot, auth-gateway retries the Caddy reload up to 15 times (3-second intervals) while Caddy initialises.
- LiveAvatar sessions time out after ~5 minutes of inactivity. The `keepAlive()` ping every 30 seconds prevents this.
- Nova uses FULL mode for LiveAvatar (not LITE). LITE mode does not permit `repeat(text)` for text-to-speech — only FULL mode supports it.
- The MCP tool name sent to Claude is formatted as `{serverName}__{toolName}` (dashes replaced with underscores) to stay within Anthropic's tool name constraints. The routing map translates back to the original server/tool names before calling `mcpClient.callTool`.
