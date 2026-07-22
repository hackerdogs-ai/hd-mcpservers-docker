import React, { useState, useRef, useEffect, useMemo } from 'react';
import { runAgenticLoop } from '../lib/claude.js';
import { mcpClient } from '../lib/mcp.js';
import { getClaudeKey } from '../lib/api.js';
import ToolResultContent from './ToolResultContent.jsx';
import Icon from './Icon.jsx';

// ─── Collapsible card ─────────────────────────────────────────────────────────

function CollapsibleCard({ header, children, defaultOpen = false, variant = 'default' }) {
  const [open, setOpen] = useState(defaultOpen);
  const headClass = variant === 'error'
    ? 'hd-collapsible__head hd-collapsible__head--err'
    : variant === 'ok'
    ? 'hd-collapsible__head hd-collapsible__head--ok'
    : 'hd-collapsible__head';
  return (
    <div className="hd-collapsible">
      <div className={headClass} onClick={() => setOpen((v) => !v)}>
        <span className="hd-result__toggle"><Icon name={open ? 'expand_more' : 'chevron_right'} size={16} /></span>
        <span className="font-mono flex-1">{header}</span>
      </div>
      {open && <div className="hd-collapsible__body">{children}</div>}
    </div>
  );
}

// ─── Message bubble ───────────────────────────────────────────────────────────

function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end mb-3">
        <div className="max-w-lg hd-chat-bubble-user text-sm">{msg.text}</div>
      </div>
    );
  }

  if (msg.role === 'assistant') {
    return (
      <div className="flex justify-start mb-3">
        <div className="max-w-2xl hd-chat-bubble-agent text-sm">
          <span className="text-xs font-semibold block mb-1 hd-text-dim">Claude</span>
          <div className="whitespace-pre-wrap">{msg.text}</div>
        </div>
      </div>
    );
  }

  if (msg.role === 'tool_call') {
    const { serverName, toolName, args } = msg.data;
    return (
      <div className="mb-2 ml-2">
        <CollapsibleCard
          header={`${serverName} → ${toolName}(${JSON.stringify(args || {}).slice(0, 80)})`}
          variant="ok"
          defaultOpen={false}
        >
          <pre className="result-pre hd-code hd-code--json p-3 text-xs">
            {JSON.stringify(args, null, 2)}
          </pre>
        </CollapsibleCard>
      </div>
    );
  }

  if (msg.role === 'tool_result') {
    const { toolName, result, error } = msg.data;

    return (
      <div className="mb-2 ml-2">
        <CollapsibleCard
          header={error ? `${toolName} error` : `${toolName} result`}
          variant={error ? 'error' : 'ok'}
          defaultOpen={false}
        >
          <ToolResultContent
            result={result}
            error={error}
            className={`result-pre p-3 text-xs overflow-auto max-h-[300px]${error ? ' hd-result__body--error' : ''}`}
          />
        </CollapsibleCard>
      </div>
    );
  }

  if (msg.role === 'status') {
    return (
      <div className="flex items-center gap-2 mb-2 ml-2">
        <span className="spinner" style={{ width: 12, height: 12 }} />
        <span className="text-xs hd-text-dim">{msg.text}</span>
      </div>
    );
  }

  if (msg.role === 'error') {
    return (
      <div
        className="mb-2 px-3 py-2 rounded text-xs"
        style={{ background: 'rgba(248,81,73,0.1)', color: '#f85149', border: '1px solid rgba(248,81,73,0.3)' }}
      >
        <Icon name="error" size={16} /> {msg.text}
      </div>
    );
  }

  if (msg.role === 'warning') {
    return (
      <div className="mb-2 text-xs" style={{ color: '#d29922' }}>
        <Icon name="warning" size={16} /> {msg.text}
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
      <div className="w-56 flex-shrink-0 flex flex-col hd-border-r hd-sidebar overflow-hidden">
        <div className="px-3 py-2 hd-border-b">
          <span className="text-xs font-semibold uppercase tracking-wider block mb-2 hd-text-dim">
            Servers
          </span>

          <label className="flex items-center gap-2 mb-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useAllRunning}
              onChange={(e) => setUseAllRunning(e.target.checked)}
            />
            <span className="text-xs hd-text-secondary">
              Auto (all {runningServers.length} running)
            </span>
          </label>

          {!useAllRunning && (
            <input
              type="text"
              value={serverSearch}
              onChange={(e) => setServerSearch(e.target.value)}
              placeholder="Search..."
              className="hd-input text-xs"
            />
          )}
        </div>

        {!useAllRunning && (
          <div className="flex-1 overflow-y-auto">
            {filteredRunning.map((s) => {
              const name = s.name || s.id || '';
              return (
                <label key={name} className="hd-list-item cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedServers.has(name)}
                    onChange={() => toggleServer(name)}
                  />
                  <span
                    className="rounded-full flex-shrink-0"
                    style={{ width: 6, height: 6, background: 'var(--semantic-success)' }}
                  />
                  <span className="text-xs truncate">{name}</span>
                </label>
              );
            })}
            {filteredRunning.length === 0 && (
              <div className="p-3 text-xs text-center hd-text-dim">No running servers</div>
            )}
          </div>
        )}

        {useAllRunning && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center px-3">
              <div className="mb-2"><Icon name="smart_toy" size={24} /></div>
              <p className="text-xs hd-text-dim">
                Claude will automatically choose from {runningServers.length} running servers
              </p>
            </div>
          </div>
        )}

        <div className="px-3 py-2 hd-border-t">
          <label className="hd-label">Claude API Key</label>
          <input
            type="password"
            value={claudeKey}
            onChange={(e) => setClaudeKeyState(e.target.value)}
            placeholder="sk-ant-..."
            className="hd-input text-xs"
          />
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center hd-empty-hint">
                <div className="mb-3"><Icon name="chat" size={32} /></div>
                <p className="text-sm">Ask Claude to use any MCP tool.</p>
                <p className="text-xs mt-1 hd-text-muted">
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

        <div className="hd-input-bar">
          <div className="flex gap-2">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Claude to use MCP tools... (Ctrl+Enter to send)"
              disabled={running}
              rows={3}
              className="hd-textarea flex-1 text-sm resize-none"
              style={{ opacity: running ? 0.6 : 1 }}
            />
            <button
              onClick={handleSend}
              disabled={running || !prompt.trim()}
              className="hd-btn hd-btn--primary self-end"
              style={{ minWidth: 80 }}
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
          <p className="text-xs mt-1 hd-text-muted">
            Ctrl+Enter to send · Claude will choose and execute MCP tools automatically
          </p>
        </div>
      </div>
    </div>
  );
}
