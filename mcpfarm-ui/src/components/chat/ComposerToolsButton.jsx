import { ToolsIcon } from './ChatThread.jsx';

/**
 * ChatGPT-style "Tools" button that lives in the composer toolbar. Shows the
 * active binding mode (Auto vs a manual count) and opens the tool picker.
 */
export default function ComposerToolsButton({ mode, count, onClick, disabled, label }) {
  const isManual = mode === 'static' && count > 0;
  return (
    <button
      type="button"
      className={`aui-composer-btn${isManual ? ' aui-composer-btn-on' : ''}`}
      onClick={onClick}
      disabled={disabled}
      title="Select tools to bind"
    >
      <ToolsIcon />
      <span>{label || 'Tools'}</span>
      {isManual ? (
        <span className="aui-composer-badge">{count}</span>
      ) : (
        <span className="aui-composer-hint">Auto</span>
      )}
    </button>
  );
}
