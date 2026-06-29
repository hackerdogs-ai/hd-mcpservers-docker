import React, { useState, useMemo } from 'react';
import { mcpClient } from '../lib/mcp.js';
import { startServer } from '../lib/api.js';

// ─── ToolForm (simplified version for MultiMode) ──────────────────────────────

function ToolForm({ tool, onSubmit, loading }) {
  const schema = tool.inputSchema || { type: 'object', properties: {}, required: [] };
  const properties = schema.properties || {};
  const required = schema.required || [];

  const [values, setValues] = useState(() => {
    const init = {};
    Object.entries(properties).forEach(([key, prop]) => {
      init[key] = prop.type === 'boolean' ? false : '';
    });
    return init;
  });

  function setValue(key, val) {
    setValues((prev) => ({ ...prev, [key]: val }));
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

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {propEntries.length === 0 && (
        <p className="text-xs hd-text-dim">No parameters required.</p>
      )}
      {propEntries.map(([key, prop]) => {
        const isRequired = required.includes(key);
        const labelEl = (
          <label className="hd-label">
            {key}{isRequired && <span className="hd-text-required"> *</span>}
            {prop.description && (
              <span className="hd-label-hint"> — {prop.description}</span>
            )}
          </label>
        );
        if (prop.enum) {
          return (
            <div key={key}>
              {labelEl}
              <select
                value={values[key]}
                onChange={(e) => setValue(key, e.target.value)}
                className="hd-select text-xs"
              >
                <option value="">— select —</option>
                {prop.enum.map((opt) => <option key={opt} value={opt}>{String(opt)}</option>)}
              </select>
            </div>
          );
        }
        if (prop.type === 'boolean') {
          return (
            <div key={key} className="flex items-center gap-2">
              <input type="checkbox" id={`mf-${key}`} checked={values[key]}
                onChange={(e) => setValue(key, e.target.checked)} />
              <label htmlFor={`mf-${key}`} className="text-xs hd-text-secondary">
                {key}{isRequired && <span className="hd-text-required"> *</span>}
              </label>
            </div>
          );
        }
        const inputType = (prop.type === 'integer' || prop.type === 'number') ? 'number' : 'text';
        return (
          <div key={key}>
            {labelEl}
            <input
              type={inputType}
              value={values[key]}
              onChange={(e) => setValue(key, e.target.value)}
              placeholder={prop.default !== undefined ? String(prop.default) : ''}
              className="hd-input text-xs"
            />
          </div>
        );
      })}
      <button type="submit" disabled={loading} className="hd-btn hd-btn--primary mt-2">
        {loading ? (
          <span className="flex items-center gap-2">
            <span className="spinner" style={{ width: 14, height: 14 }} /> Running...
          </span>
        ) : 'Run Tool'}
      </button>
    </form>
  );
}

// ─── ResultViewer ─────────────────────────────────────────────────────────────

function ResultViewer({ result, error }) {
  const [collapsed, setCollapsed] = useState(false);
  if (!result && !error) return null;

  function formatResult(r) {
    if (!r) return '';
    if (typeof r === 'string') return r;
    if (r.content && Array.isArray(r.content)) {
      return r.content.map((c) => (c.type === 'text' ? c.text : JSON.stringify(c, null, 2))).join('\n');
    }
    return JSON.stringify(r, null, 2);
  }

  return (
    <div className={`hd-result${error ? ' hd-result--error' : ''}`}>
      <div
        className="hd-result__head"
        onClick={() => setCollapsed((c) => !c)}
      >
        <span className={error ? 'hd-result__head--err' : 'hd-result__head--ok'}>
          {error ? '✗ Error' : '✓ Result'}
        </span>
        <span className="hd-result__toggle">{collapsed ? '▶' : '▼'}</span>
      </div>
      {!collapsed && (
        <pre className={`hd-result__body result-pre${error ? ' hd-result__body--error' : ''}`}>
          {error ? String(error) : formatResult(result)}
        </pre>
      )}
    </div>
  );
}

// ─── MultiMode ────────────────────────────────────────────────────────────────

export default function MultiMode({ servers, multiSelected, onToggleMulti }) {
  const [showAll, setShowAll] = useState(false);
  const [loadingTools, setLoadingTools] = useState(false);
  const [aggregatedTools, setAggregatedTools] = useState([]); // [{serverName, tool}]
  const [loadError, setLoadError] = useState(null);
  const [selectedEntry, setSelectedEntry] = useState(null); // {serverName, tool}
  const [runLoading, setRunLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultError, setResultError] = useState(null);
  const [toolFilter, setToolFilter] = useState('');

  const displayedServers = useMemo(() => {
    if (!Array.isArray(servers)) return [];
    if (showAll) return servers;
    return servers.filter((s) => (s.status || '').toLowerCase() === 'running');
  }, [servers, showAll]);

  const selectedCount = multiSelected?.size || 0;

  async function handleLoadTools() {
    if (!multiSelected || multiSelected.size === 0) return;
    setLoadingTools(true);
    setLoadError(null);
    setAggregatedTools([]);
    setSelectedEntry(null);
    setResult(null);
    setResultError(null);

    const results = [];
    const errors = [];

    await Promise.allSettled(
      Array.from(multiSelected).map(async (serverName) => {
        try {
          const tools = await mcpClient.listTools(serverName);
          tools.forEach((tool) => results.push({ serverName, tool }));
        } catch (err) {
          errors.push(`${serverName}: ${err.message}`);
        }
      })
    );

    setAggregatedTools(results);
    if (errors.length > 0) {
      setLoadError(errors.join('\n'));
    }
    setLoadingTools(false);
  }

  async function handleRunTool(args) {
    if (!selectedEntry) return;
    setRunLoading(true);
    setResult(null);
    setResultError(null);
    try {
      const r = await mcpClient.callTool(selectedEntry.serverName, selectedEntry.tool.name, args);
      setResult(r);
    } catch (err) {
      setResultError(err.message);
    } finally {
      setRunLoading(false);
    }
  }

  const filteredTools = useMemo(() => {
    if (!toolFilter) return aggregatedTools;
    const q = toolFilter.toLowerCase();
    return aggregatedTools.filter(
      ({ serverName, tool }) =>
        tool.name.toLowerCase().includes(q) || serverName.toLowerCase().includes(q)
    );
  }, [aggregatedTools, toolFilter]);

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="w-72 flex-shrink-0 flex flex-col hd-border-r hd-sidebar overflow-hidden">
        <div className="hd-border-b">
          <div className="px-3 py-2 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider hd-text-dim">
              Servers ({selectedCount} selected)
            </span>
            <button
              onClick={() => setShowAll((v) => !v)}
              className="hd-btn hd-btn--ghost text-xs px-2 py-0.5"
            >
              {showAll ? 'Running only' : 'Show all'}
            </button>
          </div>

          <div className="overflow-y-auto" style={{ maxHeight: 220 }}>
            {displayedServers.map((s) => {
              const name = s.name || s.id || '';
              const isChecked = multiSelected?.has(name);
              const isRunning = (s.status || '').toLowerCase() === 'running';
              return (
                <label key={name} className="hd-list-item cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isChecked || false}
                    onChange={() => onToggleMulti?.(name)}
                  />
                  <span
                    className="rounded-full flex-shrink-0"
                    style={{
                      width: 6,
                      height: 6,
                      background: isRunning ? 'var(--semantic-success)' : 'var(--semantic-error)',
                    }}
                  />
                  <span className="text-xs truncate flex-1">{name}</span>
                </label>
              );
            })}
          </div>

          <div className="px-3 py-2">
            <button
              onClick={handleLoadTools}
              disabled={selectedCount === 0 || loadingTools}
              className="hd-btn hd-btn--primary w-full text-xs"
            >
              {loadingTools ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="spinner" style={{ width: 12, height: 12 }} /> Loading tools...
                </span>
              ) : (
                `Load Tools (${selectedCount} servers)`
              )}
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          {aggregatedTools.length > 0 && (
            <div className="px-3 py-2 hd-border-b">
              <input
                type="text"
                value={toolFilter}
                onChange={(e) => setToolFilter(e.target.value)}
                placeholder="Filter tools..."
                className="hd-input text-xs"
              />
            </div>
          )}

          {loadError && (
            <div className="px-3 py-2 text-xs hd-text-err">
              Some errors occurred:
              <pre className="mt-1 text-xs hd-text-err" style={{ whiteSpace: 'pre-wrap' }}>{loadError}</pre>
            </div>
          )}

          <div className="flex-1 overflow-y-auto">
            {aggregatedTools.length === 0 && !loadingTools && (
              <div className="p-4 text-center text-xs hd-text-dim">
                {selectedCount === 0
                  ? 'Select servers above, then click Load Tools'
                  : 'Click "Load Tools" to aggregate tools'}
              </div>
            )}

            {filteredTools.map(({ serverName, tool }, idx) => {
              const isSelected =
                selectedEntry?.serverName === serverName && selectedEntry?.tool.name === tool.name;
              return (
                <div
                  key={`${serverName}-${tool.name}-${idx}`}
                  onClick={() => {
                    setSelectedEntry({ serverName, tool });
                    setResult(null);
                    setResultError(null);
                  }}
                  className={`hd-tool-entry ${isSelected ? 'hd-tool-entry--selected' : ''}`}
                >
                  <div className="hd-tool-entry__name">{tool.name}</div>
                  <div className="hd-tool-entry__server">{serverName}</div>
                  {tool.description && (
                    <div className="hd-tool-entry__desc">{tool.description}</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {!selectedEntry ? (
          <div className="flex-1 flex items-center justify-center hd-empty-hint">
            <div className="text-center">
              <div className="text-3xl mb-3">🔧</div>
              <p className="text-sm">
                {aggregatedTools.length === 0
                  ? 'Select servers and load tools to begin'
                  : 'Select a tool from the list'}
              </p>
              {aggregatedTools.length > 0 && (
                <p className="text-xs mt-1 hd-text-muted">
                  {aggregatedTools.length} tools loaded across {selectedCount} servers
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4">
            <div className="mb-4">
              <h2 className="text-base font-semibold hd-link">{selectedEntry.tool.name}</h2>
              <p className="text-xs mt-0.5 hd-text-dim">{selectedEntry.tool.description}</p>
              <p className="text-xs mt-1 hd-text-muted">
                on <span className="hd-text-ok">{selectedEntry.serverName}</span>
              </p>
            </div>

            <ToolForm
              key={`${selectedEntry.serverName}-${selectedEntry.tool.name}`}
              tool={selectedEntry.tool}
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
