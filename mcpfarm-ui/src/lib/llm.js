import { getClaudeKey } from './api.js';

const LLM_PROVIDERS = {
  ollama: {
    label: 'Ollama (Local)',
    defaultModel: import.meta.env.VITE_OLLAMA_MODEL || 'qwen3-coder:latest',
    models: ['qwen3-coder:latest', 'llama3.1:latest', 'mistral:latest', 'codellama:latest'],
    needsKey: false,
  },
  claude: {
    label: 'Claude (Anthropic)',
    defaultModel: 'claude-sonnet-4-20250514',
    models: ['claude-sonnet-4-20250514', 'claude-haiku-4-5-20251001'],
    needsKey: true,
    keyGetter: () => getClaudeKey(),
  },
  openai: {
    label: 'OpenAI',
    defaultModel: 'gpt-4o',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
    needsKey: true,
    keyGetter: () => localStorage.getItem('hd_openai_key') || '',
  },
};

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
  return localStorage.getItem('hd_ollama_url') || import.meta.env.VITE_OLLAMA_URL || 'http://localhost:11434';
}

async function callOllama(messages, tools, model, onChunk) {
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

  if (msg.tool_calls && msg.tool_calls.length > 0) {
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

  return { role: 'assistant', content };
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
  return { role: 'assistant', content: text };
}

async function callOpenAI(messages, tools, model) {
  const key = localStorage.getItem('hd_openai_key');
  if (!key) throw new Error('OpenAI API key not configured — add it in Settings');

  const openaiMessages = messages.map(m => {
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

  const body = {
    model: model || LLM_PROVIDERS.openai.defaultModel,
    messages: openaiMessages,
  };
  if (tools.length > 0) body.tools = tools.map(mcpToolToOpenAI);

  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`OpenAI ${res.status}: ${text}`);
  }

  const data = await res.json();
  const choice = data.choices[0].message;

  if (choice.tool_calls && choice.tool_calls.length > 0) {
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

  return { role: 'assistant', content: choice.content || '' };
}

export async function chatCompletion(provider, model, messages, tools, onChunk) {
  switch (provider) {
    case 'ollama': return callOllama(messages, tools, model, onChunk);
    case 'claude': return callClaude(messages, tools, model);
    case 'openai': return callOpenAI(messages, tools, model);
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
