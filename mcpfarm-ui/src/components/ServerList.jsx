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
    <div
      className="flex flex-col h-full"
      style={{ background: '#161b22', borderRight: '1px solid #30363d' }}
    >
      {/* Header */}
      <div className="px-3 py-3 border-b" style={{ borderColor: '#30363d' }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8b949e' }}>
            Servers
          </span>
          <span className="text-xs" style={{ color: '#8b949e' }}>
            {loading ? (
              <span className="spinner" style={{ width: 10, height: 10 }} />
            ) : (
              <>
                <span style={{ color: '#3fb950' }}>{running}</span>/{Array.isArray(servers) ? servers.length : 0}
              </>
            )}
          </span>
        </div>

        {/* Search */}
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search servers..."
          className="w-full px-2 py-1.5 rounded text-xs border mb-2"
          style={{
            background: '#0d1117',
            borderColor: '#30363d',
            color: '#e6edf3',
            outline: 'none',
          }}
          onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
          onBlur={(e) => (e.target.style.borderColor = '#30363d')}
        />

        {/* Category tabs */}
        <div className="flex flex-wrap gap-1">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className="px-2 py-0.5 rounded text-xs transition-colors capitalize"
              style={{
                background: category === cat ? '#3fb950' : '#0d1117',
                color: category === cat ? '#0d1117' : '#8b949e',
                border: `1px solid ${category === cat ? '#3fb950' : '#30363d'}`,
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Server list */}
      <div className="flex-1 overflow-y-auto">
        {loading && filtered.length === 0 && (
          <div className="p-4 text-center text-xs" style={{ color: '#8b949e' }}>
            Loading servers...
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="p-4 text-center text-xs" style={{ color: '#8b949e' }}>
            No servers found
          </div>
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
              className="group relative flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors border-b"
              style={{
                borderColor: '#21262d',
                background: isSelected ? '#1f2937' : 'transparent',
              }}
              onMouseEnter={(e) => {
                if (!isSelected) e.currentTarget.style.background = '#1c2128';
              }}
              onMouseLeave={(e) => {
                if (!isSelected) e.currentTarget.style.background = 'transparent';
              }}
            >
              {/* Multi-select checkbox */}
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
                  style={{ accentColor: '#3fb950' }}
                />
              )}

              {/* Status dot */}
              <span
                className="flex-shrink-0 rounded-full"
                title={getStatusTitle(server)}
                style={{
                  width: 8,
                  height: 8,
                  background: getStatusColor(server),
                }}
              />

              {/* Name */}
              <span
                className="flex-1 text-xs truncate"
                style={{ color: isSelected ? '#e6edf3' : '#c9d1d9' }}
              >
                {name}
              </span>

              {/* Start/Stop buttons */}
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
                    className="text-xs px-1.5 py-0.5 rounded transition-colors"
                    style={{
                      background: 'rgba(248,81,73,0.15)',
                      color: '#f85149',
                      border: '1px solid rgba(248,81,73,0.3)',
                    }}
                  >
                    ■
                  </button>
                ) : (
                  <button
                    onClick={(e) => handleStart(e, name)}
                    title="Start server"
                    className="text-xs px-1.5 py-0.5 rounded transition-colors"
                    style={{
                      background: 'rgba(63,185,80,0.15)',
                      color: '#3fb950',
                      border: '1px solid rgba(63,185,80,0.3)',
                    }}
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
      <div className="px-3 py-2 border-t" style={{ borderColor: '#30363d' }}>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="w-full py-1.5 rounded text-xs transition-colors"
          style={{
            background: '#0d1117',
            color: loading ? '#484f58' : '#8b949e',
            border: '1px solid #30363d',
          }}
        >
          {loading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>
    </div>
  );
}
