import React, { useState, useEffect, useRef, useCallback } from 'react';
import { mcpClient } from '../lib/mcp.js';
import { getToolHints } from '../lib/toolHints.js';
import { getProviders, chatCompletion, fetchOllamaModels } from '../lib/llm.js';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MAX_TOOL_ROUNDS = 10;

function getSamplePrompts(serverName, tools) {
  const hints = getToolHints(tools[0]?.name);
  const prompts = [];
  const base = serverName.replace(/-mcp$/, '');

  if (hints?.examples) {
    hints.examples.forEach(ex => {
      prompts.push(`Run ${tools[0].name} with: ${ex.value}`);
    });
  }

  if (tools.length > 0) {
    prompts.push(`What tools are available on ${base} and what do they do?`);
  }

  const toolSpecific = {
    nmap: 'Scan example.com for open ports and services',
    whois: 'Look up WHOIS information for github.com',
    nuclei: 'Run a vulnerability scan on https://example.com',
    semgrep: 'Check this code for security issues: def login(user, pw): query = f"SELECT * FROM users WHERE user=\'{user}\' AND pw=\'{pw}\'"',
    sqlmap: 'Test https://example.com/page?id=1 for SQL injection',
    shodan: 'Search Shodan for exposed MongoDB instances',
    gobuster: 'Enumerate directories on https://example.com',
    ffuf: 'Fuzz https://example.com/FUZZ for hidden paths',
    gitleaks: 'Check a repository for leaked secrets',
    nikto: 'Run a web server scan on https://example.com',
    subfinder: 'Find subdomains of example.com',
    amass: 'Enumerate subdomains for example.com',
    httpx: 'Probe a list of domains for live HTTP services',
    dnsx: 'Resolve DNS records for example.com',
    katana: 'Crawl https://example.com and extract URLs',
    trivy: 'Scan the nginx:latest Docker image for vulnerabilities',
    grype: 'Scan a container image for CVEs',
  };

  const matchKey = Object.keys(toolSpecific).find(k => base.includes(k));
  if (matchKey) {
    prompts.unshift(toolSpecific[matchKey]);
  }

  return prompts.slice(0, 4);
}

function ChatMessage({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="chat-msg chat-msg--user">
        <div className="chat-msg-label">You</div>
        <div className="chat-msg-body">{msg.content}</div>
      </div>
    );
  }

  if (msg.role === 'tool-call') {
    return (
      <div className="chat-msg chat-msg--tool">
        <div className="chat-msg-label">Tool Call</div>
        <div className="chat-msg-body chat-tool-call">
          <span className="chat-tool-name">{msg.name}</span>
          <pre className="chat-tool-args">{JSON.stringify(msg.arguments, null, 2)}</pre>
        </div>
      </div>
    );
  }

  if (msg.role === 'tool-result') {
    return (
      <div className="chat-msg chat-msg--tool">
        <div className="chat-msg-label">Tool Result</div>
        <pre className="chat-msg-body chat-tool-result">{msg.content}</pre>
      </div>
    );
  }

  if (msg.role === 'assistant') {
    return (
      <div className="chat-msg chat-msg--assistant">
        <div className="chat-msg-label">Assistant</div>
        <div className="chat-msg-body chat-md">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
        </div>
      </div>
    );
  }

  if (msg.role === 'error') {
    return (
      <div className="chat-msg chat-msg--error">
        <div className="chat-msg-label">Error</div>
        <div className="chat-msg-body">{msg.content}</div>
      </div>
    );
  }

  return null;
}

export default function ChatTab({ serverName, tools: existingTools, isRunning, onLoadTools }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [tools, setTools] = useState(existingTools || []);
  const [toolsDiscovered, setToolsDiscovered] = useState(existingTools?.length > 0);
  const [discovering, setDiscovering] = useState(false);

  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('');
  const [ollamaModels, setOllamaModels] = useState([]);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const providers = getProviders();

  useEffect(() => {
    if (existingTools?.length > 0) {
      setTools(existingTools);
      setToolsDiscovered(true);
    }
  }, [existingTools]);

  useEffect(() => {
    const p = providers.find(p => p.id === provider);
    if (p && !model) setModel(p.defaultModel);
  }, [provider]);

  useEffect(() => {
    if (provider === 'ollama') {
      fetchOllamaModels().then(models => {
        if (models.length > 0) setOllamaModels(models);
      });
    }
  }, [provider]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const samplePrompts = tools.length > 0 ? getSamplePrompts(serverName, tools) : [];

  async function discoverTools() {
    setDiscovering(true);
    try {
      mcpClient.resetSession(serverName);
      const t = await mcpClient.listTools(serverName);
      setTools(t);
      setToolsDiscovered(true);
      onLoadTools?.(t);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Discovered **${t.length} tools** on ${serverName}:\n\n${t.map(tool => `- **${tool.name}**: ${tool.description || 'No description'}`).join('\n')}`,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: `Tool discovery failed: ${err.message}`,
      }]);
    } finally {
      setDiscovering(false);
    }
  }

  function formatToolResult(result) {
    if (!result) return 'No output';
    if (typeof result === 'string') return result;
    if (result.content && Array.isArray(result.content)) {
      return result.content.map(c => {
        if (c.type === 'text') return c.text;
        if (c.type === 'image') return `[image: ${c.mimeType}]`;
        return JSON.stringify(c);
      }).join('\n');
    }
    if (result.isError && result.content) return formatToolResult({ content: result.content });
    return JSON.stringify(result, null, 2);
  }

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || loading) return;

    const userMsg = { role: 'user', content: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const systemPrompt = {
        role: 'system',
        content: `You are a cybersecurity assistant with access to the ${serverName} MCP server tools. Use the available tools to help the user with their security tasks. When a tool returns results, analyze and explain them clearly. Be concise and technical.`,
      };

      const conversationHistory = [...messages, userMsg];
      let llmMessages = [systemPrompt, ...conversationHistory.filter(m =>
        m.role === 'user' || m.role === 'assistant' || m.role === 'tool'
      )];

      let rounds = 0;
      while (rounds < MAX_TOOL_ROUNDS) {
        rounds++;
        const response = await chatCompletion(provider, model, llmMessages, tools);

        if (response.toolCalls && response.toolCalls.length > 0) {
          if (response.content) {
            setMessages(prev => [...prev, { role: 'assistant', content: response.content }]);
          }

          for (const tc of response.toolCalls) {
            setMessages(prev => [...prev, {
              role: 'tool-call',
              name: tc.name,
              arguments: tc.arguments,
            }]);

            let toolResult;
            try {
              const raw = await mcpClient.callTool(serverName, tc.name, tc.arguments);
              toolResult = formatToolResult(raw);
            } catch (err) {
              toolResult = `Tool error: ${err.message}`;
            }

            setMessages(prev => [...prev, {
              role: 'tool-result',
              content: toolResult,
            }]);

            const assistantWithCalls = {
              role: 'assistant',
              content: response.content || '',
              toolCalls: response.toolCalls,
            };

            if (provider === 'claude') {
              llmMessages.push(assistantWithCalls);
              llmMessages.push({
                role: 'tool',
                tool_use_id: tc.id || 'call_0',
                content: toolResult,
              });
            } else if (provider === 'openai') {
              if (!llmMessages.find(m => m === assistantWithCalls)) {
                llmMessages.push(assistantWithCalls);
              }
              llmMessages.push({
                role: 'tool',
                tool_call_id: tc.id || 'call_0',
                content: toolResult,
              });
            } else {
              llmMessages.push({ role: 'assistant', content: response.content || '', toolCalls: response.toolCalls });
              llmMessages.push({ role: 'tool', content: toolResult });
            }
          }
          continue;
        }

        setMessages(prev => [...prev, { role: 'assistant', content: response.content }]);
        break;
      }

      if (rounds >= MAX_TOOL_ROUNDS) {
        setMessages(prev => [...prev, {
          role: 'error',
          content: `Reached maximum tool call rounds (${MAX_TOOL_ROUNDS}). The LLM may be stuck in a loop.`,
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: err.message,
      }]);
    } finally {
      setLoading(false);
    }
  }, [loading, messages, provider, model, tools, serverName]);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  const currentProvider = providers.find(p => p.id === provider);
  const modelOptions = provider === 'ollama' && ollamaModels.length > 0
    ? ollamaModels
    : currentProvider?.models || [];

  return (
    <div className="chat-tab">
      {/* Provider bar */}
      <div className="chat-provider-bar">
        <div className="chat-provider-group">
          <label className="chat-provider-label">LLM</label>
          <select
            value={provider}
            onChange={e => { setProvider(e.target.value); setModel(''); }}
            className="chat-select"
          >
            {providers.map(p => (
              <option key={p.id} value={p.id}>
                {p.label}{p.needsKey && !p.hasKey ? ' (no key)' : ''}
              </option>
            ))}
          </select>
        </div>
        <div className="chat-provider-group">
          <label className="chat-provider-label">Model</label>
          <select
            value={model}
            onChange={e => setModel(e.target.value)}
            className="chat-select"
          >
            {modelOptions.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div className="chat-provider-group">
          <button
            onClick={discoverTools}
            disabled={discovering || !isRunning}
            className="sd-btn sd-btn--primary chat-discover-btn"
          >
            {discovering ? 'Discovering...' : toolsDiscovered ? `⚡ ${tools.length} Tools` : '🔍 Discover Tools'}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-title">Chat with {serverName.replace(/-mcp$/, '')}</div>
            <p className="chat-empty-hint">
              {!isRunning
                ? 'Server is stopped. Start it to use chat.'
                : !toolsDiscovered
                  ? 'Click "Discover Tools" to load available MCP tools, then ask a question.'
                  : `${tools.length} tools loaded. Ask a question or pick a sample prompt below.`}
            </p>
            {toolsDiscovered && samplePrompts.length > 0 && (
              <div className="chat-samples">
                {samplePrompts.map((p, i) => (
                  <button
                    key={i}
                    className="chat-sample-btn"
                    onClick={() => { setInput(p); inputRef.current?.focus(); }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} msg={msg} />
        ))}

        {loading && (
          <div className="chat-msg chat-msg--assistant">
            <div className="chat-msg-label">Assistant</div>
            <div className="chat-msg-body chat-thinking">
              <span className="chat-dot" />
              <span className="chat-dot" />
              <span className="chat-dot" />
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="chat-input-bar">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={toolsDiscovered ? 'Ask a question or describe a task...' : 'Discover tools first...'}
          disabled={loading || !isRunning}
          className="chat-input"
          rows={1}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={loading || !input.trim() || !isRunning}
          className="chat-send-btn"
        >
          {loading ? '...' : '↑'}
        </button>
      </div>
    </div>
  );
}
