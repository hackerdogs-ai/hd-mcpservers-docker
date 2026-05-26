import React, { useState, useEffect, useCallback } from 'react';
import { listServices, getAdminStats } from './lib/api.js';
import ServerList from './components/ServerList.jsx';
import ManualMode from './components/ManualMode.jsx';
import MultiMode from './components/MultiMode.jsx';
import PromptMode from './components/PromptMode.jsx';
import AgentChat from './components/AgentChat.jsx';
import Settings from './components/Settings.jsx';

const MODES = [
  { id: 'manual', label: 'Manual' },
  { id: 'multi', label: 'Multi-select' },
  { id: 'prompt', label: 'Prompt' },
  { id: 'agent', label: '✦ Nova' },
];

export default function App() {
  const [mode, setMode] = useState('manual');
  const [servers, setServers] = useState([]);
  const [serversLoading, setServersLoading] = useState(false);
  const [serversError, setServersError] = useState(null);
  const [stats, setStats] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);
  const [multiSelected, setMultiSelected] = useState(new Set());

  const loadServers = useCallback(async () => {
    setServersLoading(true);
    setServersError(null);
    try {
      const data = await listServices();
      // Normalize: accept array or object with servers key
      const arr = Array.isArray(data)
        ? data
        : Array.isArray(data?.servers)
        ? data.servers
        : Array.isArray(data?.services)
        ? data.services
        : Object.entries(data || {}).map(([name, info]) =>
            typeof info === 'object' ? { name, ...info } : { name, status: info }
          );
      setServers(arr);
      return arr;
    } catch (err) {
      setServersError(err.message);
    } finally {
      setServersLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const s = await getAdminStats();
      setStats(s);
    } catch {
      // Stats are optional, admin-only
    }
  }, []);

  // Sync credentials from server on every load — ensures admin secret stays current after rebuilds
  useEffect(() => {
    fetch('/ui-config')
      .then((r) => r.json())
      .then((cfg) => {
        if (cfg.api_key) localStorage.setItem('hd_api_key', cfg.api_key);
        if (cfg.base_url !== undefined) localStorage.setItem('hd_base_url', cfg.base_url);
        if (cfg.admin_secret) localStorage.setItem('hd_admin_secret', cfg.admin_secret);
        loadServers();
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadServers();
    loadStats();
    // Poll every 30 seconds
    const interval = setInterval(() => {
      loadServers();
      loadStats();
    }, 30000);
    return () => clearInterval(interval);
  }, [loadServers, loadStats]);

  function handleToggleMulti(name) {
    setMultiSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  function handleSelectServer(name) {
    if (mode === 'multi') {
      handleToggleMulti(name);
    } else {
      setSelectedServer(name);
    }
  }

  const runningCount = servers.filter((s) => (s.status || '').toLowerCase() === 'running').length;

  return (
    <div
      className="flex flex-col h-screen overflow-hidden"
      style={{ background: '#0d1117', color: '#e6edf3' }}
    >
      {/* ── Top bar ── */}
      <header
        className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b"
        style={{ background: '#161b22', borderColor: '#30363d', minHeight: 48 }}
      >
        {/* Logo + title */}
        <div className="flex items-center gap-3">
          <img
            src="https://hackerdogs.ai/images/logo.svg"
            alt="Hackerdogs"
            style={{ height: 28, width: 'auto' }}
          />
          <div>
            <span className="font-semibold text-sm" style={{ color: '#e6edf3' }}>
              MCP Farm
            </span>
            {stats ? (
              <span className="ml-2 text-xs" style={{ color: '#8b949e' }}>
                {stats.healthy_servers ?? runningCount}/{stats.total_servers ?? servers.length} healthy
              </span>
            ) : (
              <span className="ml-2 text-xs" style={{ color: '#8b949e' }}>
                {runningCount}/{servers.length} running
              </span>
            )}
          </div>
          {serversError && (
            <span className="text-xs px-2 py-0.5 rounded" style={{ background: 'rgba(248,81,73,0.15)', color: '#f85149' }}>
              {serversError}
            </span>
          )}
        </div>

        {/* Mode tabs + settings */}
        <div className="flex items-center gap-3">
          <nav className="flex rounded-lg overflow-hidden border" style={{ borderColor: '#30363d' }}>
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className="px-4 py-1.5 text-sm font-medium transition-colors"
                style={{
                  background: mode === m.id ? '#3fb950' : 'transparent',
                  color: mode === m.id ? '#0d1117' : '#8b949e',
                  borderRight: '1px solid #30363d',
                }}
              >
                {m.label}
              </button>
            ))}
          </nav>

          <button
            onClick={() => setShowSettings(true)}
            title="Settings"
            className="p-1.5 rounded transition-colors text-lg"
            style={{ color: '#8b949e' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#e6edf3')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#8b949e')}
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* ── Main layout ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar — hidden in Nova/agent mode */}
        {mode !== 'agent' && (
          <div className="w-56 flex-shrink-0 flex flex-col overflow-hidden">
            <ServerList
              servers={servers}
              loading={serversLoading}
              selectedServer={mode === 'manual' ? selectedServer : null}
              onSelectServer={handleSelectServer}
              multiSelected={mode === 'multi' ? multiSelected : new Set()}
              onToggleMulti={handleToggleMulti}
              mode={mode}
              onRefresh={loadServers}
            />
          </div>
        )}

        {/* Main panel */}
        <main className="flex flex-1 overflow-hidden">
          {mode === 'manual' && (
            <ManualMode
              selectedServer={selectedServer}
              servers={servers}
              onRefresh={loadServers}
            />
          )}
          {mode === 'multi' && (
            <MultiMode
              servers={servers}
              multiSelected={multiSelected}
              onToggleMulti={handleToggleMulti}
            />
          )}
          {mode === 'prompt' && (
            <PromptMode servers={servers} />
          )}
          {mode === 'agent' && (
            <AgentChat servers={servers} />
          )}
        </main>
      </div>

      {/* Settings modal */}
      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}
