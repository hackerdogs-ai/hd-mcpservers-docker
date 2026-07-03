import { useState } from 'react';
import { decodeToolCallId } from '../../lib/toolBinding.js';
import { mcpResultToText } from '../../lib/chatOrchestrator.js';

/**
 * Tool UI card rendered for every MCP tool call in an assistant message.
 * Wired as the `tools.Fallback` component of MessagePrimitive.Parts, so it
 * receives the tool-call part: { toolCallId, toolName, args, result, isError }.
 */
export default function McpToolCard({ toolCallId, toolName, args, result, isError }) {
  const [open, setOpen] = useState(false);
  const { server } = decodeToolCallId(toolCallId);
  const pending = result === undefined || result === null;
  const state = pending ? 'running' : isError ? 'error' : 'done';

  const resultText = pending ? '' : mcpResultToText(result);

  return (
    <div className={`aui-tool-card aui-tool-${state}`}>
      <button type="button" className="aui-tool-head" onClick={() => setOpen((v) => !v)}>
        <span className={`aui-tool-dot aui-tool-dot-${state}`} aria-hidden />
        <span className="aui-tool-name">
          {server ? <span className="aui-tool-server">{server.replace(/-mcp$/, '')}</span> : null}
          <span className="aui-tool-fn">{toolName}</span>
        </span>
        <span className="aui-tool-state">
          {state === 'running' ? 'running…' : state === 'error' ? 'error' : 'done'}
        </span>
        <span className="aui-tool-caret">{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div className="aui-tool-body">
          <div className="aui-tool-section-label">Arguments</div>
          <pre className="aui-tool-pre">{JSON.stringify(args || {}, null, 2)}</pre>
          {!pending && (
            <>
              <div className="aui-tool-section-label">Result</div>
              <pre className="aui-tool-pre">{resultText || '(empty)'}</pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}
