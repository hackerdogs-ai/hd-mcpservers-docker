import { useCallback, useMemo, useState } from 'react';
import { AssistantRuntimeProvider } from '@assistant-ui/react';
import ChatThread, { SamplePrompts } from './chat/ChatThread.jsx';
import ProviderModelBar from './chat/ProviderModelBar.jsx';
import ComposerToolsButton from './chat/ComposerToolsButton.jsx';
import ToolPickerDrawer from './chat/ToolPickerDrawer.jsx';
import { useMcpChatRuntime } from './chat/useMcpChatRuntime.js';
import { resolveDynamicBinding, resolveStaticSelection } from '../lib/toolBinding.js';

const SAMPLE_PROMPTS = [
  'Scan example.com for open ports and running services',
  'Find subdomains of example.com',
  'Check https://example.com for common web vulnerabilities',
  'Look up WHOIS and DNS records for github.com',
];

/**
 * ChatGPT-style chat page. Model selection and the tools picker live inside the
 * composer (bottom bar); the tools bound for each turn render as a Sources-style
 * footer under the assistant reply.
 */
export default function ChatMode({ servers }) {
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('');
  const [selection, setSelection] = useState({ servers: [], tools: {} });
  const [drawerOpen, setDrawerOpen] = useState(false);

  const staticCount = selection.servers.length;
  const bindingMode = staticCount ? 'static' : 'dynamic';

  const resolveBinding = useCallback(
    async (query) => {
      if (bindingMode === 'static' && selection.servers.length) {
        return resolveStaticSelection(selection);
      }
      return resolveDynamicBinding(query, { onlyRunning: true });
    },
    [bindingMode, selection],
  );

  const getProviderModel = useCallback(() => ({ provider, model }), [provider, model]);

  const runtime = useMcpChatRuntime({ resolveBinding, getProviderModel });

  const emptyState = useMemo(
    () => (
      <>
        <div className="aui-empty-title">MCP Farm Assistant</div>
        <p className="aui-empty-sub">
          {staticCount
            ? `${staticCount} server(s) bound. Ask a question.`
            : 'Ask anything. The right tools are selected automatically from all running servers.'}
        </p>
        <SamplePrompts prompts={SAMPLE_PROMPTS} />
      </>
    ),
    [staticCount],
  );

  const composerToolbar = (
    <>
      <ComposerToolsButton
        mode={bindingMode}
        count={staticCount}
        onClick={() => setDrawerOpen(true)}
      />
      <ProviderModelBar provider={provider} model={model} onProvider={setProvider} onModel={setModel} />
    </>
  );

  return (
    <div className="aui-page">
      <AssistantRuntimeProvider runtime={runtime}>
        <ChatThread
          composerToolbar={composerToolbar}
          emptyState={emptyState}
          placeholder="Message the MCP Farm assistant…"
        />
      </AssistantRuntimeProvider>
      {drawerOpen && (
        <ToolPickerDrawer
          servers={servers}
          selection={selection}
          onChange={(sel) => setSelection(sel)}
          onClose={() => setDrawerOpen(false)}
        />
      )}
    </div>
  );
}
