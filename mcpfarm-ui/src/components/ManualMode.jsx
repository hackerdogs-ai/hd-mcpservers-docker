import React, { useState, useEffect, useCallback } from 'react';
import { mcpClient } from '../lib/mcp.js';
import { startServer, updateServerEnv, startServer as restartServer } from '../lib/api.js';
import { getToolHints } from '../lib/toolHints.js';
import { isServerRunning } from '../lib/categories.js';
import ToolResultContent from './ToolResultContent.jsx';

// ─── Tool Form ────────────────────────────────────────────────────────────────

function ToolForm({ tool, onSubmit, loading }) {
  const schema = tool.inputSchema || { type: 'object', properties: {}, required: [] };
  const properties = schema.properties || {};
  const required = schema.required || [];
  const hints = getToolHints(tool.name);

  const [values, setValues] = useState(() => {
    const init = {};
    Object.entries(properties).forEach(([key, prop]) => {
      if (prop.type === 'boolean') init[key] = false;
      else if (prop.type === 'integer' || prop.type === 'number') init[key] = '';
      else init[key] = '';
    });
    return init;
  });

  useEffect(() => {
    const init = {};
    Object.entries(properties).forEach(([key, prop]) => {
      if (prop.type === 'boolean') init[key] = false;
      else if (prop.type === 'integer' || prop.type === 'number') init[key] = '';
      else init[key] = '';
    });
    setValues(init);
  }, [tool.name]);

  function setValue(key, val) {
    setValues((prev) => ({ ...prev, [key]: val }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const args = {};
    Object.entries(properties).forEach(([key, prop]) => {
      const val = values[key];
      if (prop.type === 'integer') args[key] = val === '' ? undefined : parseInt(val, 10);
      else if (prop.type === 'number') args[key] = val === '' ? undefined : parseFloat(val);
      else if (prop.type === 'boolean') args[key] = val;
      else if (val !== '') args[key] = val;
    });
    // Remove undefined
    Object.keys(args).forEach((k) => args[k] === undefined && delete args[k]);
    onSubmit(args);
  }

  const propEntries = Object.entries(properties);
  const firstStringKey = propEntries.find(
    ([, prop]) => !prop.enum && prop.type !== 'boolean' && prop.type !== 'integer' && prop.type !== 'number'
  )?.[0];

  if (propEntries.length === 0 && !hints?.description) return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <p className="text-xs" style={{ color: '#8b949e' }}>This tool takes no parameters.</p>
      <button type="submit" disabled={loading} className="mt-2 px-4 py-2 rounded text-sm font-medium" style={{ background: loading ? '#238636' : '#3fb950', color: '#0d1117' }}>
        {loading ? 'Running...' : 'Run Tool'}
      </button>
    </form>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {propEntries.length === 0 && (
        <p className="text-xs" style={{ color: '#8b949e' }}>
          This tool takes no parameters.
        </p>
      )}

      {propEntries.map(([key, prop]) => {
        const isRequired = required.includes(key);
        const label = (
          <label className="block text-xs font-medium mb-1" style={{ color: '#c9d1d9' }}>
            {key}
            {isRequired && <span style={{ color: '#f85149' }}> *</span>}
            {prop.description && (
              <span className="ml-1 font-normal" style={{ color: '#8b949e' }}>
                — {prop.description}
              </span>
            )}
          </label>
        );

        if (prop.enum) {
          return (
            <div key={key}>
              {label}
              <select
                value={values[key]}
                onChange={(e) => setValue(key, e.target.value)}
                className="w-full px-2 py-1.5 rounded text-xs border"
                style={{
                  background: '#0d1117',
                  borderColor: '#30363d',
                  color: '#e6edf3',
                  outline: 'none',
                }}
              >
                <option value="">— select —</option>
                {prop.enum.map((opt) => (
                  <option key={opt} value={opt}>
                    {String(opt)}
                  </option>
                ))}
              </select>
            </div>
          );
        }

        if (prop.type === 'boolean') {
          return (
            <div key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                id={`field-${key}`}
                checked={values[key]}
                onChange={(e) => setValue(key, e.target.checked)}
                style={{ accentColor: '#3fb950' }}
              />
              <label htmlFor={`field-${key}`} className="text-xs" style={{ color: '#c9d1d9' }}>
                {key}
                {isRequired && <span style={{ color: '#f85149' }}> *</span>}
              </label>
            </div>
          );
        }

        if (prop.type === 'integer' || prop.type === 'number') {
          return (
            <div key={key}>
              {label}
              <input
                type="number"
                value={values[key]}
                onChange={(e) => setValue(key, e.target.value)}
                placeholder={prop.default !== undefined ? String(prop.default) : ''}
                className="w-full px-2 py-1.5 rounded text-xs border"
                style={{
                  background: '#0d1117',
                  borderColor: '#30363d',
                  color: '#e6edf3',
                  outline: 'none',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
                onBlur={(e) => (e.target.style.borderColor = '#30363d')}
              />
            </div>
          );
        }

        // String / default
        const fieldHints = hints && key === firstStringKey ? hints : null;
        return (
          <div key={key}>
            {label}
            <input
              type="text"
              value={values[key]}
              onChange={(e) => setValue(key, e.target.value)}
              placeholder={prop.example || prop.default || (fieldHints?.examples?.[0]?.value) || ''}
              className="w-full px-2 py-1.5 rounded text-xs border"
              style={{
                background: '#0d1117',
                borderColor: '#30363d',
                color: '#e6edf3',
                outline: 'none',
              }}
              onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
              onBlur={(e) => (e.target.style.borderColor = '#30363d')}
            />
            {fieldHints && (
              <div className="mt-1.5 space-y-1.5">
                {fieldHints.hint && (
                  <p className="text-xs" style={{ color: '#8b949e' }}>
                    {fieldHints.hint}
                  </p>
                )}
                {fieldHints.examples && fieldHints.examples.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {fieldHints.examples.map((ex) => (
                      <button
                        key={ex.label}
                        type="button"
                        onClick={() => setValue(key, ex.value)}
                        title={ex.value}
                        className="px-2 py-0.5 rounded text-xs transition-colors"
                        style={{
                          background: 'rgba(88,166,255,0.1)',
                          color: '#58a6ff',
                          border: '1px solid rgba(88,166,255,0.25)',
                          cursor: 'pointer',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = 'rgba(88,166,255,0.2)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'rgba(88,166,255,0.1)';
                        }}
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

      <button
        type="submit"
        disabled={loading}
        className="mt-2 px-4 py-2 rounded text-sm font-medium transition-all"
        style={{
          background: loading ? '#238636' : '#3fb950',
          color: '#0d1117',
          opacity: loading ? 0.7 : 1,
        }}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="spinner" style={{ width: 14, height: 14 }} />
            Running...
          </span>
        ) : (
          'Run Tool'
        )}
      </button>
    </form>
  );
}

// ─── Result Viewer ────────────────────────────────────────────────────────────

function ResultViewer({ result, error }) {
  const [collapsed, setCollapsed] = useState(false);

  if (!result && !error) return null;

  return (
    <div
      className="rounded-lg border mt-4"
      style={{ borderColor: error ? '#f85149' : '#30363d', background: '#0d1117' }}
    >
      <div
        className="flex items-center justify-between px-3 py-2 border-b cursor-pointer"
        style={{ borderColor: error ? '#f85149' : '#30363d' }}
        onClick={() => setCollapsed((c) => !c)}
      >
        <span className="text-xs font-semibold" style={{ color: error ? '#f85149' : '#3fb950' }}>
          {error ? '✗ Error' : '✓ Result'}
        </span>
        <span className="text-xs" style={{ color: '#8b949e' }}>
          {collapsed ? '▶' : '▼'}
        </span>
      </div>

      {!collapsed && (
        <ToolResultContent
          result={result}
          error={error}
          className="result-pre p-3 overflow-auto"
          style={{
            color: error ? '#f85149' : undefined,
            maxHeight: 400,
          }}
        />
      )}
    </div>
  );
}

// ─── Server Config Panel ──────────────────────────────────────────────────────

function ServerConfig({ serverInfo, onClose, onSaved }) {
  const envRaw = serverInfo?.env || '{}';
  const envObj = typeof envRaw === 'string' ? JSON.parse(envRaw) : envRaw;
  const keys = Object.keys(envObj);

  const [values, setValues] = useState(() => ({ ...envObj }));
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);
  const [showValues, setShowValues] = useState({});
  const [restarting, setRestarting] = useState(false);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await updateServerEnv(serverInfo.name, values);
      setSaved(true);
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveAndRestart() {
    setSaving(true);
    setError(null);
    try {
      await updateServerEnv(serverInfo.name, values);
      setRestarting(true);
      await restartServer(serverInfo.name);
      setSaved(true);
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
      setRestarting(false);
    }
  }

  if (keys.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center" style={{ color: '#8b949e' }}>
        <p className="text-sm">This server has no configurable API keys.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold" style={{ color: '#e6edf3' }}>Configure API Keys</h2>
          <p className="text-xs mt-0.5" style={{ color: '#8b949e' }}>
            for <span style={{ color: '#3fb950' }}>{serverInfo?.name}</span>
          </p>
        </div>
        <button onClick={onClose} className="text-xs px-2 py-1 rounded" style={{ color: '#8b949e', border: '1px solid #30363d' }}>
          ✕ Close
        </button>
      </div>

      <div className="space-y-3">
        {keys.map((key) => (
          <div key={key}>
            <label className="block text-xs font-medium mb-1" style={{ color: '#c9d1d9' }}>
              {key}
            </label>
            <div className="flex gap-2">
              <input
                type={showValues[key] ? 'text' : 'password'}
                value={values[key] || ''}
                onChange={(e) => setValues((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder={`Enter ${key}`}
                className="flex-1 px-2 py-1.5 rounded text-xs border"
                style={{ background: '#0d1117', borderColor: '#30363d', color: '#e6edf3', outline: 'none' }}
                onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
                onBlur={(e) => (e.target.style.borderColor = '#30363d')}
              />
              <button
                type="button"
                onClick={() => setShowValues((p) => ({ ...p, [key]: !p[key] }))}
                className="px-2 rounded text-xs"
                style={{ background: '#21262d', color: '#8b949e', border: '1px solid #30363d' }}
              >
                {showValues[key] ? '🙈' : '👁'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {error && <p className="mt-3 text-xs" style={{ color: '#f85149' }}>{error}</p>}
      {saved && !error && <p className="mt-3 text-xs" style={{ color: '#3fb950' }}>✓ Saved — restart the server to apply changes.</p>}

      <div className="flex gap-2 mt-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-3 py-1.5 rounded text-xs font-medium"
          style={{ background: 'rgba(63,185,80,0.15)', color: '#3fb950', border: '1px solid rgba(63,185,80,0.3)' }}
        >
          {saving && !restarting ? 'Saving...' : '💾 Save'}
        </button>
        <button
          onClick={handleSaveAndRestart}
          disabled={saving}
          className="px-3 py-1.5 rounded text-xs font-medium"
          style={{ background: 'rgba(88,166,255,0.1)', color: '#58a6ff', border: '1px solid rgba(88,166,255,0.25)' }}
        >
          {restarting ? 'Restarting...' : '↺ Save & Restart'}
        </button>
      </div>
    </div>
  );
}

// ─── ManualMode ───────────────────────────────────────────────────────────────

export default function ManualMode({ selectedServer, servers, onRefresh }) {
  const [tools, setTools] = useState([]);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [toolsError, setToolsError] = useState(null);
  const [selectedTool, setSelectedTool] = useState(null);
  const [runLoading, setRunLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultError, setResultError] = useState(null);
  const [startLoading, setStartLoading] = useState(false);
  const [startError, setStartError] = useState(null);
  const [showConfig, setShowConfig] = useState(false);

  const serverInfo = servers?.find((s) => (s.name || s.id) === selectedServer);
  const isRunning = isServerRunning(serverInfo);
  const serverEnv = serverInfo?.env ? (typeof serverInfo.env === 'string' ? JSON.parse(serverInfo.env) : serverInfo.env) : {};
  const hasEnvKeys = Object.keys(serverEnv).length > 0;

  const loadTools = useCallback(async () => {
    if (!selectedServer) return;
    setToolsLoading(true);
    setToolsError(null);
    setTools([]);
    setSelectedTool(null);
    setResult(null);
    setResultError(null);
    try {
      const t = await mcpClient.listTools(selectedServer);
      setTools(t);
    } catch (err) {
      setToolsError(err.message);
    } finally {
      setToolsLoading(false);
    }
  }, [selectedServer]);

  useEffect(() => {
    setShowConfig(false);
    if (selectedServer && isRunning) {
      loadTools();
    } else {
      setTools([]);
      setSelectedTool(null);
      setResult(null);
      setResultError(null);
    }
  }, [selectedServer, isRunning]);

  async function handleStartServer() {
    setStartLoading(true);
    setStartError(null);
    try {
      await startServer(selectedServer);
      mcpClient.resetSession(selectedServer);
      onRefresh?.();
      // Wait a moment for server to come up, then load tools
      setTimeout(() => loadTools(), 5000);
    } catch (err) {
      setStartError(err.message);
    } finally {
      setStartLoading(false);
    }
  }

  async function handleRunTool(args) {
    if (!selectedTool) return;
    setRunLoading(true);
    setResult(null);
    setResultError(null);
    try {
      const r = await mcpClient.callTool(selectedServer, selectedTool.name, args);
      setResult(r);
    } catch (err) {
      setResultError(err.message);
    } finally {
      setRunLoading(false);
    }
  }

  if (!selectedServer) {
    return (
      <div className="flex-1 flex items-center justify-center" style={{ color: '#8b949e' }}>
        <div className="text-center">
          <div className="text-4xl mb-3">🖥️</div>
          <p className="text-sm">Select a server from the sidebar to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Tool list panel */}
      <div
        className="w-64 flex-shrink-0 flex flex-col border-r overflow-hidden"
        style={{ borderColor: '#30363d' }}
      >
        <div className="px-3 py-2 border-b flex items-center justify-between" style={{ borderColor: '#30363d' }}>
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8b949e' }}>
            Tools
          </span>
          <div className="flex items-center gap-1">
            {hasEnvKeys && (
              <button
                onClick={() => setShowConfig((v) => !v)}
                title="Configure API keys"
                className="text-xs px-2 py-0.5 rounded transition-colors"
                style={{
                  color: showConfig ? '#e6edf3' : '#8b949e',
                  background: showConfig ? '#21262d' : '#0d1117',
                  border: `1px solid ${showConfig ? '#58a6ff' : '#30363d'}`,
                }}
              >
                🔑 Keys
              </button>
            )}
            <button
              onClick={loadTools}
              disabled={toolsLoading || !isRunning}
              className="text-xs px-2 py-0.5 rounded transition-colors"
              style={{ color: '#8b949e', background: '#0d1117', border: '1px solid #30363d' }}
            >
              ↻
            </button>
          </div>
        </div>

        {/* Stopped server notice */}
        {!isRunning && (
          <div className="p-3 space-y-2">
            <p className="text-xs" style={{ color: '#d29922' }}>
              Server is stopped
            </p>
            <button
              onClick={handleStartServer}
              disabled={startLoading}
              className="w-full py-1.5 rounded text-xs font-medium transition-colors"
              style={{
                background: 'rgba(63,185,80,0.15)',
                color: '#3fb950',
                border: '1px solid rgba(63,185,80,0.3)',
              }}
            >
              {startLoading ? 'Starting...' : '▶ Start Server'}
            </button>
            {startError && (
              <p className="text-xs" style={{ color: '#f85149' }}>
                {startError}
              </p>
            )}
          </div>
        )}

        {toolsLoading && (
          <div className="p-3 text-xs text-center" style={{ color: '#8b949e' }}>
            <span className="spinner" style={{ width: 12, height: 12 }} /> Loading tools...
          </div>
        )}

        {toolsError && (
          <div className="p-3 text-xs" style={{ color: '#f85149' }}>
            {toolsError}
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          {tools.map((tool) => (
            <div
              key={tool.name}
              onClick={() => {
                setSelectedTool(tool);
                setResult(null);
                setResultError(null);
              }}
              className="px-3 py-2 cursor-pointer border-b transition-colors"
              style={{
                borderColor: '#21262d',
                background: selectedTool?.name === tool.name ? '#1f2937' : 'transparent',
              }}
              onMouseEnter={(e) => {
                if (selectedTool?.name !== tool.name)
                  e.currentTarget.style.background = '#1c2128';
              }}
              onMouseLeave={(e) => {
                if (selectedTool?.name !== tool.name)
                  e.currentTarget.style.background = 'transparent';
              }}
            >
              <div className="text-xs font-medium truncate" style={{ color: '#58a6ff' }}>
                {tool.name}
              </div>
              {tool.description && (
                <div
                  className="text-xs mt-0.5 overflow-hidden"
                  style={{
                    color: '#8b949e',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                  }}
                >
                  {tool.description}
                </div>
              )}
            </div>
          ))}

          {!toolsLoading && !toolsError && tools.length === 0 && isRunning && (
            <div className="p-3 text-xs text-center" style={{ color: '#8b949e' }}>
              No tools found
            </div>
          )}
        </div>
      </div>

      {/* Tool form + result panel */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {showConfig ? (
          <ServerConfig
            serverInfo={serverInfo}
            onClose={() => setShowConfig(false)}
            onSaved={() => { onRefresh?.(); }}
          />
        ) : !selectedTool ? (
          <div className="flex-1 flex items-center justify-center" style={{ color: '#8b949e' }}>
            <p className="text-sm">Select a tool to configure and run</p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4">
            {/* Tool header */}
            <div className="mb-4">
              <h2 className="text-base font-semibold" style={{ color: '#58a6ff' }}>
                {selectedTool.name}
              </h2>
              <p className="text-xs mt-0.5" style={{ color: '#484f58' }}>
                on <span style={{ color: '#3fb950' }}>{selectedServer}</span>
              </p>
              {(() => {
                const h = getToolHints(selectedTool.name);
                return h?.description ? (
                  <div
                    className="mt-2 px-3 py-2 rounded text-xs leading-relaxed"
                    style={{ background: 'rgba(88,166,255,0.06)', color: '#c9d1d9', borderLeft: '3px solid #58a6ff' }}
                  >
                    {h.description}
                  </div>
                ) : selectedTool.description ? (
                  <p className="text-xs mt-1" style={{ color: '#8b949e' }}>
                    {selectedTool.description}
                  </p>
                ) : null;
              })()}
            </div>

            <ToolForm
              key={selectedTool.name}
              tool={selectedTool}
              onSubmit={handleRunTool}
              loading={runLoading}
            />

            <ResultViewer result={result} error={resultError} />
          </div>
        )}
      </div>
    </div>
  );
}
