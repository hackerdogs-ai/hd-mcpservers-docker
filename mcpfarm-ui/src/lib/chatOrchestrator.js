/**
 * Provider-agnostic agentic loop for the assistant-ui LocalRuntime adapter.
 *
 * The LLM turn runs server-side (encrypted keys) via `/chat/completions`; tool
 * execution stays in the browser via `mcpClient` (which already has an MCP
 * session over Caddy). This generator yields cumulative assistant-ui message
 * parts so the UI streams text and tool cards as the loop progresses.
 */
import { mcpClient } from './mcp.js';
import { chatCompletionServer } from './api.js';
import { encodeToolCallId, serverForTool } from './toolBinding.js';

const DEFAULT_SYSTEM = `You are the MCP Farm assistant. You help operators run security and OSINT tooling exposed as MCP tools.
- Use the provided tools when they can answer the request; do not fabricate tool output.
- Explain findings concisely and surface concrete results.
- Only call tools that are provided. If no tool fits, answer directly.`;

const MAX_ROUNDS = 8;

/** Convert an MCP tool result into text to feed back to the model. */
export function mcpResultToText(result) {
  if (result?.content && Array.isArray(result.content)) {
    return result.content.map((c) => (c.type === 'text' ? c.text : JSON.stringify(c))).join('\n');
  }
  if (typeof result === 'string') return result;
  return JSON.stringify(result ?? '', null, 2);
}

/** Convert assistant-ui ThreadMessages into the normalized wire format. */
export function threadMessagesToNormalized(messages) {
  const out = [];
  for (const m of messages || []) {
    const role = m.role;
    if (role === 'system') continue;
    const parts = m.content || [];
    if (role === 'user') {
      const text = parts.filter((p) => p.type === 'text').map((p) => p.text).join('\n');
      out.push({ role: 'user', content: text });
      continue;
    }
    if (role === 'assistant') {
      const text = parts.filter((p) => p.type === 'text').map((p) => p.text).join('\n');
      const toolParts = parts.filter((p) => p.type === 'tool-call');
      if (toolParts.length) {
        out.push({
          role: 'assistant',
          content: text,
          toolCalls: toolParts.map((p) => ({ id: p.toolCallId, name: p.toolName, arguments: p.args || {} })),
        });
        for (const p of toolParts) {
          out.push({
            role: 'tool',
            tool_call_id: p.toolCallId,
            tool_use_id: p.toolCallId,
            name: p.toolName,
            content: typeof p.result === 'string' ? p.result : mcpResultToText(p.result),
          });
        }
      } else if (text) {
        out.push({ role: 'assistant', content: text });
      }
    }
  }
  return out;
}

/** Map bound tools to the MCP tool schema the proxy expects. */
function bindingToToolSchemas(binding) {
  return (binding?.tools || []).map((t) => ({
    name: t.name,
    description: t.description || '',
    inputSchema: t.inputSchema || { type: 'object', properties: {} },
  }));
}

/**
 * Run one user turn to completion.
 *
 * @param {object} params
 * @param {Array}  params.messages   assistant-ui ThreadMessages (full history)
 * @param {object} params.binding    { servers, tools, mode }
 * @param {string} params.provider
 * @param {string} params.model
 * @param {string} [params.system]
 * @param {AbortSignal} [params.abortSignal]
 * @param {(text:string)=>void} [params.onError]
 * @returns {AsyncGenerator} yields { content: Part[] }
 */
export async function* runChatTurn({ messages, binding, provider, model, system, abortSignal }) {
  const toolSchemas = bindingToToolSchemas(binding);
  const wire = [
    { role: 'system', content: system || DEFAULT_SYSTEM },
    ...threadMessagesToNormalized(messages),
  ];

  // Accumulated assistant-ui parts for THIS turn (re-emitted each yield).
  const parts = [];
  let callCounter = 0;

  for (let round = 0; round < MAX_ROUNDS; round += 1) {
    if (abortSignal?.aborted) return;

    let response;
    try {
      response = await chatCompletionServer({
        provider,
        model,
        messages: wire,
        tools: toolSchemas,
      });
    } catch (err) {
      parts.push({ type: 'text', text: `\n\n**Error:** ${err.message}` });
      yield { content: [...parts] };
      return;
    }

    const text = response.content || '';
    const toolCalls = response.toolCalls || [];

    if (text) {
      parts.push({ type: 'text', text });
      yield { content: [...parts] };
    }

    if (!toolCalls.length) {
      // No tools requested — turn complete.
      if (!text) {
        parts.push({ type: 'text', text: '' });
        yield { content: [...parts] };
      }
      return;
    }

    // Register the tool-call parts (pending) and record for the model.
    const pending = [];
    const assistantToolCalls = [];
    for (const tc of toolCalls) {
      const server = serverForTool(binding, tc.name);
      const callId = encodeToolCallId(server, tc.name, callCounter++);
      const partIndex = parts.length;
      parts.push({
        type: 'tool-call',
        toolCallId: callId,
        toolName: tc.name,
        args: tc.arguments || {},
        argsText: JSON.stringify(tc.arguments || {}),
      });
      pending.push({ partIndex, callId, server, name: tc.name, args: tc.arguments || {} });
      assistantToolCalls.push({ id: callId, name: tc.name, arguments: tc.arguments || {} });
    }
    yield { content: [...parts] };

    wire.push({ role: 'assistant', content: text, toolCalls: assistantToolCalls });

    // Execute each tool and stream results into the parts + wire history.
    for (const p of pending) {
      if (abortSignal?.aborted) return;
      if (!p.server) {
        parts[p.partIndex] = { ...parts[p.partIndex], result: `Unknown tool: ${p.name}`, isError: true };
        wire.push({ role: 'tool', tool_call_id: p.callId, tool_use_id: p.callId, name: p.name, content: `Unknown tool: ${p.name}` });
        yield { content: [...parts] };
        continue;
      }
      try {
        const result = await mcpClient.callTool(p.server, p.name, p.args);
        const resultText = mcpResultToText(result);
        parts[p.partIndex] = { ...parts[p.partIndex], result, isError: !!result?.isError };
        wire.push({ role: 'tool', tool_call_id: p.callId, tool_use_id: p.callId, name: p.name, content: resultText });
      } catch (err) {
        parts[p.partIndex] = { ...parts[p.partIndex], result: `Error: ${err.message}`, isError: true };
        wire.push({ role: 'tool', tool_call_id: p.callId, tool_use_id: p.callId, name: p.name, content: `Error: ${err.message}` });
      }
      yield { content: [...parts] };
    }
  }

  parts.push({ type: 'text', text: '\n\n_Reached the maximum number of tool rounds._' });
  yield { content: [...parts] };
}

export { DEFAULT_SYSTEM };
