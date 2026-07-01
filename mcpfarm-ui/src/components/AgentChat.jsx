import React, { useState, useRef, useEffect, useCallback } from 'react';
import { getClaudeKey, getHeygenKey, getHeygenAvatarId } from '../lib/api.js';
import { mcpClient } from '../lib/mcp.js';
import { runChatTurn } from '../lib/claude.js';
import { isServerRunning } from '../lib/categories.js';
import HeyGenAvatar from './HeyGenAvatar.jsx';
import ToolResultContent from './ToolResultContent.jsx';

const AGENT_NAME = 'Nova';

const BASE_SYSTEM_PROMPT = `You are Nova, an expert cybersecurity analyst AI embedded in the Hackerdogs MCP Security Farm — a platform with hundreds of professional security and intelligence tools exposed as MCP servers.

## TOOL USE RULES — follow these exactly

1. For ANY technical request (scanning, recon, OSINT, vulnerability assessment, investigation), you MUST call at least one tool. Never respond with text alone for a technical task — act, don't describe.
2. Say ONE short sentence ("I'll use X to...") then immediately call the tool. Do not write a long plan first.
3. After tool results arrive, translate findings to plain English. Bullet points for lists. No raw JSON dumps.
4. If you need to chain tools, call the first one now and explain chaining AFTER it returns.
5. If a user asks "what can you do about X?" — demonstrate by calling a relevant tool immediately, then describe what else you can do.

## WHEN RELEVANT TOOLS ARE NOT RUNNING

If the user's request needs servers that are NOT currently running, you MUST:
- Name the specific servers they need to start (e.g. "nmap-mcp for port scanning, subfinder-mcp for subdomain enum")
- Tell them to go to the Servers tab, find those servers, and click Start
- Do NOT just say "I don't have tools" — always name the specific servers for the task
- If some relevant tools ARE running, use them now and note what additional servers would add

## PERSONALITY
- Confident and direct. You are a senior security analyst, not a chatbot.
- Never say "I would" or "I could" — just do it.
- Be honest about errors (missing API keys, network timeouts, permissions)
- Suggest logical next steps after findings

`;

function buildSystemPrompt(runningServers, allServers) {
  const notRunningCount = (allServers || []).length - runningServers.length;

  let catalog = '\n\n## MCP SERVERS IN THIS FARM\n';

  if (runningServers.length > 0) {
    catalog += '\n### Currently running (you can call these now):\n';
    catalog += runningServers.map((s) => `- ${s.name}`).join('\n');
  } else {
    catalog += '\n### Currently running: NONE — all tool calls will fail until servers are started.\n';
  }

  if (notRunningCount > 0) {
    catalog += `\n\n${notRunningCount} additional servers are available but not running. Tell the user which ones to start by name based on their task.`;
  }

  return BASE_SYSTEM_PROMPT + catalog;
}

// ── Tool card ─────────────────────────────────────────────────────────────────

function ToolCard({ call }) {
  const [open, setOpen] = useState(false);
  const isError = !!call.error;
  const isDone = call.result !== undefined || isError;
  const cardClass = isError
    ? 'hd-tool-card hd-tool-card--err'
    : isDone
    ? 'hd-tool-card hd-tool-card--ok'
    : 'hd-tool-card hd-tool-card--pending';

  return (
    <div className={cardClass}>
      <button type="button" onClick={() => setOpen((o) => !o)} className="hd-tool-card__head">
        <span className={isError ? 'hd-text-err' : isDone ? 'hd-text-ok' : ''} style={{ fontSize: 10 }}>
          {isError ? '✗' : isDone ? '✓' : '↻'}
        </span>
        {!isDone && <span className="spinner" style={{ width: 9, height: 9 }} />}
        <span className="hd-tool-card__badge">{call.serverName}</span>
        <span>{call.toolName}</span>
        <span className="ml-auto hd-text-dim">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="hd-tool-card__body space-y-2">
          {call.args && Object.keys(call.args).length > 0 && (
            <div>
              <div className="hd-tool-card__label">Arguments</div>
              <pre className="hd-code hd-code--json max-h-20">{JSON.stringify(call.args, null, 2)}</pre>
            </div>
          )}
          {isError && <div className="hd-tool-card__error">{call.error}</div>}
          {call.result !== undefined && (
            <div>
              <div className="hd-tool-card__label">Result</div>
              <ToolResultContent
                result={call.result}
                className="hd-code max-h-[180px] whitespace-pre-wrap"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Message bubbles ───────────────────────────────────────────────────────────

function AgentMsg({ parts, isPending }) {
  return (
    <div className="mb-4">
      {parts.map((part, i) => {
        if (part.type === 'text' && part.text) {
          return (
            <div key={i} className="hd-chat-bubble-agent text-sm mb-2 whitespace-pre-wrap">
              {part.text}
            </div>
          );
        }
        if (part.type === 'tool') return <ToolCard key={i} call={part} />;
        return null;
      })}
      {isPending && parts.length === 0 && (
        <div className="hd-chat-bubble-agent inline-flex items-center gap-1.5 w-fit">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="rounded-full inline-block"
              style={{
                width: 7,
                height: 7,
                background: 'var(--status-live)',
                animation: `nova-bubble-pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function UserMsg({ text }) {
  return (
    <div className="flex justify-end mb-4">
      <div className="max-w-md hd-chat-bubble-user text-sm">{text}</div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function AgentChat({ servers }) {
  const allServers = Array.isArray(servers) ? servers : [];
  const runningServers = allServers.filter((s) => isServerRunning(s));

  const welcome = runningServers.length > 0
    ? `Hi! I'm Nova, your AI security analyst.\n\nI have ${runningServers.length} security tools running right now. Give me a target — domain, IP, URL, or a question — and I'll get to work.\n\nWhat would you like me to investigate?`
    : `Hi! I'm Nova, your AI security analyst.\n\nNo servers are running yet. Head to the Servers tab to start some tools, then come back and I'll put them to work.\n\nOr describe what you want to do and I'll tell you exactly which servers to start.`;

  const [displayMsgs, setDisplayMsgs] = useState([
    { id: 'welcome', type: 'agent', parts: [{ type: 'text', text: welcome }] },
  ]);
  const [claudeHistory, setClaudeHistory] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [novaState, setNovaState] = useState('idle'); // 'idle' | 'thinking' | 'talking'
  const [statusText, setStatusText] = useState('');

  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const pendingIdRef = useRef(null);
  const avatarRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayMsgs, busy]);

  // Update welcome message when server state changes
  useEffect(() => {
    const txt = runningServers.length > 0
      ? `Hi! I'm Nova, your AI security analyst.\n\nI have ${runningServers.length} security tools running right now. Give me a target — domain, IP, URL, or a question — and I'll get to work.\n\nWhat would you like me to investigate?`
      : `Hi! I'm Nova, your AI security analyst.\n\nNo servers are running yet. Head to the Servers tab to start some tools, then come back and I'll put them to work.\n\nOr describe what you want to do and I'll tell you exactly which servers to start.`;
    setDisplayMsgs((prev) =>
      prev.map((m) => m.id === 'welcome' ? { ...m, parts: [{ type: 'text', text: txt }] } : m)
    );
  }, [runningServers.length]);

  const updatePending = useCallback((updater) => {
    const id = pendingIdRef.current;
    if (!id) return;
    setDisplayMsgs((prev) => prev.map((m) => (m.id === id ? { ...m, parts: updater(m.parts) } : m)));
  }, []);

  async function handleSend() {
    const text = input.trim();
    if (!text || busy) return;

    const key = getClaudeKey();
    if (!key) {
      setDisplayMsgs((prev) => [...prev,
        { id: Date.now(), type: 'agent', parts: [{ type: 'text', text: "I need a Claude API key to think. Open ⚙️ Settings and add your sk-ant-... key, then try again." }] },
      ]);
      return;
    }

    setInput('');
    setBusy(true);
    setNovaState('thinking');
    avatarRef.current?.interrupt();

    setDisplayMsgs((prev) => [...prev, { id: Date.now(), type: 'user', text }]);

    const agentId = Date.now() + 1;
    pendingIdRef.current = agentId;
    setDisplayMsgs((prev) => [...prev, { id: agentId, type: 'agent', parts: [] }]);

    // Load tools from running servers
    setStatusText(runningServers.length > 0 ? `Connecting to ${runningServers.length} servers...` : 'Asking Nova...');
    const mcpTools = [];
    if (runningServers.length > 0) {
      await Promise.allSettled(
        runningServers.map(async (srv) => {
          try {
            const tools = await mcpClient.listTools(srv.name);
            tools.forEach((tool) => mcpTools.push({ serverName: srv.name, tool }));
          } catch { /* skip unreachable */ }
        })
      );
    }

    setStatusText(mcpTools.length > 0 ? `Thinking with ${mcpTools.length} tools...` : 'Thinking...');

    const systemPrompt = buildSystemPrompt(runningServers, allServers);
    const toolIndexMap = {};

    try {
      // Keep only last 6 messages (3 turns) to avoid token limit
      const trimmedHistory = claudeHistory.slice(-6);

      const { messages: newHistory } = await runChatTurn(
        trimmedHistory,
        text,
        mcpTools,
        (event) => {
          if (event.type === 'claude_response') {
            const raw = (event.data.content || [])
              .filter((b) => b.type === 'text')
              .map((b) => b.text)
              .join('\n')
              .trim();
            if (raw) {
              const displayText = raw.replace(/<speak>[\s\S]*?<\/speak>\n?/i, '').trim();
              if (displayText) updatePending((parts) => [...parts, { type: 'text', text: displayText }]);
              // Speak the planning sentence when Nova is about to call tools
              if (event.data.stop_reason === 'tool_use') {
                const sentence = displayText.split(/(?<=[.!?])\s/)[0]?.trim();
                if (sentence) { setNovaState('talking'); avatarRef.current?.speak(sentence); }
              }
            }
          } else if (event.type === 'done') {
            setNovaState('talking');
            avatarRef.current?.speak('Here are the results.');
            setTimeout(() => setNovaState('idle'), 3000);
          } else if (event.type === 'tool_call') {
            const { id, serverName, toolName, args } = event.data;
            setNovaState('thinking');
            setStatusText(`Running ${serverName} → ${toolName}...`);
            updatePending((parts) => {
              toolIndexMap[id] = parts.length;
              return [...parts, { type: 'tool', id, serverName, toolName, args }];
            });
          } else if (event.type === 'tool_result') {
            const { id, result } = event.data;
            updatePending((parts) => parts.map((p, i) => (i === toolIndexMap[id] ? { ...p, result } : p)));
          } else if (event.type === 'tool_error') {
            const { id, error } = event.data;
            updatePending((parts) => parts.map((p, i) => (i === toolIndexMap[id] ? { ...p, error } : p)));
          } else if (event.type === 'error') {
            updatePending((parts) => [...parts, { type: 'text', text: `Something went wrong: ${event.data}` }]);
          }
        },
        key,
        systemPrompt
      );
      setClaudeHistory(newHistory);
    } catch (err) {
      updatePending((parts) => [...parts, { type: 'text', text: `Error: ${err.message}` }]);
    } finally {
      setBusy(false);
      setNovaState('idle');
      setStatusText('');
      pendingIdRef.current = null;
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }

  function handleClear() {
    setClaudeHistory([]);
    const txt = runningServers.length > 0
      ? `Conversation cleared. ${runningServers.length} tools ready. What would you like me to investigate?`
      : `Conversation cleared. No servers running — go to the Servers tab to start some, or tell me your goal and I'll suggest which ones to start.`;
    setDisplayMsgs([{ id: Date.now(), type: 'agent', parts: [{ type: 'text', text: txt }] }]);
  }

  const statusLabel = novaState === 'thinking' ? (statusText || 'Thinking...') : novaState === 'talking' ? 'Responding...' : `${runningServers.length} tools available`;

  return (
    <>
      <style>{`
        @keyframes nova-bubble-pulse {
          0%, 80%, 100% { opacity: 0.3; transform: scale(0.75); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>

      <div className="flex h-full hd-chat-shell">
        <div className="flex flex-col items-center pt-8 pb-6 px-4 flex-shrink-0 hd-chat-sidebar" style={{ width: 240 }}>
          <HeyGenAvatar ref={avatarRef} apiKey={getHeygenKey()} avatarId={getHeygenAvatarId()} width={208} />

          <div className="mt-5 text-center">
            <div className="text-lg font-bold">{AGENT_NAME}</div>
            <div className="text-xs mt-1 hd-text-dim">Security Analyst AI</div>
          </div>

          <div className="mt-4 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs hd-panel">
            <span
              className="rounded-full flex-shrink-0"
              style={{
                width: 7,
                height: 7,
                background: novaState === 'idle' ? 'var(--status-live)' : 'var(--semantic-warning)',
              }}
            />
            <span className={novaState === 'idle' ? 'hd-text-ok' : ''}>
              {novaState === 'idle' ? 'Ready' : novaState === 'thinking' ? 'Thinking' : 'Responding'}
            </span>
          </div>

          <div className="mt-6 w-full hd-panel rounded-lg px-3 py-3 text-center">
            <div className="text-2xl font-bold hd-text-ok">{runningServers.length}</div>
            <div className="text-xs mt-0.5 hd-text-dim">tools available</div>
          </div>

          {runningServers.length > 0 && (
            <div className="mt-3 w-full space-y-1 max-h-48 overflow-y-auto">
              {runningServers.slice(0, 8).map((s) => (
                <div key={s.name} className="flex items-center gap-1.5 px-2 py-0.5 rounded text-xs hd-text-dim">
                  <span className="rounded-full flex-shrink-0 hd-text-ok" style={{ width: 5, height: 5, background: 'var(--status-live)' }} />
                  <span className="truncate">{s.name.replace(/-mcp$/, '')}</span>
                </div>
              ))}
              {runningServers.length > 8 && (
                <div className="text-xs text-center mt-1 hd-text-dim">{runningServers.length - 8} more</div>
              )}
            </div>
          )}

          <div className="mt-auto pt-4 w-full">
            <button type="button" onClick={handleClear} disabled={busy} className="hd-btn hd-btn--ghost w-full text-xs">
              ↺ New conversation
            </button>
          </div>
        </div>

        <div className="flex flex-col flex-1 min-w-0 hd-chat-shell">
          <div className="flex items-center px-5 py-3 border-b flex-shrink-0 hd-panel__head" style={{ borderBottom: '1px solid var(--border)' }}>
            <div className="text-sm hd-text-dim">
              <span className={novaState === 'idle' ? 'hd-text-ok' : ''}>{statusLabel}</span>
              {statusText && novaState === 'thinking' && (
                <span className="ml-2 text-xs hd-text-dim">· {statusText}</span>
              )}
            </div>
          </div>

          {!getClaudeKey() && (
            <div className="mx-5 mt-4 px-4 py-2.5 rounded-lg text-sm flex-shrink-0 hd-tool-card__error">
              Claude API key not set — open ⚙️ Settings and add your <code className="hd-code inline px-1">sk-ant-...</code> key to activate Nova.
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 pt-5 pb-2">
            {displayMsgs.map((msg) =>
              msg.type === 'user'
                ? <UserMsg key={msg.id} text={msg.text} />
                : <AgentMsg key={msg.id} parts={msg.parts} isPending={busy && msg.id === pendingIdRef.current && msg.parts.length === 0} />
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-5 pb-5 pt-3 flex-shrink-0 border-t" style={{ borderColor: 'var(--border)' }}>
            <div className="flex gap-3">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={busy}
                rows={2}
                placeholder="Ask Nova to scan a target, investigate a domain, check for vulnerabilities..."
                className="hd-textarea flex-1 rounded-xl text-sm resize-none"
                style={{ opacity: busy ? 0.6 : 1, lineHeight: 1.5, minHeight: '4.5rem' }}
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={busy || !input.trim()}
                className="hd-btn hd-btn--primary px-5 rounded-xl flex-shrink-0"
              >
                {busy ? <span className="spinner" style={{ width: 16, height: 16 }} /> : '▶ Send'}
              </button>
            </div>
            <div className="text-xs mt-2 hd-text-dim">
              Enter to send · Shift+Enter for new line · Nova only uses currently running servers
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
