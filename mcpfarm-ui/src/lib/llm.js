import {
  getClaudeKey,
  getOpenAIKey,
  getOllamaUrl as getStoredOllamaUrl,
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
} from './api.js';

const DEFAULT_MODELS = {
  bedrock: [
    'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'anthropic.claude-3-haiku-20240307-v1:0',
    'amazon.nova-pro-v1:0',
    'amazon.nova-lite-v1:0',
    'meta.llama3-3-70b-instruct-v1:0',
  ],
  azure: ['gpt-4o', 'gpt-4o-mini', 'gpt-4', 'gpt-35-turbo'],
  openrouter: [
    'anthropic/claude-sonnet-4',
    'openai/gpt-4o',
    'google/gemini-2.5-pro-preview',
    'meta-llama/llama-3.3-70b-instruct',
    'x-ai/grok-3',
  ],
  grok: ['grok-3', 'grok-3-mini', 'grok-2-1212'],
  gemini: ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.0-flash'],
};

function parseModelsList(raw, fallback) {
  if (raw?.trim()) {
    const parsed = raw.split(',').map(m => m.trim()).filter(Boolean);
    if (parsed.length > 0) return parsed;
  }
  return fallback;
}

// Coerce a stringified parameter value into a JS primitive/object when possible.
// Falls back to the trimmed string so free-text args (URLs, prompts) survive intact.
function coerceParamValue(raw) {
  const v = (raw ?? '').trim();
  if (v === '') return v;
  if (v === 'true') return true;
  if (v === 'false') return false;
  if (v === 'null') return null;
  if (/^-?\d+$/.test(v)) {
    const n = Number(v);
    if (Number.isSafeInteger(n)) return n;
  }
  if (/^-?\d*\.\d+$/.test(v)) return Number(v);
  if ((v.startsWith('{') && v.endsWith('}')) || (v.startsWith('[') && v.endsWith(']'))) {
    try { return JSON.parse(v); } catch { /* keep as string */ }
  }
  return v;
}

/**
 * Fallback parser for models that emit tool calls as plain text inside the
 * message content instead of the provider's structured tool-call field.
 *
 * Handles the two most common text formats seen from Qwen / Llama / Hermes
 * style models served via Ollama, OpenRouter, Bedrock, etc.:
 *
 *   1. XML-ish:  <function=NAME><parameter=KEY>VALUE</parameter>...</function>
 *                (optionally wrapped in <tool_call>...</tool_call>)
 *   2. JSON:     <tool_call>{"name":"NAME","arguments":{...}}</tool_call>
 *
 * Returns the content with the tool-call markup stripped out, plus any
 * extracted tool calls (with stable ids so the caller can round-trip them).
 */
export function extractInlineToolCalls(content) {
  if (!content || typeof content !== 'string') {
    return { text: content || '', toolCalls: [] };
  }

  const toolCalls = [];
  let cleaned = content;

  // Format 1: <function=NAME> ... <parameter=KEY>VALUE</parameter> ... </function>
  const fnRe = /<function\s*=\s*([^>\s]+)\s*>([\s\S]*?)<\/function\s*>/gi;
  let m;
  while ((m = fnRe.exec(content)) !== null) {
    const name = m[1].trim();
    const inner = m[2] || '';
    const args = {};
    const paramRe = /<parameter\s*=\s*([^>\s]+)\s*>([\s\S]*?)<\/parameter\s*>/gi;
    let pm;
    while ((pm = paramRe.exec(inner)) !== null) {
      args[pm[1].trim()] = coerceParamValue(pm[2]);
    }
    toolCalls.push({ name, arguments: args });
    cleaned = cleaned.replace(m[0], '');
  }

  // Format 2: <tool_call>{ json }</tool_call>
  const jsonRe = /<tool_call>\s*([\s\S]*?)\s*<\/tool_call>/gi;
  while ((m = jsonRe.exec(content)) !== null) {
    const body = (m[1] || '').trim();
    if (!body || body.startsWith('<')) continue; // already handled as format 1
    try {
      const obj = JSON.parse(body);
      const name = obj.name || obj.tool || obj.function?.name;
      let rawArgs = obj.arguments ?? obj.parameters ?? obj.function?.arguments ?? {};
      if (typeof rawArgs === 'string') {
        try { rawArgs = JSON.parse(rawArgs); } catch { rawArgs = {}; }
      }
      if (name) {
        toolCalls.push({ name, arguments: rawArgs || {} });
        cleaned = cleaned.replace(m[0], '');
      }
    } catch { /* not valid JSON — leave as text */ }
  }

  // Remove any dangling wrapper tags the model left behind.
  cleaned = cleaned.replace(/<\/?tool_call\s*>/gi, '').trim();

  // Assign stable ids so assistant tool_calls and tool_results stay consistent.
  toolCalls.forEach((tc, i) => { tc.id = `call_${i}`; });

  return { text: cleaned, toolCalls };
}

/**
 * Given a raw text response with no structured tool calls, return a normalized
 * assistant message — promoting inline text tool calls to real tool calls.
 */
function finalizeTextResponse(content) {
  const { text, toolCalls } = extractInlineToolCalls(content);
  if (toolCalls.length > 0) {
    return { role: 'assistant', content: text, toolCalls };
  }
  return { role: 'assistant', content: content || '' };
}

const LLM_PROVIDERS = {
  ollama: {
    label: 'Ollama (Local)',
    defaultModel: import.meta.env.VITE_OLLAMA_MODEL || 'qwen3-coder:latest',
    models: ['qwen3-coder:latest', 'llama3.1:latest', 'mistral:latest', 'codellama:latest'],
    needsKey: false,
    toolFormat: 'ollama',
  },
  claude: {
    label: 'Claude (Anthropic)',
    defaultModel: 'claude-sonnet-4-20250514',
    models: ['claude-sonnet-4-20250514', 'claude-haiku-4-5-20251001'],
    needsKey: true,
    keyGetter: () => getClaudeKey(),
    toolFormat: 'claude',
  },
  openai: {
    label: 'OpenAI',
    defaultModel: 'gpt-4o',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
    needsKey: true,
    keyGetter: () => getOpenAIKey(),
    toolFormat: 'openai',
  },
  bedrock: {
    label: 'AWS Bedrock',
    defaultModel: 'anthropic.claude-3-5-sonnet-20241022-v2:0',
    get models() {
      return parseModelsList(getBedrockModels(), DEFAULT_MODELS.bedrock);
    },
    needsKey: true,
    keyGetter: () => getBedrockApiKey(),
    toolFormat: 'openai',
  },
  azure: {
    label: 'Azure OpenAI',
    defaultModel: 'gpt-4o',
    get models() {
      return parseModelsList(getAzureOpenAIModels(), DEFAULT_MODELS.azure);
    },
    needsKey: true,
    keyGetter: () => getAzureOpenAIKey() && getAzureOpenAIEndpoint(),
    toolFormat: 'openai',
  },
  openrouter: {
    label: 'OpenRouter',
    defaultModel: 'anthropic/claude-sonnet-4',
    get models() {
      return parseModelsList(getOpenRouterModels(), DEFAULT_MODELS.openrouter);
    },
    needsKey: true,
    keyGetter: () => getOpenRouterKey(),
    toolFormat: 'openai',
  },
  grok: {
    label: 'Grok (xAI)',
    defaultModel: 'grok-3',
    get models() {
      return parseModelsList(getGrokModels(), DEFAULT_MODELS.grok);
    },
    needsKey: true,
    keyGetter: () => getGrokKey(),
    toolFormat: 'openai',
  },
  gemini: {
    label: 'Google Gemini',
    defaultModel: 'gemini-2.5-flash',
    get models() {
      return parseModelsList(getGeminiModels(), DEFAULT_MODELS.gemini);
    },
    needsKey: true,
    keyGetter: () => getGeminiKey(),
    toolFormat: 'openai',
  },
};

export function getProviderToolFormat(provider) {
  return LLM_PROVIDERS[provider]?.toolFormat || 'openai';
}

export function getProviders() {
  return Object.entries(LLM_PROVIDERS).map(([id, p]) => ({
    id,
    label: p.label,
    models: p.models,
    defaultModel: p.defaultModel,
    needsKey: p.needsKey,
    hasKey: p.keyGetter ? !!p.keyGetter() : true,
  }));
}

/**
 * Key-independent provider catalog for the Chat surfaces. Availability is
 * resolved separately via the server-side encrypted key vault (`/llm-keys`),
 * so this never reads secrets from localStorage.
 */
export function getProviderCatalog() {
  return Object.entries(LLM_PROVIDERS).map(([id, p]) => ({
    id,
    label: p.label,
    models: p.models,
    defaultModel: p.defaultModel,
    needsKey: p.needsKey,
  }));
}

function mcpToolToOllama(tool) {
  return {
    type: 'function',
    function: {
      name: tool.name,
      description: tool.description || '',
      parameters: tool.inputSchema || { type: 'object', properties: {} },
    },
  };
}

function mcpToolToOpenAI(tool) {
  return {
    type: 'function',
    function: {
      name: tool.name,
      description: tool.description || '',
      parameters: tool.inputSchema || { type: 'object', properties: {} },
    },
  };
}

function mcpToolToClaude(tool) {
  return {
    name: tool.name,
    description: tool.description || '',
    input_schema: tool.inputSchema || { type: 'object', properties: {} },
  };
}

function getOllamaUrl() {
  return getStoredOllamaUrl() || import.meta.env.VITE_OLLAMA_URL || 'http://localhost:11434';
}

function messagesToOpenAI(messages) {
  return messages.map(m => {
    if (m.role === 'tool') {
      return { role: 'tool', tool_call_id: m.tool_call_id || 'call_0', content: m.content };
    }
    if (m.toolCalls) {
      return {
        role: 'assistant',
        content: m.content || null,
        tool_calls: m.toolCalls.map((tc, i) => ({
          id: tc.id || `call_${i}`,
          type: 'function',
          function: { name: tc.name, arguments: JSON.stringify(tc.arguments || {}) },
        })),
      };
    }
    return { role: m.role, content: m.content };
  });
}

function parseOpenAIResponse(data, label) {
  const choice = data.choices?.[0]?.message;
  if (!choice) throw new Error(`${label}: empty response`);

  if (choice.tool_calls?.length > 0) {
    return {
      role: 'assistant',
      content: choice.content || '',
      toolCalls: choice.tool_calls.map(tc => ({
        id: tc.id,
        name: tc.function.name,
        arguments: JSON.parse(tc.function.arguments || '{}'),
      })),
    };
  }

  // Fallback: some models emit tool calls as text in `content` instead of
  // populating `tool_calls`. Promote those so the agent loop can execute them.
  return finalizeTextResponse(choice.content || '');
}

async function callOllama(messages, tools, model) {
  const ollamaUrl = getOllamaUrl();
  const body = {
    model: model || LLM_PROVIDERS.ollama.defaultModel,
    messages,
    stream: false,
  };
  if (tools.length > 0) {
    body.tools = tools.map(mcpToolToOllama);
  }

  const res = await fetch(`${ollamaUrl}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Ollama ${res.status}: ${text}`);
  }

  const data = await res.json();
  const msg = data.message;

  if (msg.tool_calls?.length > 0) {
    return {
      role: 'assistant',
      content: msg.content || '',
      toolCalls: msg.tool_calls.map(tc => ({
        name: tc.function.name,
        arguments: tc.function.arguments || {},
      })),
    };
  }

  let content = msg.content || '';
  if (content.includes('<think>')) {
    content = content.replace(/<think>[\s\S]*?<\/think>\s*/g, '').trim();
  }

  // Fallback for models (e.g. qwen, llama) that write tool calls as text.
  return finalizeTextResponse(content);
}

async function callClaude(messages, tools, model) {
  const key = getClaudeKey();
  if (!key) throw new Error('Claude API key not configured — add it in Settings');

  const claudeMessages = messages
    .filter(m => m.role !== 'system')
    .map(m => {
      if (m.role === 'tool') {
        return {
          role: 'user',
          content: [{ type: 'tool_result', tool_use_id: m.tool_use_id || 'call_0', content: m.content }],
        };
      }
      if (m.toolCalls) {
        const content = [];
        if (m.content) content.push({ type: 'text', text: m.content });
        m.toolCalls.forEach((tc, i) => {
          content.push({
            type: 'tool_use',
            id: tc.id || `call_${i}`,
            name: tc.name,
            input: tc.arguments || {},
          });
        });
        return { role: 'assistant', content };
      }
      return { role: m.role, content: m.content };
    });

  const systemMsg = messages.find(m => m.role === 'system');

  const body = {
    model: model || LLM_PROVIDERS.claude.defaultModel,
    max_tokens: 4096,
    messages: claudeMessages,
  };
  if (systemMsg) body.system = systemMsg.content;
  if (tools.length > 0) body.tools = tools.map(mcpToolToClaude);

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Claude ${res.status}: ${text}`);
  }

  const data = await res.json();

  const toolUseBlocks = data.content.filter(b => b.type === 'tool_use');
  if (toolUseBlocks.length > 0) {
    const textParts = data.content.filter(b => b.type === 'text').map(b => b.text).join('\n');
    return {
      role: 'assistant',
      content: textParts,
      toolCalls: toolUseBlocks.map(b => ({
        id: b.id,
        name: b.name,
        arguments: b.input || {},
      })),
    };
  }

  const text = data.content.map(b => b.text || '').join('\n');
  // Fallback in case a Claude-compatible endpoint returns a text tool call.
  return finalizeTextResponse(text);
}

async function callOpenAICompatible(url, headers, messages, tools, model, defaultModel, label) {
  const body = {
    model: model || defaultModel,
    messages: messagesToOpenAI(messages),
  };
  if (tools.length > 0) body.tools = tools.map(mcpToolToOpenAI);

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${label} ${res.status}: ${text}`);
  }

  return parseOpenAIResponse(await res.json(), label);
}

async function callOpenAI(messages, tools, model) {
  const key = getOpenAIKey();
  if (!key) throw new Error('OpenAI API key not configured — add it in Settings');

  return callOpenAICompatible(
    'https://api.openai.com/v1/chat/completions',
    { Authorization: `Bearer ${key}` },
    messages,
    tools,
    model,
    LLM_PROVIDERS.openai.defaultModel,
    'OpenAI',
  );
}

async function callBedrock(messages, tools, model) {
  const key = getBedrockApiKey();
  if (!key) throw new Error('AWS Bedrock API key not configured — add it in Settings');

  const region = getBedrockRegion();
  return callOpenAICompatible(
    `https://bedrock-runtime.${region}.amazonaws.com/openai/v1/chat/completions`,
    { Authorization: `Bearer ${key}` },
    messages,
    tools,
    model,
    LLM_PROVIDERS.bedrock.defaultModel,
    'AWS Bedrock',
  );
}

async function callAzure(messages, tools, model) {
  const key = getAzureOpenAIKey();
  const endpoint = getAzureOpenAIEndpoint().replace(/\/$/, '');
  if (!key || !endpoint) {
    throw new Error('Azure OpenAI key and endpoint not configured — add them in Settings');
  }

  const deployment = model || LLM_PROVIDERS.azure.defaultModel;
  const apiVersion = '2024-08-01-preview';

  return callOpenAICompatible(
    `${endpoint}/openai/deployments/${encodeURIComponent(deployment)}/chat/completions?api-version=${apiVersion}`,
    { 'api-key': key },
    messages,
    tools,
    deployment,
    LLM_PROVIDERS.azure.defaultModel,
    'Azure OpenAI',
  );
}

async function callOpenRouter(messages, tools, model) {
  const key = getOpenRouterKey();
  if (!key) throw new Error('OpenRouter API key not configured — add it in Settings');

  return callOpenAICompatible(
    'https://openrouter.ai/api/v1/chat/completions',
    {
      Authorization: `Bearer ${key}`,
      'HTTP-Referer': window.location.origin,
      'X-Title': 'Hackerdogs MCP Farm',
    },
    messages,
    tools,
    model,
    LLM_PROVIDERS.openrouter.defaultModel,
    'OpenRouter',
  );
}

async function callGrok(messages, tools, model) {
  const key = getGrokKey();
  if (!key) throw new Error('Grok API key not configured — add it in Settings');

  return callOpenAICompatible(
    'https://api.x.ai/v1/chat/completions',
    { Authorization: `Bearer ${key}` },
    messages,
    tools,
    model,
    LLM_PROVIDERS.grok.defaultModel,
    'Grok',
  );
}

async function callGemini(messages, tools, model) {
  const key = getGeminiKey();
  if (!key) throw new Error('Google Gemini API key not configured — add it in Settings');

  return callOpenAICompatible(
    'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
    { Authorization: `Bearer ${key}` },
    messages,
    tools,
    model,
    LLM_PROVIDERS.gemini.defaultModel,
    'Google Gemini',
  );
}

export async function chatCompletion(provider, model, messages, tools) {
  switch (provider) {
    case 'ollama': return callOllama(messages, tools, model);
    case 'claude': return callClaude(messages, tools, model);
    case 'openai': return callOpenAI(messages, tools, model);
    case 'bedrock': return callBedrock(messages, tools, model);
    case 'azure': return callAzure(messages, tools, model);
    case 'openrouter': return callOpenRouter(messages, tools, model);
    case 'grok': return callGrok(messages, tools, model);
    case 'gemini': return callGemini(messages, tools, model);
    default: throw new Error(`Unknown provider: ${provider}`);
  }
}

export async function fetchOllamaModels() {
  try {
    const url = getOllamaUrl();
    const res = await fetch(`${url}/api/tags`);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.models || []).map(m => m.name);
  } catch {
    return [];
  }
}
