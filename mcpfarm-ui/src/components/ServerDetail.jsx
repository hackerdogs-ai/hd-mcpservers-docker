import React, { useState, useEffect, useCallback, useRef } from 'react';
import { startServer, stopServer, enableServer, disableServer, updateServerEnv, getApiKey, getBaseUrl, getServerReadme } from '../lib/api.js';
import { mcpClient } from '../lib/mcp.js';
import { getCategoryInfo, getStatusInfo, generateServerIcon, getServerDescription } from '../lib/categories.js';
import { getToolHints } from '../lib/toolHints.js';
import MarkdownViewer from './MarkdownViewer.jsx';
import { getBundledReadme } from '../lib/readmes.js';
import ChatTab from './ChatTab.jsx';

function TerminalOutput({ lines }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);

  if (!lines || lines.length === 0) return null;

  return (
    <div className="sd-terminal" ref={ref}>
      {lines.map((line, i) => (
        <div key={i} className={`sd-term-line ${line.type === 'error' ? 'sd-term-err' : line.type === 'success' ? 'sd-term-ok' : ''}`}>
          <span className="sd-term-prompt">{line.type === 'error' ? '✗' : line.type === 'success' ? '✓' : '›'}</span>
          <span>{line.text}</span>
        </div>
      ))}
    </div>
  );
}

function ToolForm({ tool, onSubmit, loading }) {
  const schema = tool.inputSchema || { type: 'object', properties: {}, required: [] };
  const properties = schema.properties || {};
  const required = schema.required || [];
  const hints = getToolHints(tool.name);
  const [values, setValues] = useState({});

  useEffect(() => {
    const init = {};
    Object.entries(properties).forEach(([key, prop]) => {
      if (prop.type === 'boolean') init[key] = false;
      else init[key] = '';
    });
    setValues(init);
  }, [tool.name]);

  function setValue(key, val) {
    setValues(prev => ({ ...prev, [key]: val }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const args = {};
    Object.entries(properties).forEach(([key, prop]) => {
      const val = values[key];
      if (prop.type === 'integer') { if (val !== '') args[key] = parseInt(val, 10); }
      else if (prop.type === 'number') { if (val !== '') args[key] = parseFloat(val); }
      else if (prop.type === 'boolean') args[key] = val;
      else if (val !== '') args[key] = val;
    });
    onSubmit(args);
  }

  const propEntries = Object.entries(properties);
  const firstStringKey = propEntries.find(
    ([, prop]) => !prop.enum && prop.type !== 'boolean' && prop.type !== 'integer' && prop.type !== 'number'
  )?.[0];

  return (
    <form onSubmit={handleSubmit} className="sd-tool-form">
      {propEntries.length === 0 && (
        <p className="text-xs hd-text-dim">No parameters required.</p>
      )}
      {propEntries.map(([key, prop]) => {
        const fieldHints = hints && key === firstStringKey ? hints : null;
        const isLongField = fieldHints || key === 'arguments';

        return (
          <div key={key} className="sd-form-field">
            <label className="sd-form-label">
              {key}
              {required.includes(key) && <span className="hd-text-required"> *</span>}
              {prop.description && <span className="sd-form-hint"> — {prop.description}</span>}
            </label>
            {prop.enum ? (
              <select
                value={values[key] || ''}
                onChange={e => setValue(key, e.target.value)}
                className="sd-form-input"
              >
                <option value="">— select —</option>
                {prop.enum.map(o => <option key={o} value={o}>{String(o)}</option>)}
              </select>
            ) : prop.type === 'boolean' ? (
              <label className="flex items-center gap-2 text-xs hd-text-secondary">
                <input
                  type="checkbox"
                  checked={values[key] || false}
                  onChange={e => setValue(key, e.target.checked)}
                />
                {key}
              </label>
            ) : isLongField ? (
              <textarea
                value={values[key] || ''}
                onChange={e => setValue(key, e.target.value)}
                placeholder={prop.example || prop.default || fieldHints?.examples?.[0]?.value || ''}
                className="sd-form-input sd-form-textarea"
                rows={3}
              />
            ) : (
              <input
                type={prop.type === 'integer' || prop.type === 'number' ? 'number' : 'text'}
                value={values[key] || ''}
                onChange={e => setValue(key, e.target.value)}
                placeholder={prop.example || prop.default || fieldHints?.examples?.[0]?.value || ''}
                className="sd-form-input"
              />
            )}
            {fieldHints && (
              <div className="sd-field-help">
                {fieldHints.hint && (
                  <p className="sd-field-help-text">{fieldHints.hint}</p>
                )}
                {fieldHints.examples?.length > 0 && (
                  <div className="sd-field-examples">
                    {fieldHints.examples.map(ex => (
                      <button
                        key={ex.label}
                        type="button"
                        onClick={() => setValue(key, ex.value)}
                        title={ex.value}
                        className="sd-example-chip"
                      >
                        {ex.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
      <button type="submit" disabled={loading} className="sd-btn sd-btn--primary" style={{ marginTop: 8 }}>
        {loading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Running...</> : 'Run Tool'}
      </button>
    </form>
  );
}

function ResultViewer({ result, error }) {
  const [collapsed, setCollapsed] = useState(false);
  if (!result && !error) return null;

  function fmt(r) {
    if (!r) return '';
    if (typeof r === 'string') return r;
    if (r.content && Array.isArray(r.content)) {
      return r.content.map(c => {
        if (c.type === 'text') return c.text;
        if (c.type === 'image') return `[image: ${c.mimeType || 'binary'}]`;
        return JSON.stringify(c, null, 2);
      }).join('\n');
    }
    if (r.isError && r.content) return fmt({ content: r.content });
    return JSON.stringify(r, null, 2);
  }

  const text = error ? String(error) : fmt(result);
  const isEmpty = !error && (!text || text.trim() === 'Done.' || text.trim() === 'Command completed with no output.');

  return (
    <div className={`sd-result${error ? ' sd-result--error' : ''}`}>
      <div className="sd-result-head" onClick={() => setCollapsed(c => !c)}>
        <span className={error ? 'sd-result-head--err' : 'sd-result-head--ok'}>
          {error ? '✗ Error' : '✓ Result'}
        </span>
        <span className="hd-result__toggle">{collapsed ? '▶' : '▼'}</span>
      </div>
      {!collapsed && (
        <>
          {isEmpty ? (
            <p className="sd-result-empty">
              No output returned. Check argument format in the Docs tab — e.g. nuclei needs flags like <code>-u https://target.com</code>, or enter a bare IP/hostname (auto-prefixed with <code>-u</code> after server update).
            </p>
          ) : (
            <pre className={`sd-result-body${error ? ' sd-result-body--error' : ''}`}>
              {text}
            </pre>
          )}
        </>
      )}
    </div>
  );
}

function ReadmePanel({ serverName }) {
  const [readme, setReadme] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErr(null);
    setReadme(null);
    getServerReadme(serverName)
      .then(text => { if (!cancelled) setReadme(text); })
      .catch(() => {
        if (cancelled) return;
        const bundled = getBundledReadme(serverName);
        if (bundled) setReadme(bundled);
        else setErr('README not available. Restart auth-gateway to enable the README endpoint.');
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [serverName]);

  if (loading) return <p className="text-xs hd-text-dim">Loading README...</p>;
  if (err) return <p className="text-xs" style={{ color: '#f85149' }}>Could not load README: {err}</p>;
  return <MarkdownViewer source={readme} />;
}

export default function ServerDetail({ serverName, servers, onBack, onRefresh }) {
  const server = servers?.find(s => s.name === serverName);
  const [tools, setTools] = useState([]);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [toolsError, setToolsError] = useState(null);
  const [selectedTool, setSelectedTool] = useState(null);
  const [runLoading, setRunLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultError, setResultError] = useState(null);
  const [termLines, setTermLines] = useState([]);
  const [actionLoading, setActionLoading] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [toolPanelTab, setToolPanelTab] = useState('run');

  const cat = getCategoryInfo(server?.category);
  const status = getStatusInfo(server || {});
  const desc = getServerDescription(serverName);
  const iconSvg = generateServerIcon(serverName, server?.category, 56);
  const isRunning = server?.health_ok === true;
  const isDisabled = (server?.status || '').toLowerCase() === 'disabled';

  const envObj = server?.env
    ? (typeof server.env === 'string' ? JSON.parse(server.env) : server.env)
    : {};
  const envKeys = Object.keys(envObj);

  const log = useCallback((text, type = 'info') => {
    setTermLines(prev => [...prev, { text, type, ts: Date.now() }]);
  }, []);

  const loadTools = useCallback(async () => {
    if (!serverName) return;
    setToolsLoading(true);
    setToolsError(null);
    log(`Loading tools from ${serverName}...`);
    mcpClient.resetSession(serverName);
    try {
      const t = await mcpClient.listTools(serverName);
      setTools(t);
      log(`Found ${t.length} tools`, 'success');
    } catch (err) {
      setToolsError(err.message);
      log(`Failed: ${err.message}`, 'error');
    } finally {
      setToolsLoading(false);
    }
  }, [serverName, log]);

  useEffect(() => {
    setTools([]);
    setSelectedTool(null);
    setResult(null);
    setResultError(null);
    setTermLines([]);
    setActiveTab('overview');
    setToolPanelTab('run');
    if (server && isRunning) loadTools();
  }, [serverName]);

  async function handleAction(action) {
    setActionLoading(action);
    const labels = { start: 'Starting', stop: 'Stopping', test: 'Testing', enable: 'Enabling', disable: 'Disabling' };
    log(`${labels[action] || action}...`);
    try {
      if (action === 'enable') {
        await enableServer(serverName);
        log('Server enabled — route added to Caddy', 'success');
        onRefresh?.();
      } else if (action === 'disable') {
        await disableServer(serverName);
        log('Server disabled — route removed from Caddy', 'success');
        setTools([]);
        onRefresh?.();
      } else if (action === 'start') {
        await startServer(serverName);
        mcpClient.resetSession(serverName);
        for (let i = 0; i < 15; i++) {
          await new Promise(r => setTimeout(r, 3000));
          log(`Waiting for health check... (${i + 1})`);
          const list = await onRefresh?.();
          if (Array.isArray(list) && list.find(s => s.name === serverName)?.health_ok) {
            log('Server is healthy', 'success');
            loadTools();
            break;
          }
        }
      } else if (action === 'stop') {
        await stopServer(serverName);
        mcpClient.resetSession(serverName);
        log('Server stopped', 'success');
        setTools([]);
        onRefresh?.();
      } else if (action === 'test') {
        log('Initializing MCP session...');
        mcpClient.resetSession(serverName);
        await mcpClient.initialize(serverName);
        log('Session initialized', 'success');
        const t = await mcpClient.listTools(serverName);
        log(`tools/list returned ${t.length} tools`, 'success');
        setTools(t);
        if (t.length > 0) {
          const first = t[0];
          log(`Calling tool: ${first.name}...`);
          try {
            const r = await mcpClient.callTool(serverName, first.name, {});
            log(`Tool call succeeded`, 'success');
            setResult(r);
          } catch (e) {
            log(`Tool call: ${e.message}`, 'error');
          }
        }
      }
    } catch (err) {
      log(`${action} failed: ${err.message}`, 'error');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleRunTool(args) {
    if (!selectedTool) return;
    setRunLoading(true);
    setResult(null);
    setResultError(null);
    log(`Running ${selectedTool.name}...`);
    try {
      const r = await mcpClient.callTool(serverName, selectedTool.name, args);
      setResult(r);
      log(`${selectedTool.name} completed`, 'success');
    } catch (err) {
      setResultError(err.message);
      log(`${selectedTool.name} failed: ${err.message}`, 'error');
    } finally {
      setRunLoading(false);
    }
  }

  const baseUrl = getBaseUrl() || window.location.origin;
  const mcpConfig = JSON.stringify({
    mcpServers: {
      [serverName]: {
        url: `${baseUrl}/${serverName}/mcp`,
        headers: {
          Authorization: 'Bearer <your-api-key>'
        }
      }
    }
  }, null, 2);

  const TABS = [
    { id: 'overview', label: 'Overview' },
    { id: 'tools', label: `Tools${tools.length ? ` (${tools.length})` : ''}` },
    { id: 'chat', label: 'Chat' },
    { id: 'readme', label: 'README' },
    { id: 'config', label: 'Config' },
    { id: 'connect', label: 'Connect' },
  ];

  return (
    <div className="sd-shell">
      {/* Header */}
      <div className="sd-header">
        <button onClick={onBack} className="sd-back">← Back</button>
        <div className="sd-header-main">
          <span className="sd-header-icon" dangerouslySetInnerHTML={{ __html: iconSvg }} />
          <div className="sd-header-info">
            <div className="sd-header-name">
              {serverName.replace(/-mcp$/, '')}
              <span className="sd-header-suffix">-mcp</span>
            </div>
            <div className="sd-header-meta">
              <span className="mkt-chip" style={{ color: cat.color, background: cat.bg, borderColor: cat.border }}>
                {cat.label}
              </span>
              <span className="sd-status-badge" style={{ color: status.color }}>
                <span className="sd-status-dot" style={{ background: status.dot }} />
                {status.label}
              </span>
              <span className="hd-text-muted">Port {server?.port}</span>
            </div>
            <div className="sd-header-desc">{desc}</div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="sd-actions">
          {isDisabled ? (
            <button
              onClick={() => handleAction('enable')}
              disabled={!!actionLoading}
              className="sd-btn sd-btn--start"
            >
              {actionLoading === 'enable' ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Enabling...</> : '✓ Enable'}
            </button>
          ) : !isRunning ? (
            <>
              <button
                onClick={() => handleAction('start')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--start"
              >
                {actionLoading === 'start' ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Starting...</> : '▶ Start'}
              </button>
              <button
                onClick={() => handleAction('disable')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--disable"
              >
                {actionLoading === 'disable' ? 'Disabling...' : '⊘ Disable'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => handleAction('stop')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--stop"
              >
                {actionLoading === 'stop' ? 'Stopping...' : '■ Stop'}
              </button>
              <button
                onClick={() => handleAction('test')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--test"
              >
                {actionLoading === 'test' ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Testing...</> : '⚡ Test'}
              </button>
              <button
                onClick={() => handleAction('disable')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--disable"
              >
                {actionLoading === 'disable' ? 'Disabling...' : '⊘ Disable'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="sd-tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`sd-tab ${activeTab === t.id ? 'sd-tab--active' : ''}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="sd-content">
        {activeTab === 'overview' && (
          <div className="sd-section">
            <h3 className="sd-section-title">Server Info</h3>
            <div className="sd-info-grid">
              <div className="sd-info-item">
                <span className="sd-info-label">Image</span>
                <span className="sd-info-value">{server?.image}</span>
              </div>
              <div className="sd-info-item">
                <span className="sd-info-label">Port</span>
                <span className="sd-info-value">{server?.port}</span>
              </div>
              <div className="sd-info-item">
                <span className="sd-info-label">Category</span>
                <span className="sd-info-value" style={{ color: cat.color }}>{cat.label}</span>
              </div>
              <div className="sd-info-item">
                <span className="sd-info-label">Status</span>
                <span className="sd-info-value" style={{ color: status.color }}>{status.label}</span>
              </div>
              <div className="sd-info-item">
                <span className="sd-info-label">Tools</span>
                <span className="sd-info-value">{tools.length || (isRunning ? 'Loading...' : '—')}</span>
              </div>
              {envKeys.length > 0 && (
                <div className="sd-info-item">
                  <span className="sd-info-label">API Keys</span>
                  <span className="sd-info-value">{envKeys.join(', ')}</span>
                </div>
              )}
            </div>

            <TerminalOutput lines={termLines} />
          </div>
        )}

        {activeTab === 'tools' && (
          <div className="sd-tools-layout">
            <div className="sd-tools-list">
              <div className="sd-tools-list-head">
                <span>{tools.length} Tools</span>
                <button onClick={loadTools} disabled={toolsLoading} className="sd-btn sd-btn--sm">
                  {toolsLoading ? '...' : '↻'}
                </button>
              </div>
              {!isRunning && (
                <div className="sd-tools-notice">
                  Server is stopped. Start it to load tools.
                </div>
              )}
              {toolsError && (
                <div className="sd-tools-notice" style={{ color: '#f85149' }}>{toolsError}</div>
              )}
              {tools.map(tool => (
                <button
                  key={tool.name}
                  onClick={() => { setSelectedTool(tool); setResult(null); setResultError(null); setToolPanelTab('run'); }}
                  className={`sd-tool-item ${selectedTool?.name === tool.name ? 'sd-tool-item--active' : ''}`}
                >
                  <div className="sd-tool-name">{tool.name}</div>
                  {tool.description && <div className="sd-tool-desc">{tool.description}</div>}
                </button>
              ))}
            </div>

            <div className="sd-tools-main">
              {!selectedTool ? (
                <div className="sd-tools-empty">Select a tool to configure and run</div>
              ) : (
                <div className="sd-tools-form-wrap">
                  <h3 className="sd-section-title" style={{ color: '#58a6ff' }}>{selectedTool.name}</h3>
                  {(() => {
                    const h = getToolHints(selectedTool.name);
                    return h?.description ? (
                      <div className="sd-tool-desc-box">{h.description}</div>
                    ) : selectedTool.description ? (
                      <p className="text-xs mb-3 hd-text-dim">{selectedTool.description}</p>
                    ) : null;
                  })()}

                  <div className="sd-tool-subtabs">
                    <button
                      type="button"
                      className={`sd-tool-subtab ${toolPanelTab === 'run' ? 'sd-tool-subtab--active' : ''}`}
                      onClick={() => setToolPanelTab('run')}
                    >
                      Run
                    </button>
                    <button
                      type="button"
                      className={`sd-tool-subtab ${toolPanelTab === 'docs' ? 'sd-tool-subtab--active' : ''}`}
                      onClick={() => setToolPanelTab('docs')}
                    >
                      Docs
                    </button>
                  </div>

                  {toolPanelTab === 'run' ? (
                    <>
                      <ToolForm
                        key={selectedTool.name}
                        tool={selectedTool}
                        onSubmit={handleRunTool}
                        loading={runLoading}
                      />
                      <ResultViewer result={result} error={resultError} />
                    </>
                  ) : (
                    <div className="sd-tool-docs">
                      {(() => {
                        const h = getToolHints(selectedTool.name);
                        if (!h) {
                          return (
                            <p className="text-xs hd-text-dim">
                              No detailed documentation for this tool. See the README tab for server documentation.
                            </p>
                          );
                        }
                        return (
                          <>
                            {h.description && <p className="sd-tool-docs-desc">{h.description}</p>}
                            {h.hint && (
                              <div className="sd-tool-docs-section">
                                <h4>Usage</h4>
                                <p>{h.hint}</p>
                              </div>
                            )}
                            {h.examples?.length > 0 && (
                              <div className="sd-tool-docs-section">
                                <h4>Examples</h4>
                                <ul className="sd-tool-docs-examples">
                                  {h.examples.map(ex => (
                                    <li key={ex.label}>
                                      <strong>{ex.label}</strong>
                                      <code>{ex.value}</code>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            <p className="text-xs mt-4 hd-text-muted">
                              See the README tab for full server documentation, deploy instructions, and example prompts.
                            </p>
                          </>
                        );
                      })()}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'chat' && (
          <ChatTab
            serverName={serverName}
            tools={tools}
            isRunning={isRunning}
            onLoadTools={(t) => setTools(t)}
          />
        )}

        {activeTab === 'readme' && (
          <div className="sd-section sd-readme-section">
            <h3 className="sd-section-title">README — {serverName}</h3>
            <ReadmePanel serverName={serverName} />
          </div>
        )}

        {activeTab === 'config' && (
          <div className="sd-section">
            <h3 className="sd-section-title">Environment Variables</h3>
            {envKeys.length === 0 ? (
              <p className="text-xs hd-text-dim">This server has no configurable environment variables.</p>
            ) : (
              <EnvEditor serverName={serverName} envObj={envObj} onSaved={() => { onRefresh?.(); log('Config saved', 'success'); }} log={log} />
            )}
            <TerminalOutput lines={termLines} />
          </div>
        )}

        {activeTab === 'connect' && (
          <div className="sd-section">
            <h3 className="sd-section-title">Connect from any LLM</h3>
            <p className="text-xs mb-3 hd-text-dim">
              Add this to your MCP client configuration (Claude Desktop, Cursor, Windsurf, etc.):
            </p>
            <div className="sd-code-block">
              <div className="sd-code-head">
                <span>MCP Server Config</span>
                <button
                  className="sd-btn sd-btn--sm"
                  onClick={() => { navigator.clipboard.writeText(mcpConfig); log('Copied to clipboard', 'success'); }}
                >
                  Copy
                </button>
              </div>
              <pre className="sd-code-body">{mcpConfig}</pre>
            </div>

            <h3 className="sd-section-title" style={{ marginTop: 24 }}>Direct URL</h3>
            <div className="sd-code-block">
              <pre className="sd-code-body" style={{ padding: '8px 12px' }}>
                {`${baseUrl}/${serverName}/mcp`}
              </pre>
            </div>

            <h3 className="sd-section-title" style={{ marginTop: 24 }}>cURL Test</h3>
            <div className="sd-code-block">
              <pre className="sd-code-body">{`curl -X POST ${baseUrl}/${serverName}/mcp \\
  -H "Authorization: Bearer <your-api-key>" \\
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'`}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EnvEditor({ serverName, envObj, onSaved, log }) {
  const keys = Object.keys(envObj);
  const [values, setValues] = useState({ ...envObj });
  const [saving, setSaving] = useState(false);
  const [showValues, setShowValues] = useState({});

  async function handleSave(restart = false) {
    setSaving(true);
    log('Saving environment variables...');
    try {
      await updateServerEnv(serverName, values);
      log('Environment variables saved', 'success');
      if (restart) {
        log('Restarting server...');
        await startServer(serverName);
        log('Server restarted', 'success');
      }
      onSaved?.();
    } catch (err) {
      log(`Save failed: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      {keys.map(key => (
        <div key={key} className="sd-form-field">
          <label className="sd-form-label">{key}</label>
          <div className="flex gap-2">
            <input
              type={showValues[key] ? 'text' : 'password'}
              value={values[key] || ''}
              onChange={e => setValues(p => ({ ...p, [key]: e.target.value }))}
              placeholder={`Enter ${key}`}
              className="sd-form-input"
              style={{ flex: 1 }}
            />
            <button
              type="button"
              onClick={() => setShowValues(p => ({ ...p, [key]: !p[key] }))}
              className="sd-btn sd-btn--sm"
            >
              {showValues[key] ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>
      ))}
      <div className="flex gap-2 mt-4">
        <button onClick={() => handleSave(false)} disabled={saving} className="sd-btn sd-btn--primary">
          {saving ? 'Saving...' : 'Save'}
        </button>
        <button onClick={() => handleSave(true)} disabled={saving} className="sd-btn sd-btn--test">
          Save & Restart
        </button>
      </div>
    </div>
  );
}
