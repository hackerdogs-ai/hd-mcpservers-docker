import React, { useState, useMemo, useCallback } from 'react';
import { ALL_CATEGORIES, getCategoryInfo, getStatusInfo, isServerRunning, generateServerIcon, getServerDescription, serverRequiresKey, getRequiredEnvKeys } from '../lib/categories.js';
import { startServer, stopServer, enableServer, disableServer } from '../lib/api.js';
import { mcpClient } from '../lib/mcp.js';
import AddServerDialog from './AddServerDialog.jsx';

/* ── Confirmation dialog (hd-dialog pattern) ──────────────────────────── */

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

/* ── Shared inline action buttons ─────────────────────────────────────── */

function ServerActions({ server, onAction, actionLoading, className }) {
  const isRunning = isServerRunning(server);
  const isDisabled = (server.status || '').toLowerCase() === 'disabled';
  const thisLoading = actionLoading === server.name;

  function act(e, action) {
    e.stopPropagation();
    onAction(server, action);
  }

  return (
    <span className={className} onClick={e => e.stopPropagation()}>
      {isDisabled ? (
        <button className="mkt-card-btn mkt-card-btn--start" onClick={e => act(e, 'enable')} disabled={thisLoading} title="Enable">
          ✓
        </button>
      ) : isRunning ? (
        <>
          <button className="mkt-card-btn mkt-card-btn--stop" onClick={e => act(e, 'stop')} disabled={thisLoading} title="Stop">
            ■
          </button>
          <button className="mkt-card-btn mkt-card-btn--disable" onClick={e => act(e, 'disable')} disabled={thisLoading} title="Disable">
            ⊘
          </button>
        </>
      ) : (
        <>
          <button className="mkt-card-btn mkt-card-btn--start" onClick={e => act(e, 'start')} disabled={thisLoading} title="Start">
            ▶
          </button>
          <button className="mkt-card-btn mkt-card-btn--disable" onClick={e => act(e, 'disable')} disabled={thisLoading} title="Disable">
            ⊘
          </button>
        </>
      )}
    </span>
  );
}

/* ── View mode toggle (list / tile) ───────────────────────────────────── */

function ViewToggle({ viewMode, onChange }) {
  return (
    <div className="mkt-view-toggle" role="group" aria-label="Results view">
      <button
        type="button"
        className={`mkt-view-btn ${viewMode === 'list' ? 'mkt-view-btn--active' : ''}`}
        onClick={() => onChange('list')}
        title="List view"
        aria-label="List view"
        aria-pressed={viewMode === 'list'}
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <line x1="2" y1="4" x2="14" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          <line x1="2" y1="12" x2="14" y2="12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </button>
      <button
        type="button"
        className={`mkt-view-btn ${viewMode === 'tile' ? 'mkt-view-btn--active' : ''}`}
        onClick={() => onChange('tile')}
        title="Tile view"
        aria-label="Tile view"
        aria-pressed={viewMode === 'tile'}
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
          <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
          <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
          <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
      </button>
    </div>
  );
}

const ACTION_META = {
  start:   { title: 'Start Server',   verb: 'start',   confirmClass: 'hd-dialog-btn--green' },
  stop:    { title: 'Stop Server',    verb: 'stop',    confirmClass: 'hd-dialog-btn--red' },
  enable:  { title: 'Enable Server',  verb: 'enable',  confirmClass: 'hd-dialog-btn--green' },
  disable: { title: 'Disable Server', verb: 'disable', confirmClass: 'hd-dialog-btn--amber' },
};

const LIST_SORT_COLUMNS = [
  { id: 'name', label: 'Name' },
  { id: 'description', label: 'Description' },
  { id: 'category', label: 'Category' },
  { id: 'status', label: 'Status' },
  { id: 'key', label: 'Key Required' },
  { id: 'port', label: 'Port' },
];

function KeyIcon({ size = 14, className }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="5.5" cy="6.5" r="3" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M8 6.5h5.5M11.5 6.5v2M13.5 6.5v2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function getStatusRank(server) {
  const s = (server.status || '').toLowerCase();
  if (s === 'disabled') return 0;
  if (isServerRunning(server)) return 3;
  if (s === 'running') return 2;
  return 1;
}

function compareServers(a, b, sortBy, sortDir) {
  let cmp = 0;
  switch (sortBy) {
    case 'name':
      cmp = a.name.localeCompare(b.name);
      break;
    case 'description':
      cmp = getServerDescription(a.name).localeCompare(getServerDescription(b.name));
      break;
    case 'category':
      cmp = getCategoryInfo(a.category).label.localeCompare(getCategoryInfo(b.category).label);
      break;
    case 'status':
      cmp = getStatusRank(a) - getStatusRank(b);
      if (cmp === 0) cmp = getStatusInfo(a).label.localeCompare(getStatusInfo(b).label);
      break;
    case 'port':
      cmp = (a.port || 0) - (b.port || 0);
      break;
    case 'key':
      cmp = Number(serverRequiresKey(a)) - Number(serverRequiresKey(b));
      break;
    default:
      cmp = a.name.localeCompare(b.name);
  }
  return sortDir === 'desc' ? -cmp : cmp;
}

function defaultSortDir(column) {
  return column === 'status' || column === 'port' ? 'desc' : 'asc';
}

/* ── List column header ───────────────────────────────────────────────── */

function ListSortHeader({ column, label, sortBy, sortDir, onSort }) {
  const active = sortBy === column;
  return (
    <button
      type="button"
      className={`mkt-list-col-head mkt-list-col-head--${column} ${active ? 'mkt-list-col-head--active' : ''}`}
      onClick={() => onSort(column)}
      aria-sort={active ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <span className="mkt-list-col-head-label">{label}</span>
      <span className="mkt-sort-indicator" aria-hidden="true">
        {active ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}
      </span>
    </button>
  );
}

function ListHeader({ sortBy, sortDir, onSort }) {
  return (
    <div className="mkt-list-head" role="row">
      <span className="mkt-list-col mkt-list-col--icon" aria-hidden="true" />
      {LIST_SORT_COLUMNS.map(col => (
        <ListSortHeader
          key={col.id}
          column={col.id}
          label={col.label}
          sortBy={sortBy}
          sortDir={sortDir}
          onSort={onSort}
        />
      ))}
      <span className="mkt-list-col mkt-list-col--actions">Actions</span>
    </div>
  );
}

/* ── Server list row ──────────────────────────────────────────────────── */

function ServerListRow({ server, onClick, onAction, actionLoading }) {
  const cat = getCategoryInfo(server.category);
  const status = getStatusInfo(server);
  const desc = getServerDescription(server.name);
  const iconSvg = generateServerIcon(server.name, server.category, 28);
  const needsKey = serverRequiresKey(server);
  const keyTitle = needsKey
    ? `Requires key: ${getRequiredEnvKeys(server).join(', ')}`
    : undefined;

  return (
    <button
      onClick={() => onClick(server.name)}
      className="mkt-list-row"
      style={{ '--card-accent': cat.color }}
      role="row"
    >
      <span
        className="mkt-list-col mkt-list-col--icon"
        dangerouslySetInnerHTML={{ __html: iconSvg }}
      />
      <span className="mkt-list-col mkt-list-col--name">{server.name.replace(/-mcp$/, '')}</span>
      <span className="mkt-list-col mkt-list-col--desc">{desc}</span>
      <span className="mkt-list-col mkt-list-col--category">
        <span className="mkt-chip" style={{ color: cat.color, background: cat.bg, borderColor: cat.border }}>
          {cat.label}
        </span>
      </span>
      <span className="mkt-list-col mkt-list-col--status">
        <span className="mkt-list-status-dot" style={{ background: status.dot }} />
        <span style={{ color: status.color }}>{status.label}</span>
      </span>
      <span className="mkt-list-col mkt-list-col--key" title={keyTitle}>
        {needsKey && <KeyIcon size={14} className="mkt-key-icon" />}
      </span>
      <span className="mkt-list-col mkt-list-col--port">{server.port ?? '—'}</span>
      <ServerActions
        server={server}
        onAction={onAction}
        actionLoading={actionLoading}
        className="mkt-list-col mkt-list-col--actions mkt-list-row-actions"
      />
    </button>
  );
}

/* ── Server card with inline action buttons ───────────────────────────── */

function ServerCard({ server, onClick, onAction, actionLoading }) {
  const cat = getCategoryInfo(server.category);
  const status = getStatusInfo(server);
  const desc = getServerDescription(server.name);
  const iconSvg = generateServerIcon(server.name, server.category, 40);
  const needsKey = serverRequiresKey(server);
  const keyTitle = needsKey
    ? `Requires key: ${getRequiredEnvKeys(server).join(', ')}`
    : undefined;

  return (
    <button
      onClick={() => onClick(server.name)}
      className="mkt-card"
      style={{ '--card-accent': cat.color }}
    >
      <div className="mkt-card-head">
        <span
          className="mkt-card-icon"
          dangerouslySetInnerHTML={{ __html: iconSvg }}
        />
        <span className="mkt-card-head-badges">
          {needsKey && (
            <span className="mkt-key-badge" title={keyTitle}>
              <KeyIcon size={13} className="mkt-key-icon" />
            </span>
          )}
          <span
            className="mkt-card-dot"
            title={status.label}
            style={{ background: status.dot }}
          />
        </span>
      </div>
      <div className="mkt-card-name">{server.name.replace(/-mcp$/, '')}</div>
      <div className="mkt-card-desc">{desc}</div>
      <div className="mkt-card-foot">
        <span className="mkt-chip" style={{ color: cat.color, background: cat.bg, borderColor: cat.border }}>
          {cat.label}
        </span>
        <span className="mkt-card-spacer" />
        <ServerActions
          server={server}
          onAction={onAction}
          actionLoading={actionLoading}
          className="mkt-card-actions"
        />
      </div>
    </button>
  );
}

const STATUS_FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'running', label: 'Running' },
  { id: 'stopped', label: 'Stopped' },
  { id: 'disabled', label: 'Disabled' },
];

export default function Marketplace({ servers, loading, onSelectServer, onRefresh }) {
  const [search, setSearch] = useState('');
  const [selectedCats, setSelectedCats] = useState(new Set());
  const [statusFilter, setStatusFilter] = useState('all');
  const [requiresKeyFilter, setRequiresKeyFilter] = useState(false);
  const [sortBy, setSortBy] = useState('name');
  const [sortDir, setSortDir] = useState('asc');
  const [viewMode, setViewMode] = useState('list');
  const [confirm, setConfirm] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [showAddServer, setShowAddServer] = useState(false);

  const categoryCounts = useMemo(() => {
    const counts = {};
    (servers || []).forEach(s => {
      const c = s.category || 'misc';
      counts[c] = (counts[c] || 0) + 1;
    });
    return counts;
  }, [servers]);

  const runningCount = useMemo(() =>
    (servers || []).filter(s => isServerRunning(s)).length
  , [servers]);

  const disabledCount = useMemo(() =>
    (servers || []).filter(s => (s.status || '').toLowerCase() === 'disabled').length
  , [servers]);

  const requiresKeyCount = useMemo(() =>
    (servers || []).filter(s => serverRequiresKey(s)).length
  , [servers]);

  const filtered = useMemo(() => {
    if (!Array.isArray(servers)) return [];
    return servers
      .filter(s => {
        const name = (s.name || '').toLowerCase();
        const matchSearch = !search || name.includes(search.toLowerCase());
        const cat = s.category || 'misc';
        const matchCat = selectedCats.size === 0 || selectedCats.has(cat);
        const sStatus = (s.status || '').toLowerCase();
        const matchStatus =
          statusFilter === 'all' ||
          (statusFilter === 'running' && isServerRunning(s)) ||
          (statusFilter === 'stopped' && !isServerRunning(s) && sStatus !== 'disabled') ||
          (statusFilter === 'disabled' && sStatus === 'disabled');
        const matchKey = !requiresKeyFilter || serverRequiresKey(s);
        return matchSearch && matchCat && matchStatus && matchKey;
      })
      .sort((a, b) => compareServers(a, b, sortBy, sortDir));
  }, [servers, search, selectedCats, statusFilter, requiresKeyFilter, sortBy, sortDir]);

  function handleListSort(column) {
    if (sortBy === column) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(column);
      setSortDir(defaultSortDir(column));
    }
  }

  function toggleCat(cat) {
    setSelectedCats(prev => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  }

  const handleCardAction = useCallback((server, action) => {
    const meta = ACTION_META[action];
    const displayName = server.name.replace(/-mcp$/, '');
    setConfirm({
      server,
      action,
      title: meta.title,
      message: `Are you sure you want to ${meta.verb} "${displayName}"?`,
      confirmLabel: meta.title,
      confirmClass: meta.confirmClass,
    });
  }, []);

  const executeAction = useCallback(async () => {
    if (!confirm) return;
    const { server, action } = confirm;
    setActionLoading(server.name);
    try {
      if (action === 'start') await startServer(server.name);
      else if (action === 'stop') {
        await mcpClient.terminateSession(server.name);
        await stopServer(server.name);
      }
      else if (action === 'enable') await enableServer(server.name);
      else if (action === 'disable') await disableServer(server.name);
      onRefresh?.();
    } catch (err) {
      console.error(`${action} failed:`, err);
    } finally {
      setActionLoading(null);
      setConfirm(null);
    }
  }, [confirm, onRefresh]);

  return (
    <div className="mkt-shell">
      {/* Facet sidebar */}
      <aside className="mkt-sidebar">
        {loading && servers.length === 0 && (
          <div className="mkt-sidebar-loading">
            <span className="spinner" style={{ width: 14, height: 14 }} />
            <span>Loading filters...</span>
          </div>
        )}
        <div className="mkt-sidebar-section">
          <div className="mkt-sidebar-title">Status</div>
          {STATUS_FILTERS.map(f => (
            <label
              key={f.id}
              className={`mkt-facet-btn ${statusFilter === f.id ? 'mkt-facet-btn--active' : ''}`}
            >
              <input
                type="checkbox"
                className="mkt-facet-checkbox"
                checked={statusFilter === f.id}
                onChange={() => setStatusFilter(statusFilter === f.id ? 'all' : f.id)}
              />
              <span className="mkt-facet-label">{f.label}</span>
              <span className="mkt-facet-count">
                {f.id === 'all' ? (servers || []).length :
                 f.id === 'running' ? runningCount :
                 f.id === 'disabled' ? disabledCount :
                 (servers || []).length - runningCount - disabledCount}
              </span>
            </label>
          ))}
        </div>

        <div className="mkt-sidebar-section">
          <div className="mkt-sidebar-title">Access</div>
          <label
            className={`mkt-facet-btn ${requiresKeyFilter ? 'mkt-facet-btn--active' : ''}`}
          >
            <input
              type="checkbox"
              className="mkt-facet-checkbox"
              checked={requiresKeyFilter}
              onChange={() => setRequiresKeyFilter(v => !v)}
            />
            <span className="mkt-facet-label">Requires Key</span>
            <span className="mkt-facet-count">{requiresKeyCount}</span>
          </label>
        </div>

        <div className="mkt-sidebar-section">
          <div className="mkt-sidebar-title">Categories</div>
          {ALL_CATEGORIES.filter(c => categoryCounts[c]).map(cat => {
            const info = getCategoryInfo(cat);
            const active = selectedCats.has(cat);
            return (
              <label
                key={cat}
                className={`mkt-facet-btn ${active ? 'mkt-facet-btn--active' : ''}`}
                style={active ? { background: info.bg } : {}}
              >
                <input
                  type="checkbox"
                  className="mkt-facet-checkbox"
                  checked={active}
                  onChange={() => toggleCat(cat)}
                  style={{ accentColor: info.color }}
                />
                <span className="mkt-facet-label">
                  <span
                    className="mkt-facet-dot"
                    style={{ background: info.color }}
                  />
                  {' '}{info.label}
                </span>
                <span className="mkt-facet-count">{categoryCounts[cat]}</span>
              </label>
            );
          })}
        </div>
      </aside>

      {/* Main content */}
      <div className="mkt-main">
        {/* Toolbar: search + sort dropdown + info */}
        <div className="mkt-toolbar">
          <div className="mkt-search-wrap">
            <svg className="mkt-search-icon" width="14" height="14" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5"/>
              <line x1="11" y1="11" x2="14.5" y2="14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={loading && servers.length === 0 ? 'Loading servers...' : `Search ${servers.length} MCP servers...`}
              className="mkt-search"
            />
            {search && (
              <button onClick={() => setSearch('')} className="mkt-search-clear">×</button>
            )}
          </div>
          {viewMode === 'tile' && (
            <select
              value={sortBy}
              onChange={e => {
                setSortBy(e.target.value);
                setSortDir(defaultSortDir(e.target.value));
              }}
              className="mkt-select"
            >
              <option value="name">Sort: Name</option>
              <option value="description">Sort: Description</option>
              <option value="category">Sort: Category</option>
              <option value="status">Sort: Status</option>
              <option value="port">Sort: Port</option>
            </select>
          )}
          <div className="mkt-toolbar-info">
            {loading && servers.length === 0 ? (
              <span style={{ color: 'var(--text-dim)' }}>
                <span className="spinner" style={{ width: 10, height: 10, marginRight: 6, verticalAlign: 'middle' }} />
                Loading...
              </span>
            ) : (
              <>
                <span style={{ color: 'var(--hd-primary)' }}>{runningCount}</span>
                <span style={{ color: 'var(--text-dim)' }}> running</span>
                <span style={{ color: 'var(--text-muted)' }}> · </span>
                <span style={{ color: 'var(--text-dim)' }}>{filtered.length} shown</span>
                {loading && <span className="spinner" style={{ width: 10, height: 10, marginLeft: 8, verticalAlign: 'middle' }} />}
              </>
            )}
          </div>
          <button
            type="button"
            className="mkt-add-btn"
            onClick={() => setShowAddServer(true)}
            title="Add MCP Server"
          >
            + Add Server
          </button>
          <ViewToggle viewMode={viewMode} onChange={setViewMode} />
        </div>

        {/* Active filter chips */}
        {(selectedCats.size > 0 || statusFilter !== 'all' || requiresKeyFilter) && (
          <div className="mkt-active-filters">
            {statusFilter !== 'all' && (
              <span className="mkt-filter-chip" onClick={() => setStatusFilter('all')}>
                {statusFilter} ×
              </span>
            )}
            {requiresKeyFilter && (
              <span className="mkt-filter-chip" onClick={() => setRequiresKeyFilter(false)}>
                Requires Key ×
              </span>
            )}
            {[...selectedCats].map(cat => (
              <span
                key={cat}
                className="mkt-filter-chip"
                style={{ color: getCategoryInfo(cat).color, borderColor: getCategoryInfo(cat).border }}
                onClick={() => toggleCat(cat)}
              >
                {getCategoryInfo(cat).label} ×
              </span>
            ))}
            <button
              className="mkt-filter-clear"
              onClick={() => { setSelectedCats(new Set()); setStatusFilter('all'); setRequiresKeyFilter(false); }}
            >
              Clear all
            </button>
          </div>
        )}

        {/* Results: list or tile grid */}
        {viewMode === 'list' ? (
          <div className="mkt-list" role="table">
            <ListHeader sortBy={sortBy} sortDir={sortDir} onSort={handleListSort} />
            {filtered.map(server => (
              <ServerListRow
                key={server.name}
                server={server}
                onClick={onSelectServer}
                onAction={handleCardAction}
                actionLoading={actionLoading}
              />
            ))}
          </div>
        ) : (
          <div className="mkt-grid">
            {filtered.map(server => (
              <ServerCard
                key={server.name}
                server={server}
                onClick={onSelectServer}
                onAction={handleCardAction}
                actionLoading={actionLoading}
              />
            ))}
          </div>
        )}

        {filtered.length === 0 && (
          <div className="mkt-empty">
            {loading && servers.length === 0 ? (
              <>
                <span className="spinner" style={{ width: 24, height: 24, marginBottom: 12 }} />
                <div>Loading MCP servers...</div>
              </>
            ) : (
              <>
                <div style={{ fontSize: 32, marginBottom: 8 }}>🔍</div>
                <div>No servers match your filters</div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Confirmation dialog */}
      <ConfirmDialog
        open={!!confirm}
        title={confirm?.title}
        message={confirm?.message}
        confirmLabel={confirm?.confirmLabel}
        confirmClass={confirm?.confirmClass}
        onConfirm={executeAction}
        onCancel={() => setConfirm(null)}
        loading={!!actionLoading}
      />

      {/* Add Server dialog */}
      {showAddServer && (
        <AddServerDialog
          onClose={() => setShowAddServer(false)}
          onRefresh={onRefresh}
        />
      )}
    </div>
  );
}
