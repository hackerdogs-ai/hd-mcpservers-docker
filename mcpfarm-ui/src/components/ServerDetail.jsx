import React, { useState, useEffect, useCallback, useRef } from 'react';
import { startServer, stopServer, enableServer, disableServer, deleteServer, updateServerEnv, getApiKey, getBaseUrl, getServerReadme } from '../lib/api.js';
import { mcpClient } from '../lib/mcp.js';
import { getCategoryInfo, getStatusInfo, isServerRunning, generateServerIcon, getServerDescription } from '../lib/categories.js';
import { useTheme } from '../lib/theme.js';
import { getToolHints } from '../lib/toolHints.js';
import MarkdownViewer from './MarkdownViewer.jsx';
import { getBundledReadme } from '../lib/readmes.js';
import ChatTab from './ChatTab.jsx';
import ToolResultContent from './ToolResultContent.jsx';
import { getToolResultDisplayText } from '../lib/toolResult.js';
import Icon from './Icon.jsx';

const ACTION_META = {
  start:   { title: 'Start Server',   verb: 'start',   confirmClass: 'hd-dialog-btn--green' },
  stop:    { title: 'Stop Server',    verb: 'stop',    confirmClass: 'hd-dialog-btn--red' },
  enable:  { title: 'Enable Server',  verb: 'enable',  confirmClass: 'hd-dialog-btn--green' },
  disable: { title: 'Disable Server', verb: 'disable', confirmClass: 'hd-dialog-btn--amber' },
  delete:  { title: 'Delete Server',  verb: 'permanently delete', confirmClass: 'hd-dialog-btn--red' },
};

function ConfirmDialog({ open, title, message, confirmLabel, confirmClass, onConfirm, onCancel, loading }) {
  if (!open) return null;
  return (
    <div className="hd-dialog-overlay" onClick={onCancel}>
      <div className="hd-dialog" onClick={e => e.stopPropagation()}>
        <div className="hd-dialog-title">{title}</div>
        <div className="hd-dialog-body">{message}</div>
        <div className="hd-dialog-actions">
          <button className="hd-dialog-btn hd-dialog-btn--cancel" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button className={`hd-dialog-btn ${confirmClass || 'hd-dialog-btn--confirm'}`} onClick={onConfirm} disabled={loading}>
            {loading ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function TerminalOutput({ lines }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);

  return (
    <div className="sd-terminal" ref={ref}>
      {!lines || lines.length === 0 ? (
        <div className="sd-term-empty">Server activity and test output appear here.</div>
      ) : (
        lines.map((line, i) => (
          <div key={i} className={`sd-term-line ${line.type === 'error' ? 'sd-term-err' : line.type === 'success' ? 'sd-term-ok' : ''}`}>
            <span className="sd-term-prompt"><Icon name={line.type === 'error' ? 'close' : line.type === 'success' ? 'check' : 'chevron_right'} size={16} /></span>
            <span>{line.text}</span>
          </div>
        ))
      )}
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
        <p className="hd-text-dim">No parameters required.</p>
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
              <label className="flex items-center gap-2 hd-text-secondary">
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

  const text = error ? String(error) : getToolResultDisplayText(result);
  const isEmpty = !error && (!text || text.trim() === 'Done.' || text.trim() === 'Command completed with no output.');

  return (
    <div className={`sd-result${error ? ' sd-result--error' : ''}`}>
      <div className="sd-result-head" onClick={() => setCollapsed(c => !c)}>
        <span className={error ? 'sd-result-head--err' : 'sd-result-head--ok'}>
          {error ? <><Icon name="error" size={16} /> Error</> : <><Icon name="check_circle" size={16} /> Result</>}
        </span>
        <span className="hd-result__toggle"><Icon name={collapsed ? 'chevron_right' : 'expand_more'} size={16} /></span>
      </div>
      {!collapsed && (
        <>
          {isEmpty ? (
            <p className="sd-result-empty">
              No output returned. Check argument format in the Docs tab — e.g. nuclei needs flags like <code>-u https://target.com</code>, or enter a bare IP/hostname (auto-prefixed with <code>-u</code> after server update).
            </p>
          ) : (
            <ToolResultContent
              result={result}
              error={error}
              className={`sd-result-body${error ? ' sd-result-body--error' : ''}`}
            />
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

  if (loading) return <p className="hd-text-dim">Loading README...</p>;
  if (err) return <p style={{ color: '#f85149' }}>Could not load README: {err}</p>;
  return <MarkdownViewer source={readme} />;
}

export default function ServerDetail({ serverName, servers, onBack, onRefresh }) {
  useTheme();
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
  const [confirm, setConfirm] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [toolPanelTab, setToolPanelTab] = useState('run');

  const cat = getCategoryInfo(server?.category);
  const status = getStatusInfo(server || {});
  const desc = getServerDescription(serverName);
  const iconSvg = generateServerIcon(serverName, server?.category, 56);
  const isRunning = isServerRunning(server);
  const wasRunningRef = useRef(false);
  const toolsLoadedRef = useRef(false);
  const loadGenRef = useRef(0);
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
    const gen = ++loadGenRef.current;
    setToolsLoading(true);
    setToolsError(null);
    log(`Loading tools from ${serverName}...`);
    mcpClient.resetSession(serverName);
    try {
      const t = await mcpClient.listTools(serverName);
      if (gen !== loadGenRef.current) return;
      setTools(t);
      log(`Found ${t.length} tools`, 'success');
    } catch (err) {
      if (gen !== loadGenRef.current) return;
      setToolsError(err.message);
      log(`Failed: ${err.message}`, 'error');
    } finally {
      if (gen === loadGenRef.current) setToolsLoading(false);
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
    loadGenRef.current += 1;
    wasRunningRef.current = false;
    toolsLoadedRef.current = false;
  }, [serverName]);

  useEffect(() => {
    if (!serverName) return;
    if (isRunning && !toolsLoadedRef.current) {
      toolsLoadedRef.current = true;
      wasRunningRef.current = true;
      loadTools();
    } else if (isRunning) {
      wasRunningRef.current = true;
    } else if (wasRunningRef.current) {
      loadGenRef.current += 1;
      toolsLoadedRef.current = false;
      wasRunningRef.current = false;
      setTools([]);
      setToolsLoading(false);
      setToolsError(null);
    }
  }, [serverName, isRunning, loadTools]);

  function requestAction(action) {
    const meta = ACTION_META[action];
    if (!meta) return;
    const displayName = serverName.replace(/-mcp$/, '');
    setConfirm({
      action,
      title: meta.title,
      message: `Are you sure you want to ${meta.verb} "${displayName}"?`,
      confirmLabel: meta.title,
      confirmClass: meta.confirmClass,
    });
  }

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
        toolsLoadedRef.current = false;
        wasRunningRef.current = false;
        setTools([]);
        onRefresh?.();
      } else if (action === 'start') {
        await startServer(serverName);
        mcpClient.resetSession(serverName);
        toolsLoadedRef.current = false;
        for (let i = 0; i < 15; i++) {
          await new Promise(r => setTimeout(r, 3000));
          log(`Waiting for health check... (${i + 1})`);
          const list = await onRefresh?.();
          if (Array.isArray(list) && isServerRunning(list.find(s => s.name === serverName))) {
            log('Server is healthy', 'success');
            toolsLoadedRef.current = true;
            wasRunningRef.current = true;
            loadTools();
            break;
          }
        }
      } else if (action === 'stop') {
        loadGenRef.current += 1;
        await mcpClient.terminateSession(serverName);
        await stopServer(serverName);
        toolsLoadedRef.current = false;
        wasRunningRef.current = false;
        setTools([]);
        setToolsLoading(false);
        setToolsError(null);
        for (let i = 0; i < 5; i++) {
          const list = await onRefresh?.();
          if (Array.isArray(list) && !isServerRunning(list.find(s => s.name === serverName))) break;
          await new Promise(r => setTimeout(r, 1000));
        }
        log('Server stopped', 'success');
      } else if (action === 'delete') {
        await mcpClient.terminateSession(serverName);
        await deleteServer(serverName);
        log('Server deleted', 'success');
        onRefresh?.();
        onBack?.();
        return;
      } else if (action === 'test') {
        log('Initializing MCP session...');
        mcpClient.resetSession(serverName);
        await mcpClient.initialize(serverName);
        log('Session initialized', 'success');
        const t = await mcpClient.listTools(serverName);
        log(`tools/list returned ${t.length} tools`, 'success');
        setTools(t);
        toolsLoadedRef.current = true;
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

  async function executeConfirmedAction() {
    if (!confirm) return;
    await handleAction(confirm.action);
    setConfirm(null);
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
        <div className="sd-header-left">
          <button type="button" onClick={onBack} className="sd-back" aria-label="Back to catalog">
            <Icon name="arrow_back" size={16} /> Back
          </button>
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
        </div>

        {/* Action buttons */}
        <div className="sd-actions">
          {isDisabled ? (
            <button
              onClick={() => requestAction('enable')}
              disabled={!!actionLoading}
              className="sd-btn sd-btn--start"
            >
              {actionLoading === 'enable' ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Enabling...</> : <><Icon name="check" size={16} /> Enable</>}
            </button>
          ) : !isRunning ? (
            <>
              <button
                onClick={() => requestAction('start')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--start"
              >
                {actionLoading === 'start' ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Starting...</> : <><Icon name="play_arrow" size={16} fill /> Start</>}
              </button>
              <button
                onClick={() => requestAction('disable')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--disable"
              >
                {actionLoading === 'disable' ? 'Disabling...' : <><Icon name="block" size={16} /> Disable</>}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => requestAction('stop')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--stop"
              >
                {actionLoading === 'stop' ? 'Stopping...' : <><Icon name="stop" size={16} fill /> Stop</>}
              </button>
              <button
                onClick={() => requestAction('disable')}
                disabled={!!actionLoading}
                className="sd-btn sd-btn--disable"
              >
                {actionLoading === 'disable' ? 'Disabling...' : <><Icon name="block" size={16} /> Disable</>}
              </button>
            </>
          )}
          <button
            onClick={() => requestAction('delete')}
            disabled={!!actionLoading}
            className="sd-btn sd-btn--delete"
          >
            {actionLoading === 'delete' ? 'Deleting...' : <><Icon name="delete" size={16} /> Delete</>}
          </button>
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
                <span className="sd-info-value">{tools.length || (toolsLoading ? 'Loading...' : isRunning ? '0' : '—')}</span>
              </div>
              {envKeys.length > 0 && (
                <div className="sd-info-item">
                  <span className="sd-info-label">API Keys</span>
                  <span className="sd-info-value">{envKeys.join(', ')}</span>
                </div>
              )}
            </div>

            <div className="sd-terminal-panel">
              <div className="sd-terminal-head">
                <h3 className="sd-section-title" style={{ marginBottom: 0 }}>Terminal</h3>
                {isRunning && (
                  <button
                    onClick={() => handleAction('test')}
                    disabled={!!actionLoading}
                    className="sd-btn sd-btn--test"
                  >
                    {actionLoading === 'test' ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Testing...</> : <><Icon name="bolt" size={16} /> Test</>}
                  </button>
                )}
              </div>
              <TerminalOutput lines={termLines} />
            </div>
          </div>
        )}

        {activeTab === 'tools' && (
          <div className="sd-tools-layout">
            <div className="sd-tools-list">
              <div className="sd-tools-list-head">
                <span>{tools.length} Tools</span>
                <button onClick={loadTools} disabled={toolsLoading} className="sd-btn sd-btn--sm" aria-label="Reload tools">
                  {toolsLoading ? <span className="spinner" style={{ width: 12, height: 12 }} /> : <Icon name="refresh" size={16} />}
                </button>
              </div>
              {toolsLoading && tools.length === 0 && (
                <div className="sd-tools-notice" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="spinner" style={{ width: 14, height: 14 }} />
                  Loading tools...
                </div>
              )}
              {!isRunning && tools.length === 0 && !toolsLoading && (
                <div className="sd-tools-notice">
                  Server is not running. Start it to load tools.
                </div>
              )}
              {isRunning && tools.length === 0 && !toolsLoading && (
                <div className="sd-tools-notice">
                  <button onClick={loadTools} className="sd-btn sd-btn--primary" style={{ marginTop: 4 }}>
                    Load Tools
                  </button>
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
                      <p className="mb-3 hd-text-dim">{selectedTool.description}</p>
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
                            <p className="hd-text-dim">
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
                            <p className="mt-4 hd-text-muted">
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
          <ConfigTab
            serverName={serverName}
            server={server}
            envObj={envObj}
            baseUrl={baseUrl}
            farmKey={getApiKey()}
            onLog={log}
            onSaved={() => onRefresh?.()}
          />
        )}

        {activeTab === 'connect' && (
          <div className="sd-section">
            <h3 className="sd-section-title">Connect from any LLM</h3>
            <p className="mb-3 hd-text-dim">
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
              <pre className="sd-code-body">{`${baseUrl}/${serverName}/mcp`}</pre>
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

      <ConfirmDialog
        open={!!confirm}
        title={confirm?.title}
        message={confirm?.message}
        confirmLabel={confirm?.confirmLabel}
        confirmClass={confirm?.confirmClass}
        onConfirm={executeConfirmedAction}
        onCancel={() => setConfirm(null)}
        loading={!!actionLoading}
      />
    </div>
  );
}

// Env vars that are managed by the farm/runtime, not user-supplied secrets.
const RUNTIME_ENV_KEYS = new Set(['MCP_TRANSPORT', 'MCP_PORT']);

/**
 * Build the set of MCP client configurations for a server, injecting the actual
 * env values the user has entered. Keys with empty values fall back to an
 * obvious `<your-KEY>` placeholder so the emitted config is still valid & usable.
 */
function buildMcpConfigs({ serverName, server, values, baseUrl, farmKey }) {
  const secretKeys = Object.keys(values).filter(k => !RUNTIME_ENV_KEYS.has(k));
  const gatewayBase = (baseUrl || window.location.origin).replace(/\/$/, '');

  const envBlock = {};
  let hasMissing = false;
  secretKeys.forEach(k => {
    const v = values[k];
    if (v && String(v).length) {
      envBlock[k] = String(v);
    } else {
      envBlock[k] = `<your-${k.toLowerCase()}>`;
      hasMissing = true;
    }
  });

  // Farm gateway (recommended) — authenticated via farm key; secret keys live server-side.
  const farm = {
    mcpServers: {
      [serverName]: {
        url: `${gatewayBase}/${serverName}/mcp`,
        headers: {
          Authorization: `Bearer ${farmKey && farmKey.length ? farmKey : '<your-farm-api-key>'}`,
        },
      },
    },
  };

  // Local stdio via Docker — secret keys are passed straight into the container.
  const dockerArgs = ['run', '-i', '--rm', '-e', 'MCP_TRANSPORT'];
  secretKeys.forEach(k => { dockerArgs.push('-e', k); });
  dockerArgs.push(server?.image || `hackerdogs/${serverName}:latest`);
  const local = {
    mcpServers: {
      [serverName]: {
        command: 'docker',
        args: dockerArgs,
        env: { MCP_TRANSPORT: 'stdio', ...envBlock },
      },
    },
  };

  // Direct HTTP to the container port (no gateway auth) — secret keys stay server-side.
  const direct = {
    mcpServers: {
      [serverName]: {
        url: `http://localhost:${server?.port || 'PORT'}/mcp`,
      },
    },
  };

  return {
    hasMissing,
    secretKeys,
    blocks: [
      {
        id: 'farm',
        label: 'Farm Gateway (recommended)',
        note: 'Authenticated MCP Farm endpoint. The Authorization bearer is your farm API key. Server-side secrets are not included here — they are held by the server.',
        json: JSON.stringify(farm, null, 2),
      },
      {
        id: 'local',
        label: 'Local (Docker / stdio)',
        note: secretKeys.length
          ? 'Runs the container locally over stdio. Includes the API key values you entered above.'
          : 'Runs the container locally over stdio. This server needs no API keys.',
        json: JSON.stringify(local, null, 2),
      },
      {
        id: 'direct',
        label: 'Direct HTTP (no gateway)',
        note: 'Connects straight to the running container port. Secrets are configured on the server, not in this config.',
        json: JSON.stringify(direct, null, 2),
      },
    ],
  };
}

function ConfigBlock({ block, onCopy }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="sd-code-block" style={{ marginBottom: 16 }}>
      <div className="sd-code-head">
        <span>{block.label}</span>
        <button
          className="sd-btn sd-btn--sm"
          onClick={() => {
            navigator.clipboard.writeText(block.json);
            setCopied(true);
            onCopy?.(block.label);
            setTimeout(() => setCopied(false), 1500);
          }}
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      {block.note && <p className="hd-text-muted" style={{ margin: '8px 12px 0' }}>{block.note}</p>}
      <pre className="sd-code-body">{block.json}</pre>
    </div>
  );
}

function ConfigTab({ serverName, server, envObj, baseUrl, farmKey, onLog, onSaved }) {
  const keys = Object.keys(envObj);
  const [values, setValues] = useState({ ...envObj });
  const [saving, setSaving] = useState(false);
  const [showValues, setShowValues] = useState({});
  const [status, setStatus] = useState(null);
  const [generated, setGenerated] = useState(null);

  async function handleSave(restart = false) {
    setSaving(true);
    setStatus(null);
    try {
      await updateServerEnv(serverName, values);
      if (restart) {
        await startServer(serverName);
        setStatus({ type: 'success', text: 'Saved and server restarted.' });
      } else {
        setStatus({ type: 'success', text: 'Environment variables saved.' });
      }
      onSaved?.();
    } catch (err) {
      setStatus({ type: 'error', text: err.message });
    } finally {
      setSaving(false);
    }
  }

  function handleGenerate() {
    // Generate from the live values the user has entered, not just the saved env.
    setGenerated(buildMcpConfigs({ serverName, server, values, baseUrl, farmKey }));
    onLog?.('Generated MCP server configurations', 'success');
  }

  return (
    <div className="sd-section">
      <h3 className="sd-section-title">Environment Variables</h3>
      {keys.length === 0 ? (
        <p className="hd-text-dim">This server has no configurable environment variables.</p>
      ) : (
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
          {status && (
            <p className={status.type === 'error' ? 'sd-config-status sd-config-status--error' : 'sd-config-status sd-config-status--ok'}>
              {status.text}
            </p>
          )}
          <div className="flex gap-2 mt-4">
            <button onClick={() => handleSave(false)} disabled={saving} className="sd-btn sd-btn--primary">
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button onClick={() => handleSave(true)} disabled={saving} className="sd-btn sd-btn--test">
              Save & Restart
            </button>
          </div>
        </div>
      )}

      <div className="sd-config-generate" style={{ marginTop: 28 }}>
        <div className="sd-terminal-head" style={{ marginBottom: 8 }}>
          <h3 className="sd-section-title" style={{ marginBottom: 0 }}>MCP Server Configurations</h3>
          <button onClick={handleGenerate} className="sd-btn sd-btn--primary">
            {generated ? <><Icon name="refresh" size={16} /> Regenerate</> : 'Generate MCP Configurations'}
          </button>
        </div>
        <p className="hd-text-dim" style={{ marginBottom: 12 }}>
          {keys.length === 0
            ? 'Generate ready-to-paste MCP client configs for connecting to this server.'
            : 'Generate ready-to-paste MCP client configs. The Docker/stdio config embeds the API key values entered above (save them first to persist).'}
        </p>

        {generated && (
          <>
            {generated.hasMissing && (
              <p className="sd-config-status sd-config-status--error" style={{ marginBottom: 12 }}>
                Some API keys are empty — those fields use a <code>&lt;your-key&gt;</code> placeholder. Enter and save the keys, then regenerate.
              </p>
            )}
            {generated.blocks.map(block => (
              <ConfigBlock key={block.id} block={block} onCopy={label => onLog?.(`Copied ${label} config`, 'success')} />
            ))}
          </>
        )}
      </div>
    </div>
  );
}
