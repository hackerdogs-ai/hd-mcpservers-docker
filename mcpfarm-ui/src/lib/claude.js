// claude.js — Claude API integration for Prompt mode (agentic loop)

import { getClaudeKey } from './api.js';
import { mcpClient } from './mcp.js';

const CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages';
const ANTHROPIC_VERSION = '2023-06-01';
const DEFAULT_MODEL = 'claude-opus-4-5';

/**
 * Convert MCP tool schema to Anthropic tool format
 */
function mcpToolToAnthropic(tool, serverName) {
  return {
    name: `${serverName}__${tool.name}`.replace(/-/g, '_'),
    description: `[${serverName}] ${tool.description || tool.name}`,
    input_schema: tool.inputSchema || { type: 'object', properties: {} },
    // Store original info for routing
    _serverName: serverName,
    _toolName: tool.name,
  };
}

/**
 * Call Claude API with messages and tools
 */
async function callClaude(messages, tools, claudeKey) {
  const key = claudeKey || getClaudeKey();
  if (!key) throw new Error('Claude API key is required. Set it in Settings.');

  // Strip internal routing fields before sending to API
  const apiTools = tools.map(({ _serverName, _toolName, ...t }) => t);

  const body = {
    model: DEFAULT_MODEL,
    max_tokens: 8192,
    messages,
    tools: apiTools,
  };

  const res = await fetch(CLAUDE_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': key,
      'anthropic-version': ANTHROPIC_VERSION,
      'anthropic-dangerous-direct-browser-calls': 'true',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`Claude API error ${res.status}: ${errText}`);
  }

  return res.json();
}

/**
 * Run agentic loop: prompt → Claude → tool calls → tool results → Claude → ...
 *
 * @param {string} prompt - User's natural language prompt
 * @param {Array} mcpTools - Array of { serverName, tool } objects
 * @param {Function} onEvent - Callback for streaming events { type, data }
 * @param {string} [claudeKey] - Optional override for Claude API key
 * @returns {Promise<{ messages: Array, toolCalls: Array }>}
 */
export async function runAgenticLoop(prompt, mcpTools, onEvent, claudeKey) {
  const tools = mcpTools.map(({ serverName, tool }) =>
    mcpToolToAnthropic(tool, serverName)
  );

  // Build routing map: anthropic tool name → { serverName, toolName }
  const toolRoutes = {};
  mcpTools.forEach(({ serverName, tool }) => {
    const anthropicName = `${serverName}__${tool.name}`.replace(/-/g, '_');
    toolRoutes[anthropicName] = { serverName, toolName: tool.name };
  });

  const messages = [{ role: 'user', content: prompt }];
  const allToolCalls = [];

  onEvent?.({ type: 'status', data: 'Sending prompt to Claude...' });

  let iterations = 0;
  const MAX_ITERATIONS = 10;

  while (iterations < MAX_ITERATIONS) {
    iterations++;

    let response;
    try {
      response = await callClaude(messages, tools, claudeKey);
    } catch (err) {
      onEvent?.({ type: 'error', data: err.message });
      throw err;
    }

    onEvent?.({ type: 'claude_response', data: response });

    // Add assistant message to history
    messages.push({ role: 'assistant', content: response.content });

    // Check stop reason
    if (response.stop_reason === 'end_turn') {
      onEvent?.({ type: 'done', data: 'Claude finished.' });
      break;
    }

    if (response.stop_reason === 'tool_use') {
      const toolUseBlocks = response.content.filter((b) => b.type === 'tool_use');

      if (toolUseBlocks.length === 0) break;

      // Execute each tool call
      const toolResults = [];

      for (const block of toolUseBlocks) {
        const route = toolRoutes[block.name];
        if (!route) {
          const errMsg = `Unknown tool: ${block.name}`;
          onEvent?.({ type: 'tool_error', data: { name: block.name, error: errMsg } });
          toolResults.push({
            type: 'tool_result',
            tool_use_id: block.id,
            content: errMsg,
            is_error: true,
          });
          continue;
        }

        const { serverName, toolName } = route;

        onEvent?.({
          type: 'tool_call',
          data: {
            id: block.id,
            serverName,
            toolName,
            args: block.input,
          },
        });

        let toolResult;
        try {
          toolResult = await mcpClient.callTool(serverName, toolName, block.input);

          onEvent?.({
            type: 'tool_result',
            data: {
              id: block.id,
              serverName,
              toolName,
              result: toolResult,
            },
          });

          allToolCalls.push({
            id: block.id,
            serverName,
            toolName,
            args: block.input,
            result: toolResult,
          });

          // Convert MCP result content to string for Claude
          let resultContent;
          if (toolResult && Array.isArray(toolResult.content)) {
            resultContent = toolResult.content
              .map((c) => (c.type === 'text' ? c.text : JSON.stringify(c)))
              .join('\n');
          } else if (typeof toolResult === 'string') {
            resultContent = toolResult;
          } else {
            resultContent = JSON.stringify(toolResult, null, 2);
          }

          toolResults.push({
            type: 'tool_result',
            tool_use_id: block.id,
            content: resultContent,
          });
        } catch (err) {
          onEvent?.({
            type: 'tool_error',
            data: { id: block.id, serverName, toolName, error: err.message },
          });

          allToolCalls.push({
            id: block.id,
            serverName,
            toolName,
            args: block.input,
            error: err.message,
          });

          toolResults.push({
            type: 'tool_result',
            tool_use_id: block.id,
            content: `Error: ${err.message}`,
            is_error: true,
          });
        }
      }

      // Add tool results as user message
      messages.push({ role: 'user', content: toolResults });
      onEvent?.({ type: 'status', data: 'Sending tool results back to Claude...' });
      continue;
    }

    // Unknown stop reason — stop the loop
    break;
  }

  if (iterations >= MAX_ITERATIONS) {
    onEvent?.({ type: 'warning', data: 'Maximum iteration limit reached.' });
  }

  return { messages, toolCalls: allToolCalls };
}
