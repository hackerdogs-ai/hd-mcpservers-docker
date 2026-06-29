import React, { useState, useMemo } from 'react';
import { startServer, stopServer } from '../lib/api.js';
import { mcpClient } from '../lib/mcp.js';

const CATEGORIES = ['all', 'recon', 'exploit', 'cloud', 'misc'];

function getStatusColor(server) {
  if (!server) return '#8b949e';
  if (server.health_ok) return '#3fb950';
  const s = (server.status || '').toLowerCase();
  if (s === 'running') return '#d29922'; // registered running but not reachable
  return '#f85149';
}

function getStatusTitle(server) {
  if (!server) return 'unknown';
  if (server.health_ok) return 'running';
  const s = (server.status || '').toLowerCase();
  if (s === 'running') return 'not reachable';
  return s || 'stopped';
}

function guessCategory(name) {
  const n = name.toLowerCase();
  if (/aws|azure|gcp|cloud|s3|ec2|iam|k8s|kube|terraform|scoutsuite|prowler|pacu|cloudlist|cloudmapper/.test(n)) return 'cloud';
  if (/nmap|masscan|rustscan|zmap|fping|netdiscover|arp|nbtscan|naabu|port|scan|recon|amass|subfinder|sublist|assetfinder|dnsx|dnsenum|dnsrecon|theharvester|shodan|censys|spiderfoot|nuclei|nikto|whatweb|wapiti|ferox|gobuster|dirb|ffuf|dirsearch|katana|hakrawler|gospider|wayback|gau|httpx|aquatone|eyewitness|gowitness/.test(n)) return 'recon';
  if (/exploit|metasploit|msf|sqlmap|hydra|medusa|ncrack|patator|hashcat|john|crack|brute|payload|commix|xss|dalfox|xxe|ssti|tplmap|evil|winrm|bloodhound|certipy|pacu|boofuzz|fuzzer|fuzz/.test(n)) return 'exploit';
  return 'misc';
}

export default function ServerList({
  servers,
  loading,
  selectedServer,
  onSelectServer,
  multiSelected,
  onToggleMulti,
  mode,
  onRefresh,
}) {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [actionLoading, setActionLoading] = useState({});
  const [actionError, setActionError] = useState({});

  const filtered = useMemo(() => {
    if (!Array.isArray(servers)) return [];
    return servers.filter((s) => {
      const name = s.name || s.id || '';
      const matchSearch = name.toLowerCase().includes(search.toLowerCase());
      const cat = s.category || guessCategory(name);
      const matchCat = category === 'all' || cat === category;
      return matchSearch && matchCat;
    });
  }, [servers, search, category]);

  const running = useMemo(
    () => (Array.isArray(servers) ? servers.filter((s) => s.health_ok).length : 0),
    [servers]
  );

  async function handleStart(e, name) {
    e.stopPropagation();
    setActionLoading((p) => ({ ...p, [name]: 'starting' }));
    setActionError((p) => ({ ...p, [name]: null }));
    try {
      await startServer(name);
      mcpClient.resetSession(name);
      // Poll every 3s until health_ok=true (max 45s)
      for (let i = 0; i < 15; i++) {
        await new Promise((r) => setTimeout(r, 3000));
        const list = await onRefresh?.();
        if (Array.isArray(list) && list.find((s) => s.name === name)?.health_ok) break;
      }
    } catch (err) {
      setActionError((p) => ({ ...p, [name]: err.message }));
    } finally {
      setActionLoading((p) => ({ ...p, [name]: null }));
    }
  }

  async function handleStop(e, name) {
    e.stopPropagation();
    setActionLoading((p) => ({ ...p, [name]: 'stopping' }));
    setActionError((p) => ({ ...p, [name]: null }));
    try {
      await stopServer(name);
      mcpClient.resetSession(name);
      // Poll every 3s until health_ok=false (max 15s)
      for (let i = 0; i < 5; i++) {
        await new Promise((r) => setTimeout(r, 3000));
        const list = await onRefresh?.();
        if (Array.isArray(list) && !list.find((s) => s.name === name)?.health_ok) break;
      }
    } catch (err) {
      setActionError((p) => ({ ...p, [name]: err.message }));
    } finally {
      setActionLoading((p) => ({ ...p, [name]: null }));
    }
  }

  return (
    <div className="hd-sidebar flex flex-col h-full">
      <div className="px-3 py-3 border-b hd-panel__head" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider hd-text-dim">Servers</span>
          <span className="text-xs hd-text-dim">
            {loading ? (
              <span className="spinner" style={{ width: 10, height: 10 }} />
            ) : (
              <>
                <span className="hd-text-ok">{running}</span>/{Array.isArray(servers) ? servers.length : 0}
              </>
            )}
          </span>
        </div>

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search servers..."
          className="hd-input text-xs mb-2"
        />

        {/* Category tabs */}
        <div className="flex flex-wrap gap-1">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`hd-chip capitalize ${category === cat ? 'hd-chip--active' : ''}`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Server list */}
      <div className="flex-1 overflow-y-auto">
        {loading && filtered.length === 0 && (
          <div className="p-4 text-center text-xs hd-text-dim">Loading servers...</div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="p-4 text-center text-xs hd-text-dim">No servers found</div>
        )}

        {filtered.map((server) => {
          const name = server.name || server.id || '';
          const isRunning = !!server.health_ok;
          const isSelected = selectedServer === name;
          const isMultiChecked = multiSelected?.has(name);
          const isActing = !!actionLoading[name];
          const err = actionError[name];

          return (
            <div
              key={name}
              onClick={() => onSelectServer?.(name)}
              className={`hd-list-item group relative ${isSelected ? 'hd-list-item--selected' : ''}`}
            >
              {mode === 'multi' && (
                <input
                  type="checkbox"
                  checked={isMultiChecked || false}
                  onChange={(e) => {
                    e.stopPropagation();
                    onToggleMulti?.(name);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="flex-shrink-0"
                />
              )}

              <span
                className="flex-shrink-0 rounded-full"
                title={getStatusTitle(server)}
                style={{ width: 8, height: 8, background: getStatusColor(server) }}
              />

              <span className="flex-1 text-xs truncate">{name}</span>

              <div
                className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => e.stopPropagation()}
              >
                {isActing ? (
                  <span className="spinner" style={{ width: 12, height: 12 }} />
                ) : isRunning ? (
                  <button
                    onClick={(e) => handleStop(e, name)}
                    title="Stop server"
                    className="hd-list-action hd-list-action--stop"
                  >
                    ■
                  </button>
                ) : (
                  <button
                    onClick={(e) => handleStart(e, name)}
                    title="Start server"
                    className="hd-list-action hd-list-action--start"
                  >
                    ▶
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer: refresh */}
      <div className="px-3 py-2 hd-border-t">
        <button
          onClick={onRefresh}
          disabled={loading}
          className="hd-btn hd-btn--muted w-full"
        >
          {loading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>
    </div>
  );
}
