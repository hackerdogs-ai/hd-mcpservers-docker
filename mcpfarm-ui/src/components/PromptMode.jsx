import React, { useState, useRef, useEffect, useMemo } from 'react';
import { runAgenticLoop } from '../lib/claude.js';
import { mcpClient } from '../lib/mcp.js';
import { getClaudeKey } from '../lib/api.js';

// ─── Collapsible card ─────────────────────────────────────────────────────────

function CollapsibleCard({ header, children, defaultOpen = false, borderColor = '#30363d', headerColor = '#8b949e' }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-lg border overflow-hidden" style={{ borderColor }}>
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer select-none"
        style={{ background: '#161b22' }}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="text-xs" style={{ color: '#8b949e' }}>{open ? '▼' : '▶'}</span>
        <span className="text-xs font-mono flex-1" style={{ color: headerColor }}>
          {header}
        </span>
      </div>
      {open && (
        <div style={{ background: '#0d1117' }}>
          {children}
        </div>
      )}
    </div>
  );
}

// ─── Message bubble ───────────────────────────────────────────────────────────

function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end mb-3">
        <div
          className="max-w-lg px-3 py-2 rounded-lg text-sm"
          style={{ background: '#1f6feb', color: '#e6edf3' }}
        >
          {msg.text}
        </div>
      </div>
    );
  }

  if (msg.role === 'assistant') {
    return (
      <div className="flex justify-start mb-3">
        <div
          className="max-w-2xl px-3 py-2 rounded-lg text-sm"
          style={{ background: '#161b22', color: '#e6edf3', border: '1px solid #30363d' }}
        >
          <span className="text-xs font-semibold block mb-1" style={{ color: '#8b949e' }}>Claude</span>
          <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
        </div>
      </div>
    );
  }

  if (msg.role === 'tool_call') {
    const { serverName, toolName, args } = msg.data;
    return (
      <div className="mb-2 ml-2">
        <CollapsibleCard
          header={`🔧 ${serverName} → ${toolName}(${JSON.stringify(args || {}).slice(0, 80)})`}
          borderColor="#388bfd"
          headerColor="#58a6ff"
          defaultOpen={false}
        >
          <pre className="result-pre p-3 text-xs" style={{ color: '#58a6ff' }}>
            {JSON.stringify(args, null, 2)}
          </pre>
        </CollapsibleCard>
      </div>
    );
  }

  if (msg.role === 'tool_result') {
    const { serverName, toolName, result, error } = msg.data;

    function formatResult(r) {
      if (!r) return '';
      if (typeof r === 'string') return r;
      if (r.content && Array.isArray(r.content)) {
        return r.content.map((c) => (c.type === 'text' ? c.text : JSON.stringify(c, null, 2))).join('\n');
      }
      return JSON.stringify(r, null, 2);
    }

    return (
      <div className="mb-2 ml-2">
        <CollapsibleCard
          header={error ? `✗ ${toolName} error` : `✓ ${toolName} result`}
          borderColor={error ? '#f85149' : '#238636'}
          headerColor={error ? '#f85149' : '#3fb950'}
          defaultOpen={false}
        >
          <pre
            className="result-pre p-3 text-xs overflow-auto"
            style={{ color: error ? '#f85149' : '#e6edf3', maxHeight: 300 }}
          >
            {error ? String(error) : formatResult(result)}
          </pre>
        </CollapsibleCard>
      </div>
    );
  }

  if (msg.role === 'status') {
    return (
      <div className="flex items-center gap-2 mb-2 ml-2">
        <span className="spinner" style={{ width: 12, height: 12 }} />
        <span className="text-xs" style={{ color: '#8b949e' }}>{msg.text}</span>
      </div>
    );
  }

  if (msg.role === 'error') {
    return (
      <div
        className="mb-2 px-3 py-2 rounded text-xs"
        style={{ background: 'rgba(248,81,73,0.1)', color: '#f85149', border: '1px solid rgba(248,81,73,0.3)' }}
      >
        ✗ {msg.text}
      </div>
    );
  }

  if (msg.role === 'warning') {
    return (
      <div className="mb-2 text-xs" style={{ color: '#d29922' }}>
        ⚠ {msg.text}
      </div>
    );
  }

  return null;
}

// ─── PromptMode ───────────────────────────────────────────────────────────────

export default function PromptMode({ servers }) {
  const [claudeKey, setClaudeKeyState] = useState(getClaudeKey);
  const [selectedServers, setSelectedServers] = useState(new Set());
  const [useAllRunning, setUseAllRunning] = useState(true);
  const [serverSearch, setServerSearch] = useState('');
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState([]);
  const [running, setRunning] = useState(false);
  const chatBottomRef = useRef(null);

  const runningServers = useMemo(
    () => (Array.isArray(servers) ? servers.filter((s) => (s.status || '').toLowerCase() === 'running') : []),
    [servers]
  );

  const filteredRunning = useMemo(() => {
    if (!serverSearch) return runningServers;
    return runningServers.filter((s) =>
      (s.name || s.id || '').toLowerCase().includes(serverSearch.toLowerCase())
    );
  }, [runningServers, serverSearch]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function addMessage(msg) {
    setMessages((prev) => [...prev, { ...msg, id: Date.now() + Math.random() }]);
  }

  function toggleServer(name) {
    setSelectedServers((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  async function handleSend() {
    if (!prompt.trim() || running) return;

    const activeServers = useAllRunning
      ? runningServers.map((s) => s.name || s.id)
      : Array.from(selectedServers);

    if (activeServers.length === 0) {
      addMessage({ role: 'error', text: 'No running servers selected. Start some servers first.' });
      return;
    }

    const key = claudeKey || getClaudeKey();
    if (!key) {
      addMessage({ role: 'error', text: 'Claude API key is required. Add it in Settings or the field above.' });
      return;
    }

    // Add user message
    addMessage({ role: 'user', text: prompt });
    const userPrompt = prompt;
    setPrompt('');
    setRunning(true);

    // Load tools from active servers
    addMessage({ role: 'status', text: `Loading tools from ${activeServers.length} servers...` });

    const mcpTools = [];
    const toolErrors = [];

    await Promise.allSettled(
      activeServers.map(async (serverName) => {
        try {
          const tools = await mcpClient.listTools(serverName);
          tools.forEach((tool) => mcpTools.push({ serverName, tool }));
        } catch (err) {
          toolErrors.push(`${serverName}: ${err.message}`);
        }
      })
    );

    if (mcpTools.length === 0) {
      addMessage({ role: 'error', text: `Could not load any tools. Errors:\n${toolErrors.join('\n')}` });
      setRunning(false);
      return;
    }

    addMessage({
      role: 'status',
      text: `Loaded ${mcpTools.length} tools from ${activeServers.length} servers. Running agentic loop...`,
    });

    // Run agentic loop
    try {
      await runAgenticLoop(
        userPrompt,
        mcpTools,
        (event) => {
          if (event.type === 'status') {
            addMessage({ role: 'status', text: event.data });
          } else if (event.type === 'claude_response') {
            const resp = event.data;
            // Extract text blocks from response
            const textBlocks = (resp.content || [])
              .filter((b) => b.type === 'text')
              .map((b) => b.text)
              .join('\n');
            if (textBlocks) {
              addMessage({ role: 'assistant', text: textBlocks });
            }
          } else if (event.type === 'tool_call') {
            addMessage({ role: 'tool_call', data: event.data });
          } else if (event.type === 'tool_result') {
            addMessage({ role: 'tool_result', data: event.data });
          } else if (event.type === 'tool_error') {
            addMessage({ role: 'tool_result', data: { ...event.data, error: event.data.error } });
          } else if (event.type === 'error') {
            addMessage({ role: 'error', text: event.data });
          } else if (event.type === 'warning') {
            addMessage({ role: 'warning', text: event.data });
          }
        },
        key
      );
    } catch (err) {
      addMessage({ role: 'error', text: err.message });
    } finally {
      setRunning(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSend();
    }
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left sidebar: server selection */}
      <div
        className="w-56 flex-shrink-0 flex flex-col border-r overflow-hidden"
        style={{ borderColor: '#30363d' }}
      >
        <div className="px-3 py-2 border-b" style={{ borderColor: '#30363d' }}>
          <span className="text-xs font-semibold uppercase tracking-wider block mb-2" style={{ color: '#8b949e' }}>
            Servers
          </span>

          <label className="flex items-center gap-2 mb-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useAllRunning}
              onChange={(e) => setUseAllRunning(e.target.checked)}
              style={{ accentColor: '#3fb950' }}
            />
            <span className="text-xs" style={{ color: '#c9d1d9' }}>
              Auto (all {runningServers.length} running)
            </span>
          </label>

          {!useAllRunning && (
            <input
              type="text"
              value={serverSearch}
              onChange={(e) => setServerSearch(e.target.value)}
              placeholder="Search..."
              className="w-full px-2 py-1 rounded text-xs border"
              style={{ background: '#0d1117', borderColor: '#30363d', color: '#e6edf3', outline: 'none' }}
              onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
              onBlur={(e) => (e.target.style.borderColor = '#30363d')}
            />
          )}
        </div>

        {!useAllRunning && (
          <div className="flex-1 overflow-y-auto">
            {filteredRunning.map((s) => {
              const name = s.name || s.id || '';
              return (
                <label
                  key={name}
                  className="flex items-center gap-2 px-3 py-1.5 cursor-pointer border-b"
                  style={{ borderColor: '#21262d' }}
                >
                  <input
                    type="checkbox"
                    checked={selectedServers.has(name)}
                    onChange={() => toggleServer(name)}
                    style={{ accentColor: '#3fb950' }}
                  />
                  <span
                    className="rounded-full flex-shrink-0"
                    style={{ width: 6, height: 6, background: '#3fb950' }}
                  />
                  <span className="text-xs truncate" style={{ color: '#c9d1d9' }}>
                    {name}
                  </span>
                </label>
              );
            })}
            {filteredRunning.length === 0 && (
              <div className="p-3 text-xs text-center" style={{ color: '#8b949e' }}>
                No running servers
              </div>
            )}
          </div>
        )}

        {useAllRunning && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center px-3">
              <div className="text-2xl mb-2">🤖</div>
              <p className="text-xs" style={{ color: '#8b949e' }}>
                Claude will automatically choose from {runningServers.length} running servers
              </p>
            </div>
          </div>
        )}

        {/* Claude key override */}
        <div className="px-3 py-2 border-t" style={{ borderColor: '#30363d' }}>
          <label className="block text-xs mb-1" style={{ color: '#8b949e' }}>
            Claude API Key
          </label>
          <input
            type="password"
            value={claudeKey}
            onChange={(e) => setClaudeKeyState(e.target.value)}
            placeholder="sk-ant-..."
            className="w-full px-2 py-1 rounded text-xs border"
            style={{ background: '#0d1117', borderColor: '#30363d', color: '#e6edf3', outline: 'none' }}
            onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
            onBlur={(e) => (e.target.style.borderColor = '#30363d')}
          />
        </div>
      </div>

      {/* Right: chat panel */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Chat messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center" style={{ color: '#8b949e' }}>
                <div className="text-4xl mb-3">💬</div>
                <p className="text-sm">Ask Claude to use any MCP tool.</p>
                <p className="text-xs mt-1" style={{ color: '#484f58' }}>
                  Example: "Scan hackerdogs.ai with nmap and check for open ports"
                </p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}

          <div ref={chatBottomRef} />
        </div>

        {/* Input area */}
        <div
          className="border-t p-3"
          style={{ borderColor: '#30363d', background: '#161b22' }}
        >
          <div className="flex gap-2">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Claude to use MCP tools... (Ctrl+Enter to send)"
              disabled={running}
              rows={3}
              className="flex-1 px-3 py-2 rounded text-sm border resize-none"
              style={{
                background: '#0d1117',
                borderColor: '#30363d',
                color: '#e6edf3',
                outline: 'none',
                opacity: running ? 0.6 : 1,
              }}
              onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
              onBlur={(e) => (e.target.style.borderColor = '#30363d')}
            />
            <button
              onClick={handleSend}
              disabled={running || !prompt.trim()}
              className="px-4 py-2 rounded text-sm font-medium self-end transition-all"
              style={{
                background: running || !prompt.trim() ? '#21262d' : '#3fb950',
                color: running || !prompt.trim() ? '#484f58' : '#0d1117',
                minWidth: 80,
              }}
            >
              {running ? (
                <span className="flex items-center gap-1 justify-center">
                  <span className="spinner" style={{ width: 14, height: 14 }} />
                </span>
              ) : (
                'Send'
              )}
            </button>
          </div>
          <p className="text-xs mt-1" style={{ color: '#484f58' }}>
            Ctrl+Enter to send • Claude will choose and execute MCP tools automatically
          </p>
        </div>
      </div>
    </div>
  );
}
