import React, { useState, useEffect, useCallback } from 'react';
import {
  listServices,
  getAdminStats,
  getAdminSecret,
  fetchUiConfig,
  saveSettings,
  verifyAdminSecret,
} from './lib/api.js';
import { isServerRunning } from './lib/categories.js';
import { useTheme } from './lib/theme.js';
import Marketplace from './components/Marketplace.jsx';
import ServerDetail from './components/ServerDetail.jsx';
import ServerList from './components/ServerList.jsx';
// Nova tab (HeyGen avatar + agent) is disabled on main — feature is incomplete.
// import AgentChat from './components/AgentChat.jsx';
import ChatMode from './components/ChatMode.jsx';
import Settings from './components/Settings.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';
import OnboardingWizard from './components/OnboardingWizard.jsx';
import Icon from './components/Icon.jsx';

const MODES = [
  { id: 'manual', label: 'Catalog' },
  { id: 'chat', label: 'Chat' },
  // Nova tab disabled on main — feature is incomplete.
  // { id: 'agent', label: 'Nova' },
];

export default function App() {
  const theme = useTheme();
  const [mode, setMode] = useState('manual');
  const [servers, setServers] = useState([]);
  const [serversLoading, setServersLoading] = useState(true);
  const [serversError, setServersError] = useState(null);
  const [stats, setStats] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);
  const [setupReady, setSetupReady] = useState(false);
  const [setupChecking, setSetupChecking] = useState(true);

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
    let cancelled = false;
    async function checkSetup() {
      setSetupChecking(true);
      try {
        const cfg = await fetchUiConfig();
        if (cfg.base_url !== undefined) saveSettings({ baseUrl: cfg.base_url });
        if (cfg.api_key) saveSettings({ apiKey: cfg.api_key });
        if (cfg.admin_secret) saveSettings({ adminSecret: cfg.admin_secret });

        // Block only until an admin secret exists. API keys are configured later
        // in Settings — not part of first-run.
        if (cfg.admin_configured) {
          if (!cancelled) {
            setSetupReady(true);
            localStorage.setItem('hd_setup_complete', '1');
          }
          return;
        }

        const secret = getAdminSecret();
        if (secret) {
          try {
            await verifyAdminSecret(secret);
            if (!cancelled) {
              setSetupReady(true);
              localStorage.setItem('hd_setup_complete', '1');
            }
            return;
          } catch {
            /* show wizard */
          }
        }
        if (!cancelled) setSetupReady(false);
      } catch {
        if (!cancelled) setSetupReady(!!getAdminSecret());
      } finally {
        if (!cancelled) setSetupChecking(false);
      }
    }
    checkSetup();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!setupReady) return undefined;
    loadServers();
    loadStats();
    const interval = setInterval(() => {
      loadServers();
      loadStats();
    }, 30000);
    return () => clearInterval(interval);
  }, [setupReady, loadServers, loadStats]);

  function handleSetupComplete() {
    setSetupReady(true);
  }

  function handleSelectServer(name) {
    setSelectedServer(name);
  }

  function goHome() {
    setMode('manual');
    setSelectedServer(null);
  }

  const runningCount = servers.filter((s) => isServerRunning(s)).length;

  if (setupChecking) {
    return (
      <div className="app-shell flex flex-col h-screen overflow-hidden items-center justify-center">
        <p className="hd-label-hint">Checking farm credentials…</p>
      </div>
    );
  }

  if (!setupReady) {
    return <OnboardingWizard onComplete={handleSetupComplete} />;
  }

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
              src={theme === 'light' ? '/favicon.svg' : '/images/logo.svg'}
              alt=""
              style={{ height: 28, width: 'auto' }}
            />
            <div>
              <span className="app-header__title">MCP Farm</span>
              <span className="app-header__stats">
                {serversLoading && servers.length === 0 ? (
                  <>
                    <span className="spinner" style={{ width: 10, height: 10, marginRight: 4, verticalAlign: 'middle' }} />
                    loading...
                  </>
                ) : (
                  <>
                    <span className="app-header__stats-live">{runningCount}</span>/{servers.length} running
                  </>
                )}
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
            aria-label="Settings"
          >
            <Icon name="settings" size={20} />
          </button>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {mode === 'prompt' && (
          <div className="w-56 flex-shrink-0 flex flex-col overflow-hidden">
            <ServerList
              servers={servers}
              loading={serversLoading}
              selectedServer={null}
              onSelectServer={handleSelectServer}
              onRefresh={loadServers}
            />
          </div>
        )}

        <main className="flex flex-1 overflow-hidden">
          {mode === 'manual' && !selectedServer && (
            <Marketplace
              servers={servers}
              loading={serversLoading}
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
          {mode === 'chat' && (
            <ChatMode servers={servers} />
          )}
          {/* Nova tab disabled on main — feature is incomplete.
          {mode === 'agent' && (
            <AgentChat servers={servers} />
          )}
          */}
        </main>
      </div>

      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}
