import React, { useState, useEffect, useCallback } from 'react';
import { listServices, getAdminStats } from './lib/api.js';
import Marketplace from './components/Marketplace.jsx';
import ServerDetail from './components/ServerDetail.jsx';
import ServerList from './components/ServerList.jsx';
import MultiMode from './components/MultiMode.jsx';
import PromptMode from './components/PromptMode.jsx';
import AgentChat from './components/AgentChat.jsx';
import Settings from './components/Settings.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';

const MODES = [
  { id: 'manual', label: 'Catalog' },
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
    } catch {}
  }, []);

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

  function goHome() {
    setMode('manual');
    setSelectedServer(null);
  }

  const runningCount = servers.filter((s) => s.health_ok).length;

  return (
    <div className="app-shell flex flex-col h-screen overflow-hidden">
      {/* Top bar */}
      <header className="app-header">
        <div className="app-header__brand">
          <button
            type="button"
            className="app-header__logo-btn"
            onClick={goHome}
            title="Back to catalog search"
            aria-label="Back to catalog search"
          >
            <img
              src="/images/logo.svg"
              alt=""
              style={{ height: 28, width: 'auto' }}
            />
            <div>
              <span className="app-header__title">MCP Farm</span>
              <span className="app-header__stats">
                <span className="app-header__stats-live">{runningCount}</span>/{servers.length} running
              </span>
            </div>
          </button>
          {serversError && (
            <span className="app-header__error">{serversError}</span>
          )}
        </div>

        <div className="app-header__controls">
          <nav className="app-nav">
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => { setMode(m.id); if (m.id === 'manual') setSelectedServer(null); }}
                className={`app-nav__btn${mode === m.id ? ' app-nav__btn--active' : ''}`}
              >
                {m.label}
              </button>
            ))}
          </nav>
          <ThemeToggle />
          <button
            onClick={() => setShowSettings(true)}
            title="Settings"
            className="app-header__settings-btn"
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* ServerList sidebar — only for multi and prompt modes */}
        {(mode === 'multi' || mode === 'prompt') && (
          <div className="w-56 flex-shrink-0 flex flex-col overflow-hidden">
            <ServerList
              servers={servers}
              loading={serversLoading}
              selectedServer={null}
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
          {mode === 'manual' && !selectedServer && (
            <Marketplace
              servers={servers}
              onSelectServer={handleSelectServer}
              onRefresh={loadServers}
            />
          )}
          {mode === 'manual' && selectedServer && (
            <ServerDetail
              serverName={selectedServer}
              servers={servers}
              onBack={() => setSelectedServer(null)}
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

      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}
