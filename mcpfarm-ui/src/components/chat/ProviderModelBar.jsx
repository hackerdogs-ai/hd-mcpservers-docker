import { useEffect, useState } from 'react';
import { getProviderCatalog, fetchOllamaModels } from '../../lib/llm.js';
import { listLlmKeys } from '../../lib/api.js';

/**
 * Provider + model selectors shared by both chat surfaces. Availability is
 * resolved from the server-side encrypted key vault (never localStorage).
 */
export default function ProviderModelBar({ provider, model, onProvider, onModel }) {
  const catalog = getProviderCatalog();
  const [configured, setConfigured] = useState(null); // Set of providers with keys
  const [ollamaModels, setOllamaModels] = useState([]);

  useEffect(() => {
    listLlmKeys()
      .then((res) => setConfigured(new Set((res.keys || []).map((k) => k.provider))))
      .catch(() => setConfigured(new Set()));
  }, []);

  useEffect(() => {
    if (provider === 'ollama') {
      fetchOllamaModels().then((m) => { if (m.length) setOllamaModels(m); });
    }
  }, [provider]);

  const current = catalog.find((p) => p.id === provider);
  const modelOptions = provider === 'ollama' && ollamaModels.length
    ? ollamaModels
    : current?.models || [];

  function hasKey(p) {
    if (!p.needsKey) return true;
    if (configured === null) return true; // unknown yet — don't discourage
    return configured.has(p.id);
  }

  return (
    <div className="aui-model-controls">
      <select
        className="aui-model-select"
        value={provider}
        onChange={(e) => { onProvider(e.target.value); onModel(''); }}
        title="LLM provider"
        aria-label="LLM provider"
      >
        {catalog.map((p) => (
          <option key={p.id} value={p.id}>
            {p.label}{p.needsKey && !hasKey(p) ? ' · no key' : ''}
          </option>
        ))}
      </select>
      {modelOptions.length > 0 && (
        <select
          className="aui-model-select"
          value={model || current?.defaultModel || ''}
          onChange={(e) => onModel(e.target.value)}
          title="Model"
          aria-label="Model"
        >
          {modelOptions.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      )}
    </div>
  );
}
