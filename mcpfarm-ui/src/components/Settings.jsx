import React, { useState, useEffect } from 'react';
import {
  getBaseUrl,
  getApiKey,
  getAdminSecret,
  getOllamaUrl,
  getHeygenKey,
  getHeygenAvatarId,
  getBedrockRegion,
  getBedrockModels,
  getAzureOpenAIEndpoint,
  getAzureOpenAIModels,
  getOpenRouterModels,
  getGrokModels,
  getGeminiModels,
  saveSettings,
  rotateSecret,
  listLlmKeys,
  putLlmKey,
  deleteLlmKey,
  listApiKeys,
  createApiKey,
  revokeApiKey,
  fetchUiConfig,
} from '../lib/api.js';
import Icon from './Icon.jsx';

// LLM provider keys are stored server-side (encrypted). These never touch localStorage.
const VAULT_PROVIDERS = ['claude', 'openai', 'bedrock', 'azure', 'openrouter', 'grok', 'gemini'];

export default function Settings({ onClose }) {
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [adminSecret, setAdminSecret] = useState('');
  const [claudeKey, setClaudeKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [ollamaUrl, setOllamaUrl] = useState('');
  const [heygenKey, setHeygenKey] = useState('');
  const [heygenAvatarId, setHeygenAvatarId] = useState('');
  const [bedrockApiKey, setBedrockApiKey] = useState('');
  const [bedrockRegion, setBedrockRegion] = useState('');
  const [bedrockModels, setBedrockModels] = useState('');
  const [azureOpenaiKey, setAzureOpenaiKey] = useState('');
  const [azureOpenaiEndpoint, setAzureOpenaiEndpoint] = useState('');
  const [azureOpenaiModels, setAzureOpenaiModels] = useState('');
  const [openrouterKey, setOpenrouterKey] = useState('');
  const [openrouterModels, setOpenrouterModels] = useState('');
  const [grokKey, setGrokKey] = useState('');
  const [grokModels, setGrokModels] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [geminiModels, setGeminiModels] = useState('');
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState(null);
  const [rotating, setRotating] = useState(false);
  const [rotateMsg, setRotateMsg] = useState(null);
  // Masked status of server-side keys, keyed by provider → { key_prefix }.
  const [vaultKeys, setVaultKeys] = useState({});
  const [farmKeys, setFarmKeys] = useState([]);
  const [keysLoading, setKeysLoading] = useState(false);
  const [keysErr, setKeysErr] = useState(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [creatingKey, setCreatingKey] = useState(false);
  const [createdPlaintext, setCreatedPlaintext] = useState(null);

  /** Keep localStorage in sync so adminHeaders() matches the form field. */
  function syncAdminSecret(secret) {
    const value = (secret ?? '').trim();
    setAdminSecret(value);
    if (value) saveSettings({ adminSecret: value });
    return value;
  }

  function loadVaultKeys() {
    listLlmKeys()
      .then((res) => {
        const map = {};
        (res.keys || []).forEach((k) => { map[k.provider] = k; });
        setVaultKeys(map);
      })
      .catch(() => setVaultKeys({}));
  }

  function loadFarmKeys() {
    setKeysLoading(true);
    setKeysErr(null);
    listApiKeys()
      .then((rows) => setFarmKeys(Array.isArray(rows) ? rows : []))
      .catch((e) => {
        setFarmKeys([]);
        const msg = e.message || String(e);
        if (/403|invalid admin secret/i.test(msg)) {
          setKeysErr(
            'Admin secret mismatch. Reloading credentials from the farm… If this persists, paste the current ADMIN_SECRET below and click Save.',
          );
        } else {
          setKeysErr(msg);
        }
      })
      .finally(() => setKeysLoading(false));
  }

  useEffect(() => {
    let cancelled = false;
    async function init() {
      setBaseUrl(getBaseUrl());
      setApiKey(getApiKey());
      setAdminSecret(getAdminSecret());
      setOllamaUrl(getOllamaUrl());
      setHeygenKey(getHeygenKey());
      setHeygenAvatarId(getHeygenAvatarId());
      setBedrockRegion(getBedrockRegion());
      setBedrockModels(getBedrockModels());
      setAzureOpenaiEndpoint(getAzureOpenAIEndpoint());
      setAzureOpenaiModels(getAzureOpenAIModels());
      setOpenrouterModels(getOpenRouterModels());
      setGrokModels(getGrokModels());
      setGeminiModels(getGeminiModels());

      // Prefer live credentials from the gateway so a rotated secret is picked up.
      try {
        const cfg = await fetchUiConfig();
        if (cancelled) return;
        if (cfg.base_url !== undefined) {
          setBaseUrl(cfg.base_url);
          saveSettings({ baseUrl: cfg.base_url });
        }
        if (cfg.api_key) {
          setApiKey(cfg.api_key);
          saveSettings({ apiKey: cfg.api_key });
        }
        if (cfg.admin_secret) {
          syncAdminSecret(cfg.admin_secret);
        }
      } catch {
        /* keep localStorage values */
      }
      if (cancelled) return;
      loadVaultKeys();
      loadFarmKeys();
    }
    init();
    return () => { cancelled = true; };
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaveErr(null);
    // Non-secret preferences stay in localStorage; provider keys never do.
    saveSettings({
      baseUrl,
      apiKey,
      adminSecret,
      ollamaUrl,
      heygenKey,
      heygenAvatarId,
      bedrockRegion,
      bedrockModels,
      azureOpenaiEndpoint,
      azureOpenaiModels,
      openrouterModels,
      grokModels,
      geminiModels,
    });

    // Upload any newly-entered provider keys to the encrypted server vault.
    const pending = [
      ['claude', claudeKey], ['openai', openaiKey], ['bedrock', bedrockApiKey],
      ['azure', azureOpenaiKey], ['openrouter', openrouterKey], ['grok', grokKey],
      ['gemini', geminiKey],
    ];
    try {
      for (const [provider, value] of pending) {
        if (value && value.trim()) await putLlmKey(provider, value.trim());
      }
      setSaved(true);
      setTimeout(() => { setSaved(false); onClose(); }, 800);
    } catch (e) {
      setSaveErr(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleClearKey(provider, setter) {
    try {
      await deleteLlmKey(provider);
      setter('');
      loadVaultKeys();
    } catch (e) {
      setSaveErr(e.message);
    }
  }

  async function handleRotate() {
    syncAdminSecret(adminSecret);
    setRotating(true);
    setRotateMsg(null);
    try {
      const data = await rotateSecret();
      const newSecret = data.admin_secret;
      syncAdminSecret(newSecret);
      if (data.api_key) {
        setApiKey(data.api_key);
        saveSettings({ apiKey: data.api_key });
      }
      setRotateMsg({
        ok: true,
        text: 'Rotated — this browser is updated. Copy the new secret; update .env if you keep ADMIN_SECRET there. Other browsers still on the old secret will get 403 until refreshed.',
      });
    } catch (e) {
      setRotateMsg({ ok: false, text: e.message });
    } finally {
      setRotating(false);
      setTimeout(() => setRotateMsg(null), 4000);
    }
  }

  async function handleCreateFarmKey() {
    syncAdminSecret(adminSecret);
    const name = (newKeyName || 'ui-key').trim();
    setCreatingKey(true);
    setKeysErr(null);
    setCreatedPlaintext(null);
    try {
      const data = await createApiKey(name);
      setCreatedPlaintext(data.key);
      setNewKeyName('');
      // Remember for Chat in this browser (not shown as a separate Settings field).
      if (data.key) {
        setApiKey(data.key);
        saveSettings({ apiKey: data.key });
      }
      loadFarmKeys();
      try {
        await navigator.clipboard.writeText(data.key);
      } catch { /* ignore */ }
    } catch (e) {
      setKeysErr(e.message);
    } finally {
      setCreatingKey(false);
    }
  }

  async function handleRevokeFarmKey(id, keyPrefix) {
    if (!window.confirm('Revoke this API key? Clients using it will fail immediately.')) return;
    syncAdminSecret(adminSecret);
    setKeysErr(null);
    try {
      await revokeApiKey(id);
      if (createdPlaintext) setCreatedPlaintext(null);
      if (keyPrefix && apiKey && apiKey.startsWith(keyPrefix)) {
        setApiKey('');
        saveSettings({ apiKey: '' });
      }
      loadFarmKeys();
    } catch (e) {
      setKeysErr(e.message);
    }
  }

  return (
    <div
      className="hd-modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="hd-modal hd-modal--settings">
        <div className="hd-modal__head">
          <h2 className="hd-modal__title">Settings</h2>
          <button type="button" onClick={onClose} className="hd-modal__close" aria-label="Close">
            ×
          </button>
        </div>

        <div className="hd-modal__body space-y-4">
          <Field
            label="Farm Base URL"
            value={baseUrl}
            onChange={setBaseUrl}
            placeholder="https://mcpservers-dev.hackerdogs.ai"
            type="text"
          />
          <div>
            <label className="hd-label" htmlFor="settings-admin-secret">
              Admin secret
              <span className="hd-label-hint ml-2 text-xs">
                Farm operator password (X-Admin-Secret) for start/stop, Settings, and key management
              </span>
            </label>
            <div className="flex gap-2">
              <PrefixedSecretInput
                id="settings-admin-secret"
                value={adminSecret}
                onChange={setAdminSecret}
                placeholder="Paste or generate an admin secret"
                className="hd-input flex-1 text-sm font-mono"
              />
              <button
                type="button"
                onClick={handleRotate}
                disabled={rotating}
                className={`hd-btn hd-btn--muted whitespace-nowrap${rotateMsg?.ok ? ' hd-text-ok' : ''}`}
              >
                {rotating ? '…' : rotateMsg?.ok ? <><Icon name="check" size={16} /> Rotated</> : 'Rotate'}
              </button>
            </div>
            {!adminSecret && (
              <p className="mt-1 text-xs hd-label-hint">
                Not set in this browser. If the farm already has one (e.g. from .env), paste it here.
              </p>
            )}
            {rotateMsg && !rotateMsg.ok && (
              <p className="mt-1 text-xs hd-text-err">{rotateMsg.text}</p>
            )}
            {rotateMsg?.ok && (
              <p className="mt-1 text-xs hd-text-ok">{rotateMsg.text}</p>
            )}
          </div>

          <SectionTitle>API keys</SectionTitle>
          <p className="hd-label-hint text-xs" style={{ marginTop: '-0.25rem' }}>
            Tokens for MCP clients (Cursor, Claude Desktop, etc.) and for Chat in this browser.
            Create a key when you need one — the full secret is shown only once. Revoke to invalidate it.
          </p>
          <div className="hd-keymgr">
            <div className="hd-keymgr__toolbar">
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Name (e.g. cursor-client)"
                className="hd-input flex-1 text-sm"
                aria-label="New API key name"
              />
              <button
                type="button"
                className="hd-btn hd-btn--primary whitespace-nowrap"
                disabled={creatingKey}
                onClick={handleCreateFarmKey}
              >
                {creatingKey ? 'Creating…' : 'Create key'}
              </button>
              <button
                type="button"
                className="hd-btn hd-btn--muted whitespace-nowrap"
                disabled={keysLoading}
                onClick={() => {
                  syncAdminSecret(adminSecret);
                  loadFarmKeys();
                }}
                title="Refresh list"
              >
                {keysLoading ? 'Refreshing…' : 'Refresh'}
              </button>
            </div>

            {createdPlaintext && (
              <div className="hd-keymgr__oneshot" role="status">
                <button
                  type="button"
                  className="hd-keymgr__oneshot-dismiss"
                  aria-label="Dismiss"
                  title="Dismiss"
                  onClick={() => setCreatedPlaintext(null)}
                >
                  ×
                </button>
                <div className="hd-keymgr__oneshot-label">
                  Copy this key now — it will not be shown again in full.
                  Chat in this browser will use it automatically.
                </div>
                <div className="hd-keymgr__oneshot-row">
                  <code className="hd-keymgr__oneshot-value">{createdPlaintext}</code>
                  <button
                    type="button"
                    className="hd-keymgr__icon-btn"
                    aria-label="Copy to clipboard"
                    title="Copy to clipboard"
                    onClick={() => {
                      navigator.clipboard?.writeText(createdPlaintext).catch(() => {});
                    }}
                  >
                    <Icon name="content_copy" size={18} />
                  </button>
                </div>
              </div>
            )}

            {keysErr && <p className="text-xs hd-text-err">{keysErr}</p>}

            <div className="hd-keymgr__table-wrap">
              <table className="hd-keymgr__table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Prefix</th>
                    <th scope="col">Status</th>
                    <th scope="col">Created</th>
                    <th scope="col" className="hd-keymgr__col-actions">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {keysLoading && farmKeys.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="hd-keymgr__empty">Loading…</td>
                    </tr>
                  ) : farmKeys.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="hd-keymgr__empty">No API keys yet. Create one when you need Chat or an MCP client.</td>
                    </tr>
                  ) : (
                    farmKeys.map((k) => {
                      const usedHere = Boolean(
                        apiKey && k.key_prefix && apiKey.startsWith(k.key_prefix),
                      );
                      return (
                      <tr key={k.id}>
                        <td>
                          {k.name}
                          {usedHere && (
                            <span className="hd-keymgr__badge hd-keymgr__badge--ok" style={{ marginLeft: 8 }}>
                              This browser
                            </span>
                          )}
                        </td>
                        <td className="font-mono text-xs">{k.key_prefix}…</td>
                        <td>
                          <span className={k.is_active ? 'hd-keymgr__badge hd-keymgr__badge--ok' : 'hd-keymgr__badge hd-keymgr__badge--off'}>
                            {k.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="text-xs hd-label-hint">
                          {k.created_at ? String(k.created_at).slice(0, 10) : '—'}
                        </td>
                        <td className="hd-keymgr__col-actions">
                          <button
                            type="button"
                            className="hd-btn hd-btn--ghost hd-keymgr__revoke"
                            onClick={() => handleRevokeFarmKey(k.id, k.key_prefix)}
                          >
                            Revoke
                          </button>
                        </td>
                      </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <SectionTitle>Chat LLM Providers</SectionTitle>
          <p className="hd-label-hint text-xs" style={{ marginTop: '-0.25rem' }}>
            Provider keys are encrypted and stored on the server. They are never saved in your browser.
          </p>

          <KeyField
            provider="claude"
            label="Claude API Key"
            hint="Nova and Chat (Claude provider)"
            value={claudeKey}
            onChange={setClaudeKey}
            placeholder="sk-ant-..."
            vaultKeys={vaultKeys}
            onClear={handleClearKey}
          />
          <KeyField
            provider="openai"
            label="OpenAI API Key"
            hint="Chat tab (OpenAI provider)"
            value={openaiKey}
            onChange={setOpenaiKey}
            placeholder="sk-..."
            vaultKeys={vaultKeys}
            onClear={handleClearKey}
          />
          <Field
            label="Ollama URL"
            hint="Local Ollama for Chat tab (default: http://localhost:11434)"
            value={ollamaUrl}
            onChange={setOllamaUrl}
            placeholder="http://localhost:11434"
            type="text"
          />

          <SectionTitle>AWS Bedrock</SectionTitle>
          <KeyField
            provider="bedrock"
            label="Bedrock API Key"
            hint="Bedrock API key for Chat tab"
            value={bedrockApiKey}
            onChange={setBedrockApiKey}
            placeholder="bedrock-api-key-..."
            vaultKeys={vaultKeys}
            onClear={handleClearKey}
          />
          <Field
            label="Bedrock Region"
            hint="AWS region (e.g. us-east-1)"
            value={bedrockRegion}
            onChange={setBedrockRegion}
            placeholder="us-east-1"
            type="text"
          />
          <Field
            label="Bedrock Models"
            hint="Comma-separated model IDs (overrides defaults)"
            value={bedrockModels}
            onChange={setBedrockModels}
            placeholder="anthropic.claude-3-5-sonnet-20241022-v2:0, amazon.nova-pro-v1:0"
            type="text"
          />

          <SectionTitle>Azure OpenAI</SectionTitle>
          <KeyField
            provider="azure"
            label="Azure OpenAI API Key"
            hint="Chat tab (Azure provider)"
            value={azureOpenaiKey}
            onChange={setAzureOpenaiKey}
            placeholder="azure-api-key"
            vaultKeys={vaultKeys}
            onClear={handleClearKey}
          />
          <Field
            label="Azure OpenAI Endpoint"
            hint="Resource endpoint URL"
            value={azureOpenaiEndpoint}
            onChange={setAzureOpenaiEndpoint}
            placeholder="https://myresource.openai.azure.com"
            type="text"
          />
          <Field
            label="Azure Deployments"
            hint="Comma-separated deployment names (used as models)"
            value={azureOpenaiModels}
            onChange={setAzureOpenaiModels}
            placeholder="gpt-4o, gpt-4o-mini, gpt-4"
            type="text"
          />

          <SectionTitle>OpenRouter</SectionTitle>
          <KeyField
            provider="openrouter"
            label="OpenRouter API Key"
            hint="Chat tab (OpenRouter provider)"
            value={openrouterKey}
            onChange={setOpenrouterKey}
            placeholder="sk-or-..."
            vaultKeys={vaultKeys}
            onClear={handleClearKey}
          />
          <Field
            label="OpenRouter Models"
            hint="Comma-separated model slugs (overrides defaults)"
            value={openrouterModels}
            onChange={setOpenrouterModels}
            placeholder="anthropic/claude-sonnet-4, openai/gpt-4o"
            type="text"
          />

          <SectionTitle>Grok (xAI)</SectionTitle>
          <KeyField
            provider="grok"
            label="Grok API Key"
            hint="Chat tab (Grok provider)"
            value={grokKey}
            onChange={setGrokKey}
            placeholder="xai-..."
            vaultKeys={vaultKeys}
            onClear={handleClearKey}
          />
          <Field
            label="Grok Models"
            hint="Comma-separated model names (overrides defaults)"
            value={grokModels}
            onChange={setGrokModels}
            placeholder="grok-3, grok-3-mini"
            type="text"
          />

          <SectionTitle>Google Gemini</SectionTitle>
          <KeyField
            provider="gemini"
            label="Gemini API Key"
            hint="Chat tab (Gemini provider)"
            value={geminiKey}
            onChange={setGeminiKey}
            placeholder="AIza..."
            vaultKeys={vaultKeys}
            onClear={handleClearKey}
          />
          <Field
            label="Gemini Models"
            hint="Comma-separated model names (overrides defaults)"
            value={geminiModels}
            onChange={setGeminiModels}
            placeholder="gemini-2.5-flash, gemini-2.5-pro"
            type="text"
          />

          <SectionTitle>Other</SectionTitle>
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

        <div className="hd-modal__foot">
          {saveErr && <span className="hd-text-err text-xs mr-auto">{saveErr}</span>}
          <button type="button" onClick={onClose} className="hd-btn hd-btn--ghost">
            Cancel
          </button>
          <button type="button" onClick={handleSave} disabled={saving} className="hd-btn hd-btn--primary">
            {saving ? '…' : saved ? <><Icon name="check" size={16} /> Saved</> : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <h3 className="hd-settings-section-title">{children}</h3>
  );
}

function KeyField({ provider, label, hint, value, onChange, placeholder, vaultKeys, onClear }) {
  const stored = vaultKeys?.[provider];
  return (
    <div>
      <label className="hd-label">
        {label}
        {hint && <span className="hd-label-hint ml-2 text-xs">{hint}</span>}
      </label>
      <div className="flex gap-2">
        <input
          type="password"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={stored ? `Stored: ${stored.key_prefix}` : placeholder}
          className="hd-input flex-1 text-sm"
          autoComplete="new-password"
        />
        {stored && (
          <button
            type="button"
            onClick={() => onClear(provider, onChange)}
            className="hd-btn hd-btn--muted whitespace-nowrap"
            title="Remove stored key"
          >
            Clear
          </button>
        )}
      </div>
      {stored && (
        <p className="hd-label-hint text-xs mt-1">Encrypted on server{stored.updated_at ? ` · updated ${stored.updated_at.slice(0, 10)}` : ''}</p>
      )}
    </div>
  );
}

function maskWithVisiblePrefix(value, visible = 8) {
  const s = String(value || '');
  if (!s) return '';
  const prefix = s.slice(0, Math.min(visible, s.length));
  const maskedLen = Math.max(s.length - prefix.length, 0);
  return prefix + '•'.repeat(maskedLen);
}

/**
 * Standard secret field: prefix stays readable in the box; remainder is bullets.
 * Focus shows the full value for paste/edit.
 */
function PrefixedSecretInput({
  id,
  value,
  onChange,
  placeholder,
  className,
  visiblePrefix = 8,
}) {
  const [focused, setFocused] = useState(false);
  const display = focused || !value
    ? value
    : maskWithVisiblePrefix(value, visiblePrefix);

  return (
    <input
      id={id}
      type="text"
      value={display}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      placeholder={placeholder}
      className={className}
      autoComplete="off"
      spellCheck={false}
      aria-label="Admin secret"
    />
  );
}

function Field({ label, hint, value, onChange, placeholder, type = 'text' }) {
  return (
    <div>
      <label className="hd-label">
        {label}
        {hint && <span className="hd-label-hint ml-2 text-xs">{hint}</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="hd-input text-sm"
        autoComplete="off"
        spellCheck={false}
      />
    </div>
  );
}
