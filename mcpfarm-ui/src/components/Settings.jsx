import React, { useState, useEffect } from 'react';
import {
  getBaseUrl,
  getApiKey,
  getAdminSecret,
  getClaudeKey,
  getOpenAIKey,
  getOllamaUrl,
  getHeygenKey,
  getHeygenAvatarId,
  getBedrockApiKey,
  getBedrockRegion,
  getBedrockModels,
  getAzureOpenAIKey,
  getAzureOpenAIEndpoint,
  getAzureOpenAIModels,
  getOpenRouterKey,
  getOpenRouterModels,
  getGrokKey,
  getGrokModels,
  getGeminiKey,
  getGeminiModels,
  saveSettings,
  rotateSecret,
} from '../lib/api.js';

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
  const [rotating, setRotating] = useState(false);
  const [rotateMsg, setRotateMsg] = useState(null);

  useEffect(() => {
    setBaseUrl(getBaseUrl());
    setApiKey(getApiKey());
    setAdminSecret(getAdminSecret());
    setClaudeKey(getClaudeKey());
    setOpenaiKey(getOpenAIKey());
    setOllamaUrl(getOllamaUrl());
    setHeygenKey(getHeygenKey());
    setHeygenAvatarId(getHeygenAvatarId());
    setBedrockApiKey(getBedrockApiKey());
    setBedrockRegion(getBedrockRegion());
    setBedrockModels(getBedrockModels());
    setAzureOpenaiKey(getAzureOpenAIKey());
    setAzureOpenaiEndpoint(getAzureOpenAIEndpoint());
    setAzureOpenaiModels(getAzureOpenAIModels());
    setOpenrouterKey(getOpenRouterKey());
    setOpenrouterModels(getOpenRouterModels());
    setGrokKey(getGrokKey());
    setGrokModels(getGrokModels());
    setGeminiKey(getGeminiKey());
    setGeminiModels(getGeminiModels());
  }, []);

  function handleSave() {
    saveSettings({
      baseUrl,
      apiKey,
      adminSecret,
      claudeKey,
      openaiKey,
      ollamaUrl,
      heygenKey,
      heygenAvatarId,
      bedrockApiKey,
      bedrockRegion,
      bedrockModels,
      azureOpenaiKey,
      azureOpenaiEndpoint,
      azureOpenaiModels,
      openrouterKey,
      openrouterModels,
      grokKey,
      grokModels,
      geminiKey,
      geminiModels,
    });
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

          <Field
            label="Claude API Key"
            hint="Prompt mode, Nova, and Chat (Claude provider)"
            value={claudeKey}
            onChange={setClaudeKey}
            placeholder="sk-ant-..."
            type="password"
          />
          <Field
            label="OpenAI API Key"
            hint="Chat tab (OpenAI provider)"
            value={openaiKey}
            onChange={setOpenaiKey}
            placeholder="sk-..."
            type="password"
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
          <Field
            label="Bedrock API Key"
            hint="Bedrock API key for Chat tab"
            value={bedrockApiKey}
            onChange={setBedrockApiKey}
            placeholder="bedrock-api-key-..."
            type="password"
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
          <Field
            label="Azure OpenAI API Key"
            hint="Chat tab (Azure provider)"
            value={azureOpenaiKey}
            onChange={setAzureOpenaiKey}
            placeholder="azure-api-key"
            type="password"
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
          <Field
            label="OpenRouter API Key"
            hint="Chat tab (OpenRouter provider)"
            value={openrouterKey}
            onChange={setOpenrouterKey}
            placeholder="sk-or-..."
            type="password"
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
          <Field
            label="Grok API Key"
            hint="Chat tab (Grok provider)"
            value={grokKey}
            onChange={setGrokKey}
            placeholder="xai-..."
            type="password"
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
          <Field
            label="Gemini API Key"
            hint="Chat tab (Gemini provider)"
            value={geminiKey}
            onChange={setGeminiKey}
            placeholder="AIza..."
            type="password"
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
          <button type="button" onClick={onClose} className="hd-btn hd-btn--ghost">
            Cancel
          </button>
          <button type="button" onClick={handleSave} className="hd-btn hd-btn--primary">
            {saved ? '✓ Saved' : 'Save'}
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
