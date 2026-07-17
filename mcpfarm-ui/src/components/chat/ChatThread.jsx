import {
  ActionBarPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useMessage,
} from '@assistant-ui/react';
import { MarkdownTextPrimitive } from '@assistant-ui/react-markdown';
import remarkGfm from 'remark-gfm';
import McpToolCard from './McpToolCard.jsx';

function MarkdownText() {
  return <MarkdownTextPrimitive remarkPlugins={[remarkGfm]} className="aui-md" />;
}

/**
 * Rendered by assistant-ui whenever the assistant message has no visible part
 * yet but the run is in progress — i.e. while we resolve tools / wait on the
 * model, and between a tool call and the model's next reply. This is the
 * loading indicator the runtime surfaces "for free".
 */
function LoadingIndicator() {
  return (
    <div className="aui-loading" role="status" aria-label="Assistant is working">
      <span className="aui-loading-dot" />
      <span className="aui-loading-dot" />
      <span className="aui-loading-dot" />
    </div>
  );
}

const PARTS_COMPONENTS = {
  Empty: LoadingIndicator,
  Text: MarkdownText,
  tools: { Fallback: McpToolCard },
};

/**
 * Sources-style footer rendered at the bottom of an assistant message. Lists
 * the tools that were bound for that turn (dynamic auto-selection or manual),
 * mirroring how assistant-ui / ChatGPT surface "Sources".
 */
function MessageTools() {
  const binding = useMessage((m) => m.metadata?.custom?.binding);
  const tools = binding?.tools || [];
  if (!tools.length) return null;
  const label = binding.mode === 'dynamic' ? 'Auto-selected tools' : 'Bound tools';
  return (
    <div className="aui-sources">
      <div className="aui-sources-head">
        <ToolsIcon />
        <span className="aui-sources-label">{label}</span>
        <span className="aui-sources-count">{tools.length}</span>
      </div>
      <div className="aui-sources-list">
        {tools.map((t) => (
          <span key={`${t.server}::${t.name}`} className="aui-source" title={t.description || ''}>
            <span className="aui-source-server">{(t.server || '').replace(/-mcp$/, '')}</span>
            <span className="aui-source-tool">{t.name}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="aui-msg aui-msg-user">
      <div className="aui-bubble aui-bubble-user">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="aui-msg aui-msg-assistant">
      <div className="aui-bubble aui-bubble-assistant">
        <MessagePrimitive.Parts components={PARTS_COMPONENTS} />
        <MessageTools />
      </div>
      <ActionBarPrimitive.Root className="aui-actionbar" autohide="not-last" autohideFloat="single-branch">
        <ActionBarPrimitive.Copy className="aui-action-btn">Copy</ActionBarPrimitive.Copy>
        <ActionBarPrimitive.Reload className="aui-action-btn">Regenerate</ActionBarPrimitive.Reload>
      </ActionBarPrimitive.Root>
    </MessagePrimitive.Root>
  );
}

const MESSAGE_COMPONENTS = {
  UserMessage,
  AssistantMessage,
};

/**
 * ChatGPT-style composer: an input surface with a bottom toolbar that hosts the
 * tools button and model/provider controls (passed via `toolbar`), plus send.
 */
function Composer({ disabled, placeholder, toolbar }) {
  return (
    <ComposerPrimitive.Root className="aui-composer">
      <ComposerPrimitive.Input
        className="aui-input"
        placeholder={placeholder || 'Ask anything…'}
        disabled={disabled}
        autoFocus
        rows={1}
      />
      <div className="aui-composer-toolbar">
        <div className="aui-composer-tools">{toolbar}</div>
        <div className="aui-composer-actions">
          <ThreadPrimitive.If running={false}>
            <ComposerPrimitive.Send className="aui-send" disabled={disabled} aria-label="Send">
              <SendIcon />
            </ComposerPrimitive.Send>
          </ThreadPrimitive.If>
          <ThreadPrimitive.If running>
            <ComposerPrimitive.Cancel className="aui-cancel" aria-label="Stop">
              <StopIcon />
            </ComposerPrimitive.Cancel>
          </ThreadPrimitive.If>
        </div>
      </div>
    </ComposerPrimitive.Root>
  );
}

/**
 * Shared thread surface used by both the Chat page and the per-server Chat tab.
 * Must be rendered inside an <AssistantRuntimeProvider>.
 */
export default function ChatThread({ disabled, placeholder, emptyState, composerToolbar }) {
  return (
    <ThreadPrimitive.Root className="aui-thread">
      <ThreadPrimitive.Viewport className="aui-viewport">
        <ThreadPrimitive.Empty>
          <div className="aui-empty">{emptyState}</div>
        </ThreadPrimitive.Empty>
        <ThreadPrimitive.Messages components={MESSAGE_COMPONENTS} />
        <div className="aui-viewport-spacer" />
      </ThreadPrimitive.Viewport>
      <div className="aui-composer-wrap">
        <Composer disabled={disabled} placeholder={placeholder} toolbar={composerToolbar} />
      </div>
    </ThreadPrimitive.Root>
  );
}

/** Convenience: clickable sample prompts for empty states. */
export function SamplePrompts({ prompts = [] }) {
  if (!prompts.length) return null;
  return (
    <div className="aui-suggestions">
      {prompts.map((p) => (
        <ThreadPrimitive.Suggestion
          key={p}
          className="aui-suggestion"
          prompt={p}
          method="replace"
        >
          {p}
        </ThreadPrimitive.Suggestion>
      ))}
    </div>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 19V5M12 5l-6 6M12 5l6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function StopIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </svg>
  );
}

export function ToolsIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
