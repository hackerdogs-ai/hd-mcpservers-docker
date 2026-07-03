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
} from '../lib/api.js';

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

  function loadVaultKeys() {
    listLlmKeys()
      .then((res) => {
        const map = {};
        (res.keys || []).forEach((k) => { map[k.provider] = k; });
        setVaultKeys(map);
      })
      .catch(() => setVaultKeys({}));
  }

  useEffect(() => {
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
    loadVaultKeys();
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
      className="hd-modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="hd-modal">
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
          <Field
            label="API Key"
            hint="Bearer token for MCP server access"
            value={apiKey}
            onChange={setApiKey}
            placeholder="hd-..."
            type="password"
          />
          <div>
            <label className="hd-label">
              Admin Secret
              <span className="hd-label-hint ml-2 text-xs">
                X-Admin-Secret header for start/stop/reload
              </span>
            </label>
            <div className="flex gap-2">
              <input
                type="password"
                value={adminSecret}
                onChange={(e) => setAdminSecret(e.target.value)}
                placeholder="admin-secret"
                className="hd-input flex-1 text-sm"
              />
              <button
                type="button"
                onClick={handleRotate}
                disabled={rotating}
                className={`hd-btn hd-btn--muted whitespace-nowrap${rotateMsg?.ok ? ' hd-text-ok' : ''}`}
              >
                {rotating ? '…' : rotateMsg?.ok ? '✓ Rotated' : '↺ Generate'}
              </button>
            </div>
            {rotateMsg && !rotateMsg.ok && (
              <p className="mt-1 text-xs hd-text-err">{rotateMsg.text}</p>
            )}
          </div>

          <SectionTitle>Chat LLM Providers</SectionTitle>
          <p className="hd-label-hint text-xs" style={{ marginTop: '-0.25rem' }}>
            Provider keys are encrypted and stored on the server. They are never saved in your browser.
          </p>

          <KeyField
            provider="claude"
            label="Claude API Key"
            hint="Prompt mode, Nova, and Chat (Claude provider)"
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
            {saving ? '…' : saved ? '✓ Saved' : 'Save'}
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
      />
    </div>
  );
}
