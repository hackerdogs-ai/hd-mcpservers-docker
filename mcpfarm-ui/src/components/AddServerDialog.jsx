import React, { useState, useRef } from 'react';
import { createServer, importServers } from '../lib/api.js';
import { ALL_CATEGORIES, getCategoryInfo } from '../lib/categories.js';

const TABS = [
  { id: 'docker', label: 'Docker Image' },
  { id: 'http', label: 'HTTP Endpoint' },
  { id: 'import', label: 'Import JSON' },
];

function Field({ label, hint, value, onChange, placeholder, type = 'text', required }) {
  return (
    <div>
      <label className="hd-label">
        {label}
        {required && <span style={{ color: 'var(--semantic-error)', marginLeft: 3 }}>*</span>}
        {hint && <span className="hd-label-hint ml-2 text-xs">{hint}</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="hd-input text-sm"
        required={required}
      />
    </div>
  );
}

function EnvEditor({ env, onChange }) {
  const [newKey, setNewKey] = useState('');
  const [newVal, setNewVal] = useState('');

  function addEnv() {
    if (!newKey.trim()) return;
    onChange({ ...env, [newKey.trim()]: newVal });
    setNewKey('');
    setNewVal('');
  }

  function removeEnv(key) {
    const next = { ...env };
    delete next[key];
    onChange(next);
  }

  return (
    <div>
      <label className="hd-label">Environment Variables</label>
      {Object.entries(env).length > 0 && (
        <div className="add-srv-env-list">
          {Object.entries(env).map(([k, v]) => (
            <div key={k} className="add-srv-env-row">
              <span className="add-srv-env-key">{k}</span>
              <span className="add-srv-env-eq">=</span>
              <span className="add-srv-env-val">{v || '(empty)'}</span>
              <button type="button" className="add-srv-env-rm" onClick={() => removeEnv(k)} title="Remove">x</button>
            </div>
          ))}
        </div>
      )}
      <div className="add-srv-env-add">
        <input
          type="text"
          value={newKey}
          onChange={e => setNewKey(e.target.value)}
          placeholder="KEY"
          className="hd-input text-sm add-srv-env-input"
          onKeyDown={e => e.key === 'Enter' && addEnv()}
        />
        <span className="add-srv-env-eq">=</span>
        <input
          type="text"
          value={newVal}
          onChange={e => setNewVal(e.target.value)}
          placeholder="value"
          className="hd-input text-sm add-srv-env-input"
          onKeyDown={e => e.key === 'Enter' && addEnv()}
        />
        <button type="button" className="hd-btn hd-btn--muted add-srv-env-addbtn" onClick={addEnv}>+</button>
      </div>
    </div>
  );
}

function CategoryPicker({ value, onChange }) {
  return (
    <div>
      <label className="hd-label">Category</label>
      <select value={value} onChange={e => onChange(e.target.value)} className="hd-input text-sm">
        <option value="">None</option>
        {ALL_CATEGORIES.map(cat => (
          <option key={cat} value={cat}>{getCategoryInfo(cat).label}</option>
        ))}
      </select>
    </div>
  );
}

function DockerTab({ onSubmit, loading }) {
  const [name, setName] = useState('');
  const [image, setImage] = useState('');
  const [port, setPort] = useState('');
  const [category, setCategory] = useState('');
  const [env, setEnv] = useState({});

  function handleSubmit(e) {
    e.preventDefault();
    const serverName = name.trim().endsWith('-mcp') ? name.trim() : `${name.trim()}-mcp`;
    onSubmit({
      name: serverName.toLowerCase().replace(/\s+/g, '-'),
      image: image.trim(),
      port: port ? parseInt(port, 10) : 0,
      env,
      category: category || undefined,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="add-srv-form">
      <p className="add-srv-hint">
        Pull a Docker image from DockerHub and run it as an MCP server on the farm.
      </p>
      <Field label="Server Name" value={name} onChange={setName} placeholder="my-tool" required hint="-mcp suffix added automatically" />
      <Field label="Docker Image" value={image} onChange={setImage} placeholder="hackerdogs/my-tool-mcp:latest" required />
      <Field label="Port" value={port} onChange={setPort} placeholder="Auto-assigned if empty" type="number" hint="Leave blank for auto" />
      <CategoryPicker value={category} onChange={setCategory} />
      <EnvEditor env={env} onChange={setEnv} />
      <div className="add-srv-actions">
        <button type="submit" className="hd-dialog-btn hd-dialog-btn--green" disabled={loading || !name.trim() || !image.trim()}>
          {loading ? 'Creating...' : 'Create Server'}
        </button>
      </div>
    </form>
  );
}

function HttpTab({ onSubmit, loading }) {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('');
  const [env, setEnv] = useState({});

  function handleSubmit(e) {
    e.preventDefault();
    const serverName = name.trim().endsWith('-mcp') ? name.trim() : `${name.trim()}-mcp`;
    onSubmit({
      name: serverName.toLowerCase().replace(/\s+/g, '-'),
      url: url.trim(),
      env,
      category: category || undefined,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="add-srv-form">
      <p className="add-srv-hint">
        Connect to an existing MCP server via its HTTP streamable endpoint. No container is created &mdash; traffic is proxied directly.
      </p>
      <Field label="Server Name" value={name} onChange={setName} placeholder="my-remote-tool" required hint="-mcp suffix added automatically" />
      <Field label="Endpoint URL" value={url} onChange={setUrl} placeholder="https://my-server.example.com/mcp" required />
      <CategoryPicker value={category} onChange={setCategory} />
      <EnvEditor env={env} onChange={setEnv} />
      <div className="add-srv-actions">
        <button type="submit" className="hd-dialog-btn hd-dialog-btn--green" disabled={loading || !name.trim() || !url.trim()}>
          {loading ? 'Creating...' : 'Add Endpoint'}
        </button>
      </div>
    </form>
  );
}

const SAMPLE_JSON = `{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {}
    },
    "my-remote": {
      "url": "https://my-mcp.example.com/mcp"
    }
  }
}`;

function ImportTab({ onSubmit, loading }) {
  const [jsonText, setJsonText] = useState('');
  const [parsed, setParsed] = useState(null);
  const [parseError, setParseError] = useState(null);
  const [results, setResults] = useState(null);
  const fileInputRef = useRef(null);

  function handleParse(text) {
    setJsonText(text);
    setResults(null);
    setParseError(null);
    setParsed(null);
    if (!text.trim()) return;

    try {
      const obj = JSON.parse(text);
      const servers = obj.mcpServers || obj;
      if (typeof servers !== 'object' || Array.isArray(servers)) {
        setParseError('Expected an object with "mcpServers" key or a flat server map.');
        return;
      }
      const entries = Object.entries(servers);
      if (entries.length === 0) {
        setParseError('No servers found in the JSON.');
        return;
      }
      const preview = entries.map(([name, config]) => {
        const type = config.url ? 'HTTP Endpoint' : config.command === 'docker' ? 'Docker' : config.command ? `npm (${config.command})` : 'Unknown';
        return { name: name.endsWith('-mcp') ? name : `${name}-mcp`, type, config };
      });
      setParsed(preview);
    } catch (e) {
      setParseError(`Invalid JSON: ${e.message}`);
    }
  }

  function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => handleParse(ev.target.result);
    reader.readAsText(file);
  }

  async function handleImport() {
    try {
      const obj = JSON.parse(jsonText);
      const servers = obj.mcpServers || obj;
      const res = await onSubmit(servers);
      setResults(res);
    } catch (e) {
      setParseError(e.message);
    }
  }

  return (
    <div className="add-srv-form">
      <p className="add-srv-hint">
        Paste or upload a Claude Desktop or Cursor MCP config JSON. Each server entry will be created on the farm.
      </p>

      <div className="add-srv-import-actions">
        <button type="button" className="hd-btn hd-btn--muted" onClick={() => fileInputRef.current?.click()}>
          Upload JSON file
        </button>
        <button type="button" className="hd-btn hd-btn--muted" onClick={() => handleParse(SAMPLE_JSON)}>
          Load example
        </button>
        <input ref={fileInputRef} type="file" accept=".json,application/json" onChange={handleFileUpload} style={{ display: 'none' }} />
      </div>

      <div>
        <label className="hd-label">JSON Config</label>
        <textarea
          value={jsonText}
          onChange={e => handleParse(e.target.value)}
          placeholder={SAMPLE_JSON}
          className="hd-input text-sm add-srv-textarea"
          rows={10}
          spellCheck={false}
        />
      </div>

      {parseError && <div className="add-srv-error">{parseError}</div>}

      {parsed && !results && (
        <div className="add-srv-preview">
          <label className="hd-label">Servers to import ({parsed.length})</label>
          <div className="add-srv-preview-list">
            {parsed.map(s => (
              <div key={s.name} className="add-srv-preview-row">
                <span className="add-srv-preview-name">{s.name}</span>
                <span className="add-srv-preview-type">{s.type}</span>
              </div>
            ))}
          </div>
          <div className="add-srv-actions">
            <button type="button" className="hd-dialog-btn hd-dialog-btn--green" onClick={handleImport} disabled={loading}>
              {loading ? 'Importing...' : `Import ${parsed.length} Server${parsed.length > 1 ? 's' : ''}`}
            </button>
          </div>
        </div>
      )}

      {results && (
        <div className="add-srv-results">
          <label className="hd-label">Import Results</label>
          <div className="add-srv-preview-list">
            {results.results.map((r, i) => (
              <div key={i} className="add-srv-preview-row">
                <span className="add-srv-preview-name">{r.name}</span>
                <span className={`add-srv-result-badge add-srv-result-badge--${r.status}`}>
                  {r.status}
                </span>
                {r.reason && <span className="add-srv-result-reason">{r.reason}</span>}
              </div>
            ))}
          </div>
          <div className="add-srv-results-summary">
            {results.imported} of {results.results.length} imported successfully
          </div>
        </div>
      )}
    </div>
  );
}

export default function AddServerDialog({ onClose, onRefresh }) {
  const [tab, setTab] = useState('docker');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  async function handleCreate(payload) {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await createServer(payload);
      setSuccess(`Server "${payload.name}" created successfully.`);
      onRefresh?.();
      setTimeout(() => onClose(), 1500);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleImport(mcpServers) {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await importServers(mcpServers);
      onRefresh?.();
      return res;
    } catch (e) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="hd-modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="hd-modal add-srv-modal">
        <div className="hd-modal__head">
          <h2 className="hd-modal__title">Add MCP Server</h2>
          <button type="button" onClick={onClose} className="hd-modal__close" aria-label="Close">x</button>
        </div>

        <div className="add-srv-tabs">
          {TABS.map(t => (
            <button
              key={t.id}
              type="button"
              className={`add-srv-tab ${tab === t.id ? 'add-srv-tab--active' : ''}`}
              onClick={() => { setTab(t.id); setError(null); setSuccess(null); }}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="hd-modal__body">
          {error && <div className="add-srv-error">{error}</div>}
          {success && <div className="add-srv-success">{success}</div>}

          {tab === 'docker' && <DockerTab onSubmit={handleCreate} loading={loading} />}
          {tab === 'http' && <HttpTab onSubmit={handleCreate} loading={loading} />}
          {tab === 'import' && <ImportTab onSubmit={handleImport} loading={loading} />}
        </div>
      </div>
    </div>
  );
}
