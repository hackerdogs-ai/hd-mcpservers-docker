function classifyTextContent(text) {
  const trimmed = text.trim();
  if (!trimmed) return { kind: 'text', value: text };

  try {
    return { kind: 'json', value: JSON.parse(trimmed) };
  } catch {
    const lines = trimmed.split('\n').filter((line) => line.trim());
    if (lines.length > 1) {
      try {
        return { kind: 'json', value: lines.map((line) => JSON.parse(line.trim())) };
      } catch {
        /* fall through */
      }
    }
    return { kind: 'text', value: text };
  }
}

/** Extract plain text from an MCP tool result payload. */
export function extractToolResultText(result) {
  if (!result) return '';
  if (typeof result === 'string') return result;
  if (result.content && Array.isArray(result.content)) {
    return result.content
      .map((c) => {
        if (c.type === 'text') return c.text;
        if (c.type === 'image') return `[image: ${c.mimeType || 'binary'}]`;
        return JSON.stringify(c, null, 2);
      })
      .join('\n');
  }
  if (result.isError && result.content) return extractToolResultText({ content: result.content });
  return null;
}

/** Flat string used for empty-output checks and fallbacks. */
export function getToolResultDisplayText(result) {
  if (!result) return '';
  if (typeof result === 'string') return result;
  const text = extractToolResultText(result);
  if (text !== null) return text;
  return JSON.stringify(result, null, 2);
}

/** Decide whether to render JSON or plain text for a tool result. */
export function classifyToolResultContent(result) {
  if (result == null) return { kind: 'text', value: '' };
  if (typeof result === 'string') return classifyTextContent(result);

  const text = extractToolResultText(result);
  if (text !== null) return classifyTextContent(text);

  if (typeof result === 'object') return { kind: 'json', value: result };
  return { kind: 'text', value: String(result) };
}
