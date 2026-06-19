import React, { useState, useEffect } from 'react';
import { getBaseUrl, getApiKey, getAdminSecret, getClaudeKey, getHeygenKey, getHeygenAvatarId, saveSettings, rotateSecret } from '../lib/api.js';

export default function Settings({ onClose }) {
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [adminSecret, setAdminSecret] = useState('');
  const [claudeKey, setClaudeKey] = useState('');
  const [heygenKey, setHeygenKey] = useState('');
  const [heygenAvatarId, setHeygenAvatarId] = useState('');
  const [saved, setSaved] = useState(false);
  const [rotating, setRotating] = useState(false);
  const [rotateMsg, setRotateMsg] = useState(null);

  useEffect(() => {
    setBaseUrl(getBaseUrl());
    setApiKey(getApiKey());
    setAdminSecret(getAdminSecret());
    setClaudeKey(getClaudeKey());
    setHeygenKey(getHeygenKey());
    setHeygenAvatarId(getHeygenAvatarId());
  }, []);

  function handleSave() {
    saveSettings({ baseUrl, apiKey, adminSecret, claudeKey, heygenKey, heygenAvatarId });
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 800);
  }

  async function handleRotate() {
    setRotating(true);
    setRotateMsg(null);
    try {
      const data = await rotateSecret();
      const newSecret = data.admin_secret;
      setAdminSecret(newSecret);
      saveSettings({ adminSecret: newSecret });
      setRotateMsg({ ok: true, text: 'New secret saved' });
    } catch (e) {
      setRotateMsg({ ok: false, text: e.message });
    } finally {
      setRotating(false);
      setTimeout(() => setRotateMsg(null), 4000);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.7)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-full max-w-lg rounded-lg border shadow-2xl"
        style={{ background: '#161b22', borderColor: '#30363d' }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b"
          style={{ borderColor: '#30363d' }}
        >
          <h2 className="text-lg font-semibold" style={{ color: '#e6edf3' }}>
            Settings
          </h2>
          <button
            onClick={onClose}
            className="text-2xl leading-none transition-colors hover:text-white"
            style={{ color: '#8b949e' }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          <Field
            label="Farm Base URL"
            value={baseUrl}
            onChange={setBaseUrl}
            placeholder="https://mcpservers-dev.hackerdogs.ai"
            type="text"
          />
          <Field
            label="API Key"
            hint="Bearer token for MCP server access"
            value={apiKey}
            onChange={setApiKey}
            placeholder="hd-..."
            type="password"
          />
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: '#e6edf3' }}>
              Admin Secret
              <span className="ml-2 text-xs font-normal" style={{ color: '#8b949e' }}>
                X-Admin-Secret header for start/stop/reload
              </span>
            </label>
            <div className="flex gap-2">
              <input
                type="password"
                value={adminSecret}
                onChange={(e) => setAdminSecret(e.target.value)}
                placeholder="admin-secret"
                className="flex-1 px-3 py-2 rounded text-sm border transition-colors"
                style={{ background: '#0d1117', borderColor: '#30363d', color: '#e6edf3', outline: 'none' }}
                onFocus={(e) => (e.target.style.borderColor = '#3fb950')}
                onBlur={(e) => (e.target.style.borderColor = '#30363d')}
              />
              <button
                onClick={handleRotate}
                disabled={rotating}
                className="px-3 py-2 rounded text-sm font-medium transition-all whitespace-nowrap"
                style={{
                  background: rotateMsg?.ok ? '#238636' : '#21262d',
                  color: rotateMsg?.ok ? '#fff' : '#8b949e',
                  border: '1px solid #30363d',
                  opacity: rotating ? 0.6 : 1,
                }}
              >
                {rotating ? '…' : rotateMsg?.ok ? '✓ Rotated' : '↺ Generate'}
              </button>
            </div>
            {rotateMsg && !rotateMsg.ok && (
              <p className="mt-1 text-xs" style={{ color: '#f85149' }}>{rotateMsg.text}</p>
            )}
          </div>
          <Field
            label="Claude API Key"
            hint="Required for Prompt mode and Nova"
            value={claudeKey}
            onChange={setClaudeKey}
            placeholder="sk-ant-..."
            type="password"
          />
          <Field
            label="HeyGen API Key"
            hint="Enables live avatar in Nova tab"
            value={heygenKey}
            onChange={setHeygenKey}
            placeholder="paste your HeyGen key..."
            type="password"
          />
          <Field
            label="HeyGen Avatar ID"
            hint="liveavatar.com → Avatars → copy ID"
            value={heygenAvatarId}
            onChange={setHeygenAvatarId}
            placeholder="e.g. Avatar_v3_public_..."
            type="text"
          />
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 px-6 py-4 border-t"
          style={{ borderColor: '#30363d' }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 rounded text-sm transition-colors hover:text-white"
            style={{ color: '#8b949e' }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded text-sm font-medium transition-all"
            style={{
              background: saved ? '#238636' : '#3fb950',
              color: '#0d1117',
            }}
          >
            {saved ? '✓ Saved' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, hint, value, onChange, placeholder, type = 'text' }) {
  return (
    <div>
      <label className="block text-sm font-medium mb-1" style={{ color: '#e6edf3' }}>
        {label}
        {hint && (
          <span className="ml-2 text-xs font-normal" style={{ color: '#8b949e' }}>
            {hint}
          </span>
        )}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded text-sm border transition-colors"
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
