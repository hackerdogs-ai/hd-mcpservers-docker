import React, { useState } from 'react';
import { classifyToolResultContent } from '../lib/toolResult.js';

function JsonPrimitive({ value }) {
  if (value === null) return <span className="json-null">null</span>;
  if (typeof value === 'boolean') return <span className="json-boolean">{String(value)}</span>;
  if (typeof value === 'number') return <span className="json-number">{value}</span>;
  return <span className="json-string">&quot;{value}&quot;</span>;
}

function JsonNode({ name, value, depth = 0 }) {
  const [open, setOpen] = useState(depth < 2);

  if (value === null || typeof value !== 'object') {
    return (
      <div className="json-line">
        {name !== undefined && <span className="json-key">{name}: </span>}
        <JsonPrimitive value={value} />
      </div>
    );
  }

  const isArray = Array.isArray(value);
  const entries = isArray ? value.entries() : Object.entries(value);
  const entryList = [...entries];
  const openBracket = isArray ? '[' : '{';
  const closeBracket = isArray ? ']' : '}';
  const preview = isArray ? `${value.length} items` : `${entryList.length} keys`;

  if (entryList.length === 0) {
    return (
      <div className="json-line">
        {name !== undefined && <span className="json-key">{name}: </span>}
        <span className="json-bracket">{openBracket}{closeBracket}</span>
      </div>
    );
  }

  return (
    <div className="json-node">
      <button type="button" className="json-line json-line--toggle" onClick={() => setOpen((o) => !o)}>
        {name !== undefined && <span className="json-key">{name}: </span>}
        <span className="json-toggle">{open ? '▼' : '▶'}</span>
        <span className="json-bracket">{openBracket}</span>
        {!open && <span className="json-preview">{preview}</span>}
        {!open && <span className="json-bracket">{closeBracket}</span>}
      </button>
      {open && (
        <div className="json-children">
          {entryList.map(([key, child]) => (
            <JsonNode
              key={String(key)}
              name={isArray ? undefined : key}
              value={child}
              depth={depth + 1}
            />
          ))}
          <div className="json-line">
            <span className="json-bracket">{closeBracket}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function JsonResultWidget({ data, className = '', style }) {
  return (
    <div className={`tool-result-json ${className}`.trim()} style={style}>
      <JsonNode value={data} />
    </div>
  );
}

export function TextResultWidget({ text, className = '', style, error = false }) {
  return (
    <pre
      className={`tool-result-text${error ? ' tool-result-text--error' : ''} ${className}`.trim()}
      style={style}
    >
      {text}
    </pre>
  );
}

export default function ToolResultContent({ result, error, className = '', style }) {
  if (error) {
    return <TextResultWidget text={String(error)} className={className} style={style} error />;
  }

  const classified = classifyToolResultContent(result);
  if (classified.kind === 'json') {
    return <JsonResultWidget data={classified.value} className={className} style={style} />;
  }

  return <TextResultWidget text={classified.value} className={className} style={style} />;
}
