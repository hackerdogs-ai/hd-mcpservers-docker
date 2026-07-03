import { useCallback, useMemo, useState } from 'react';
import { AssistantRuntimeProvider } from '@assistant-ui/react';
import ChatThread, { SamplePrompts } from './chat/ChatThread.jsx';
import ProviderModelBar from './chat/ProviderModelBar.jsx';
import { useMcpChatRuntime } from './chat/useMcpChatRuntime.js';
import { toStaticBinding } from '../lib/toolBinding.js';
import { mcpClient } from '../lib/mcp.js';
import { getToolHints } from '../lib/toolHints.js';

function getSamplePrompts(serverName, tools) {
  const hints = getToolHints(tools[0]?.name);
  const prompts = [];
  const base = serverName.replace(/-mcp$/, '');

  if (hints?.examples) {
    hints.examples.forEach((ex) => prompts.push(`Run ${tools[0].name} with: ${ex.value}`));
  }
  if (tools.length > 0) {
    prompts.push(`What tools are available on ${base} and what do they do?`);
  }

  const toolSpecific = {
    nmap: 'Scan example.com for open ports and services',
    whois: 'Look up WHOIS information for github.com',
    nuclei: 'Run a vulnerability scan on https://example.com',
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
  const matchKey = Object.keys(toolSpecific).find((k) => base.includes(k));
  if (matchKey) prompts.unshift(toolSpecific[matchKey]);

  return prompts.slice(0, 4);
}

/**
 * Per-server chat, reimplemented on assistant-ui with a fixed single-server
 * static binding. Same runtime/orchestrator as the Chat page for a consistent
 * UX (streaming, tool cards, edit/regenerate, cancel).
 */
export default function ChatTab({ serverName, tools: existingTools, isRunning, onLoadTools }) {
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('');
  const [tools, setTools] = useState(existingTools || []);
  const [toolsDiscovered, setToolsDiscovered] = useState((existingTools?.length || 0) > 0);
  const [discovering, setDiscovering] = useState(false);

  const resolveBinding = useCallback(async () => {
    let list = tools;
    if (!list.length) {
      try {
        list = await mcpClient.listTools(serverName);
        setTools(list);
        setToolsDiscovered(true);
        onLoadTools?.(list);
      } catch {
        list = [];
      }
    }
    return toStaticBinding(serverName, list);
  }, [serverName, tools, onLoadTools]);

  const getProviderModel = useCallback(() => ({ provider, model }), [provider, model]);

  const system = useMemo(
    () => `You are a cybersecurity assistant with access to the ${serverName} MCP server tools. `
      + 'Use the available tools to help with security tasks. When a tool returns results, analyze and explain them clearly. Be concise and technical.',
    [serverName],
  );

  const runtime = useMcpChatRuntime({ resolveBinding, getProviderModel, system });

  async function discoverTools() {
    setDiscovering(true);
    try {
      mcpClient.resetSession(serverName);
      const t = await mcpClient.listTools(serverName);
      setTools(t);
      setToolsDiscovered(true);
      onLoadTools?.(t);
    } catch {
      /* surfaced on next send */
    } finally {
      setDiscovering(false);
    }
  }

  const samplePrompts = tools.length > 0 ? getSamplePrompts(serverName, tools) : [];

  const composerToolbar = (
    <>
      <button
        type="button"
        className="aui-composer-btn"
        onClick={discoverTools}
        disabled={discovering || !isRunning}
        title="Reload this server's tools"
      >
        {discovering ? 'Discovering…' : toolsDiscovered ? `Tools · ${tools.length}` : 'Discover tools'}
      </button>
      <ProviderModelBar provider={provider} model={model} onProvider={setProvider} onModel={setModel} />
    </>
  );

  const emptyState = (
    <>
      <div className="aui-empty-title">Chat with {serverName.replace(/-mcp$/, '')}</div>
      <p className="aui-empty-sub">
        {!isRunning
          ? 'Server is stopped. Start it to use chat.'
          : !toolsDiscovered
            ? 'Ask a question — tools load automatically on your first message.'
            : `${tools.length} tools loaded. Ask a question or pick a sample prompt.`}
      </p>
      {isRunning && <SamplePrompts prompts={samplePrompts} />}
    </>
  );

  return (
    <div className="aui-page aui-page-embedded">
      <AssistantRuntimeProvider runtime={runtime}>
        <ChatThread
          composerToolbar={composerToolbar}
          emptyState={emptyState}
          disabled={!isRunning}
          placeholder={isRunning ? 'Ask a question or describe a task…' : 'Server is stopped…'}
        />
      </AssistantRuntimeProvider>
    </div>
  );
}
