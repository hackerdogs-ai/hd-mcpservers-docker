import React, { useState, useRef, useEffect, useCallback } from 'react';
import { getClaudeKey, getHeygenKey, getHeygenAvatarId } from '../lib/api.js';
import { mcpClient } from '../lib/mcp.js';
import { runChatTurn } from '../lib/claude.js';
import HeyGenAvatar from './HeyGenAvatar.jsx';

const AGENT_NAME = 'Nova';

const SYSTEM_PROMPT = `You are Nova, an expert cybersecurity analyst AI assistant embedded in the Hackerdogs MCP Security Farm — a platform with hundreds of professional security and intelligence tools exposed as MCP servers.

Your personality:
- Friendly, confident, and technically precise
- You ALWAYS explain your plan in natural language before running any tools: "I'll use X along with Y because..."
- Mention the specific MCP server names you plan to use upfront
- After tools finish, translate raw output into plain-English findings — don't dump raw data
- If chaining multiple tools, describe the strategy first (e.g. "I'll start with subfinder to enumerate subdomains, then httpx to find live hosts, and finally nuclei to check for vulnerabilities")
- Be honest about limitations (missing API keys, tool errors, network timeouts)
- Suggest logical next steps after summarising findings
- Keep responses focused and use bullet points for lists of findings

You have access to the tools exposed by the currently running MCP servers. Choose the most appropriate ones for the user's request.`;

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatToolResult(result) {
  if (!result) return '';
  if (typeof result === 'string') return result;
  if (result.content && Array.isArray(result.content)) {
    return result.content.map((c) => (c.type === 'text' ? c.text : JSON.stringify(c, null, 2))).join('\n');
  }
  return JSON.stringify(result, null, 2);
}

// ── Tool card ─────────────────────────────────────────────────────────────────

function ToolCard({ call }) {
  const [open, setOpen] = useState(false);
  const isError = !!call.error;
  const isDone = call.result !== undefined || isError;
  const color = isError ? '#f85149' : isDone ? '#3fb950' : '#d29922';

  return (
    <div className="rounded border my-1.5 text-xs" style={{ borderColor: color + '44', background: '#0a0f14' }}>
      <button onClick={() => setOpen((o) => !o)} className="w-full flex items-center gap-2 px-3 py-2 text-left">
        <span style={{ color, fontSize: 10 }}>{isError ? '✗' : isDone ? '✓' : '↻'}</span>
        {!isDone && <span className="spinner" style={{ width: 9, height: 9 }} />}
        <span className="font-mono px-1.5 py-0.5 rounded" style={{ background: '#161b22', color: '#8b949e', fontSize: 10 }}>
          {call.serverName}
        </span>
        <span style={{ color: '#c9d1d9' }}>{call.toolName}</span>
        <span className="ml-auto" style={{ color: '#484f58' }}>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="border-t px-3 pb-3 pt-2 space-y-2" style={{ borderColor: '#21262d' }}>
          {call.args && Object.keys(call.args).length > 0 && (
            <div>
              <div className="mb-1 font-medium" style={{ color: '#8b949e' }}>Arguments</div>
              <pre className="overflow-auto rounded p-2" style={{ background: '#161b22', color: '#58a6ff', maxHeight: 80, fontSize: 11 }}>
                {JSON.stringify(call.args, null, 2)}
              </pre>
            </div>
          )}
          {isError && (
            <div className="rounded p-2" style={{ background: 'rgba(248,81,73,0.08)', color: '#f85149' }}>{call.error}</div>
          )}
          {call.result !== undefined && (
            <div>
              <div className="mb-1 font-medium" style={{ color: '#8b949e' }}>Result</div>
              <pre className="overflow-auto rounded p-2 whitespace-pre-wrap" style={{ background: '#161b22', color: '#e6edf3', maxHeight: 180, fontSize: 11 }}>
                {formatToolResult(call.result)}
              </pre>
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
            <div key={i} className="rounded-xl px-4 py-3 text-sm mb-2 whitespace-pre-wrap"
              style={{ background: '#161b22', color: '#e6edf3', border: '1px solid #30363d', lineHeight: 1.6 }}>
              {part.text}
            </div>
          );
        }
        if (part.type === 'tool') return <ToolCard key={i} call={part} />;
        return null;
      })}
      {isPending && parts.length === 0 && (
        <div className="rounded-xl px-4 py-3 flex items-center gap-1.5"
          style={{ background: '#161b22', border: '1px solid #30363d', width: 'fit-content' }}>
          {[0, 1, 2].map((i) => (
            <span key={i} className="rounded-full inline-block"
              style={{ width: 7, height: 7, background: '#3fb950', animation: `nova-bubble-pulse 1.2s ease-in-out ${i * 0.2}s infinite` }} />
          ))}
        </div>
      )}
    </div>
  );
}

function UserMsg({ text }) {
  return (
    <div className="flex justify-end mb-4">
      <div className="max-w-md px-4 py-2.5 rounded-xl text-sm" style={{ background: '#1f6feb', color: '#fff', lineHeight: 1.5 }}>
        {text}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function AgentChat({ servers }) {
  const runningServers = Array.isArray(servers) ? servers.filter((s) => s.health_ok) : [];

  const welcome = `Hi! I'm Nova, your AI security analyst.\n\nI have access to ${runningServers.length} running security tools right now. Tell me what you'd like to investigate — a domain, IP address, vulnerability scan, or anything else — and I'll pick the right tools and walk you through the findings.\n\nWhat would you like me to look into?`;

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

  // Update welcome tool count when servers change
  useEffect(() => {
    const txt = `Hi! I'm Nova, your AI security analyst.\n\nI have access to ${runningServers.length} running security tools right now. Tell me what you'd like to investigate — a domain, IP address, vulnerability scan, or anything else — and I'll pick the right tools and walk you through the findings.\n\nWhat would you like me to look into?`;
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

    // Load tools
    setStatusText(`Connecting to ${runningServers.length} servers...`);
    const mcpTools = [];
    await Promise.allSettled(
      runningServers.map(async (srv) => {
        try {
          const tools = await mcpClient.listTools(srv.name);
          tools.forEach((tool) => mcpTools.push({ serverName: srv.name, tool }));
        } catch { /* skip unreachable */ }
      })
    );

    if (mcpTools.length === 0) {
      updatePending(() => [{ type: 'text', text: "I couldn't connect to any running servers. Please make sure at least one server is running and healthy, then try again." }]);
      setBusy(false);
      setNovaState('idle');
      setStatusText('');
      pendingIdRef.current = null;
      return;
    }

    setStatusText(`Thinking with ${mcpTools.length} tools...`);

    const toolIndexMap = {};

    try {
      const { messages: newHistory } = await runChatTurn(
        claudeHistory,
        text,
        mcpTools,
        (event) => {
          if (event.type === 'claude_response') {
            const textBlocks = (event.data.content || [])
              .filter((b) => b.type === 'text')
              .map((b) => b.text)
              .join('\n')
              .trim();
            if (textBlocks) {
              setNovaState('talking');
              updatePending((parts) => [...parts, { type: 'text', text: textBlocks }]);
              avatarRef.current?.speak(textBlocks);
              setTimeout(() => setNovaState('thinking'), 800);
            }
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
        SYSTEM_PROMPT
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
    const txt = `Conversation cleared. I have access to ${runningServers.length} running tools. What would you like me to investigate?`;
    setDisplayMsgs([{ id: Date.now(), type: 'agent', parts: [{ type: 'text', text: txt }] }]);
  }

  const statusLabel = novaState === 'thinking' ? (statusText || 'Thinking...') : novaState === 'talking' ? 'Responding...' : `${runningServers.length} tools available`;
  const statusColor = novaState === 'idle' ? '#3fb950' : '#d29922';

  return (
    <>
      <style>{`
        @keyframes nova-bubble-pulse {
          0%, 80%, 100% { opacity: 0.3; transform: scale(0.75); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>

      <div className="flex h-full" style={{ background: '#0d1117' }}>

        {/* ── Left panel: Nova avatar ── */}
        <div
          className="flex flex-col items-center pt-8 pb-6 px-4 flex-shrink-0"
          style={{ width: 240, borderRight: '1px solid #21262d', background: '#0d1117' }}
        >
          <HeyGenAvatar ref={avatarRef} apiKey={getHeygenKey()} avatarId={getHeygenAvatarId()} width={208} />

          <div className="mt-5 text-center">
            <div className="text-lg font-bold" style={{ color: '#e6edf3' }}>{AGENT_NAME}</div>
            <div className="text-xs mt-1" style={{ color: '#8b949e' }}>Security Analyst AI</div>
          </div>

          {/* Status badge */}
          <div
            className="mt-4 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
            style={{ background: '#161b22', border: `1px solid ${statusColor}44` }}
          >
            <span
              className="rounded-full flex-shrink-0"
              style={{ width: 7, height: 7, background: statusColor,
                boxShadow: novaState !== 'idle' ? `0 0 6px ${statusColor}` : 'none' }}
            />
            <span style={{ color: statusColor }}>
              {novaState === 'idle' ? 'Ready' : novaState === 'thinking' ? 'Thinking' : 'Responding'}
            </span>
          </div>

          {/* Running server count */}
          <div className="mt-6 w-full rounded-lg px-3 py-3 text-center"
            style={{ background: '#161b22', border: '1px solid #21262d' }}>
            <div className="text-2xl font-bold" style={{ color: '#3fb950' }}>{runningServers.length}</div>
            <div className="text-xs mt-0.5" style={{ color: '#8b949e' }}>tools available</div>
          </div>

          {runningServers.length > 0 && (
            <div className="mt-3 w-full space-y-1 max-h-48 overflow-y-auto">
              {runningServers.slice(0, 8).map((s) => (
                <div key={s.name} className="flex items-center gap-1.5 px-2 py-0.5 rounded text-xs"
                  style={{ color: '#8b949e' }}>
                  <span className="rounded-full flex-shrink-0" style={{ width: 5, height: 5, background: '#3fb950' }} />
                  <span className="truncate">{s.name.replace(/-mcp$/, '')}</span>
                </div>
              ))}
              {runningServers.length > 8 && (
                <div className="text-xs text-center mt-1" style={{ color: '#484f58' }}>
                  +{runningServers.length - 8} more
                </div>
              )}
            </div>
          )}

          <div className="mt-auto pt-4 w-full">
            <button onClick={handleClear} disabled={busy}
              className="w-full py-1.5 rounded text-xs transition-colors"
              style={{ border: '1px solid #30363d', color: '#8b949e', background: 'transparent' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#e6edf3')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#8b949e')}
            >
              ↺ New conversation
            </button>
          </div>
        </div>

        {/* ── Right panel: chat ── */}
        <div className="flex flex-col flex-1 min-w-0">

          {/* Chat header */}
          <div className="flex items-center px-5 py-3 border-b flex-shrink-0"
            style={{ borderColor: '#21262d', background: '#0d1117' }}>
            <div className="text-sm" style={{ color: '#8b949e' }}>
              <span style={{ color: statusColor }}>{statusLabel}</span>
              {statusText && novaState === 'thinking' && (
                <span className="ml-2 text-xs" style={{ color: '#484f58' }}>· {statusText}</span>
              )}
            </div>
          </div>

          {/* No Claude key warning */}
          {!getClaudeKey() && (
            <div className="mx-5 mt-4 px-4 py-2.5 rounded-lg text-sm flex-shrink-0"
              style={{ background: 'rgba(210,153,34,0.08)', border: '1px solid rgba(210,153,34,0.3)', color: '#d29922' }}>
              Claude API key not set — open ⚙️ Settings and add your <code style={{ background: '#0d1117', padding: '1px 4px', borderRadius: 3 }}>sk-ant-...</code> key to activate Nova.
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
          <div className="px-5 pb-5 pt-3 flex-shrink-0 border-t" style={{ borderColor: '#21262d' }}>
            <div className="flex gap-3">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={busy}
                rows={2}
                placeholder="Ask Nova to scan a target, investigate a domain, check for vulnerabilities..."
                className="flex-1 px-4 py-3 rounded-xl text-sm resize-none border transition-colors"
                style={{
                  background: '#161b22', borderColor: '#30363d', color: '#e6edf3',
                  outline: 'none', opacity: busy ? 0.6 : 1, lineHeight: 1.5,
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
                onBlur={(e) => (e.target.style.borderColor = '#30363d')}
              />
              <button onClick={handleSend} disabled={busy || !input.trim()}
                className="px-5 rounded-xl text-sm font-semibold transition-all flex-shrink-0"
                style={{
                  background: busy || !input.trim() ? '#161b22' : 'linear-gradient(135deg, #3fb950, #238636)',
                  color: busy || !input.trim() ? '#484f58' : '#fff',
                  cursor: busy || !input.trim() ? 'not-allowed' : 'pointer',
                  border: '1px solid',
                  borderColor: busy || !input.trim() ? '#30363d' : '#3fb950',
                  boxShadow: !busy && input.trim() ? '0 0 12px rgba(63,185,80,0.3)' : 'none',
                }}
              >
                {busy ? <span className="spinner" style={{ width: 16, height: 16 }} /> : '▶ Send'}
              </button>
            </div>
            <div className="text-xs mt-2" style={{ color: '#484f58' }}>
              Enter to send · Shift+Enter for new line · Nova only uses currently running servers
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
