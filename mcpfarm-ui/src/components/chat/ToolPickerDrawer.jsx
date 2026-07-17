import { useEffect, useMemo, useState } from 'react';
import { isServerRunning } from '../../lib/categories.js';
import { mcpClient } from '../../lib/mcp.js';

/**
 * Drawer for static tool binding: pick servers (and optionally specific tools)
 * that get bound to every message. Selection shape:
 *   { servers: string[], tools: { [server]: string[] } }
 */
export default function ToolPickerDrawer({ servers, selection, onChange, onClose }) {
  const [query, setQuery] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [toolsByServer, setToolsByServer] = useState({});
  const [loadingTools, setLoadingTools] = useState(false);

  const running = useMemo(
    () => (servers || []).filter((s) => isServerRunning(s)),
    [servers],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return running;
    return running.filter((s) => s.name.toLowerCase().includes(q));
  }, [running, query]);

  const selectedServers = new Set(selection.servers || []);

  function toggleServer(name) {
    const next = new Set(selectedServers);
    if (next.has(name)) {
      next.delete(name);
      const tools = { ...selection.tools };
      delete tools[name];
      onChange({ servers: [...next], tools });
    } else {
      next.add(name);
      onChange({ servers: [...next], tools: selection.tools || {} });
    }
  }

  async function expandServer(name) {
    if (expanded === name) { setExpanded(null); return; }
    setExpanded(name);
    if (!toolsByServer[name]) {
      setLoadingTools(true);
      try {
        const t = await mcpClient.listTools(name);
        setToolsByServer((prev) => ({ ...prev, [name]: t }));
      } catch {
        setToolsByServer((prev) => ({ ...prev, [name]: [] }));
      } finally {
        setLoadingTools(false);
      }
    }
  }

  function toggleTool(server, toolName) {
    const current = new Set(selection.tools?.[server] || []);
    if (current.has(toolName)) current.delete(toolName);
    else current.add(toolName);
    const servers = new Set(selectedServers);
    servers.add(server);
    onChange({ servers: [...servers], tools: { ...selection.tools, [server]: [...current] } });
  }

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="aui-drawer-overlay" onClick={onClose}>
      <aside className="aui-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="aui-drawer-head">
          <div className="aui-drawer-title">Bind tools</div>
          <button className="aui-drawer-close" onClick={onClose} aria-label="Close">×</button>
        </div>
        <input
          className="aui-drawer-search"
          placeholder="Search running servers…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        <div className="aui-drawer-hint">
          {selectedServers.size
            ? `${selectedServers.size} server(s) bound`
            : 'Select servers to bind. Leave empty to use dynamic auto-selection.'}
        </div>
        <div className="aui-drawer-list">
          {filtered.length === 0 && <div className="aui-drawer-empty">No running servers.</div>}
          {filtered.map((s) => {
            const name = s.name;
            const picked = selectedServers.has(name);
            const toolSel = selection.tools?.[name] || [];
            return (
              <div key={name} className={`aui-drawer-item${picked ? ' aui-drawer-item-on' : ''}`}>
                <div className="aui-drawer-row">
                  <label className="aui-drawer-check">
                    <input type="checkbox" checked={picked} onChange={() => toggleServer(name)} />
                    <span className="aui-drawer-name">{name.replace(/-mcp$/, '')}</span>
                  </label>
                  <button className="aui-drawer-expand" onClick={() => expandServer(name)}>
                    {expanded === name ? 'Hide tools' : 'Tools'}
                    {toolSel.length ? ` (${toolSel.length})` : ''}
                  </button>
                </div>
                {expanded === name && (
                  <div className="aui-drawer-tools">
                    {loadingTools && !toolsByServer[name] && <div className="aui-drawer-empty">Loading…</div>}
                    {(toolsByServer[name] || []).map((t) => (
                      <label key={t.name} className="aui-drawer-tool">
                        <input
                          type="checkbox"
                          checked={toolSel.includes(t.name)}
                          onChange={() => toggleTool(name, t.name)}
                        />
                        <span className="aui-drawer-tool-name">{t.name}</span>
                      </label>
                    ))}
                    {toolsByServer[name] && toolsByServer[name].length === 0 && (
                      <div className="aui-drawer-empty">No tools (all bound by default).</div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <div className="aui-drawer-foot">
          <button className="aui-btn-ghost" onClick={() => onChange({ servers: [], tools: {} })}>Clear</button>
          <button className="aui-btn-primary" onClick={onClose}>Done</button>
        </div>
      </aside>
    </div>
  );
}
