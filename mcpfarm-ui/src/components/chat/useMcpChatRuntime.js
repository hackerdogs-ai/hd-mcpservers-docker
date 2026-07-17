/**
 * Shared assistant-ui LocalRuntime hook for both chat surfaces.
 *
 * The Chat page and the per-server Chat tab differ only in how a binding is
 * resolved for a turn, so they pass a `resolveBinding(query, ctx)` callback and
 * a `getProviderModel()` accessor. Everything else (streaming, cancel, edit,
 * regenerate) is provided by assistant-ui's LocalRuntime.
 */
import { useLocalRuntime } from '@assistant-ui/react';
import { useMemo, useRef } from 'react';
import { runChatTurn } from '../../lib/chatOrchestrator.js';

/**
 * @param {object} opts
 * @param {(query:string)=>Promise<object>} opts.resolveBinding
 * @param {()=>{provider:string, model:string}} opts.getProviderModel
 * @param {string} [opts.system]
 * @param {(binding:object)=>void} [opts.onBinding] notified with the resolved binding
 */
export function useMcpChatRuntime({ resolveBinding, getProviderModel, system, onBinding }) {
  // Keep latest callbacks without re-creating the adapter each render.
  const ref = useRef({ resolveBinding, getProviderModel, system, onBinding });
  ref.current = { resolveBinding, getProviderModel, system, onBinding };

  const adapter = useMemo(
    () => ({
      async *run({ messages, abortSignal }) {
        const { resolveBinding, getProviderModel, system, onBinding } = ref.current;
        const { provider, model } = getProviderModel();

        const lastUser = [...messages].reverse().find((m) => m.role === 'user');
        const query = (lastUser?.content || [])
          .filter((p) => p.type === 'text')
          .map((p) => p.text)
          .join('\n');

        let binding;
        try {
          binding = await resolveBinding(query);
        } catch (err) {
          yield { content: [{ type: 'text', text: `**Could not resolve tools:** ${err.message}` }] };
          return;
        }
        onBinding?.(binding);

        // Serializable summary attached to the assistant message so the thread
        // can render a "tools" footer (Sources-style) at the bottom of the reply.
        const bindingMeta = {
          mode: binding?.mode || 'dynamic',
          notes: binding?.notes || '',
          tools: (binding?.tools || []).map((t) => ({
            server: t.server,
            name: t.name,
            description: t.description || '',
          })),
        };

        for await (const chunk of runChatTurn({ messages, binding, provider, model, system, abortSignal })) {
          yield { ...chunk, metadata: { custom: { binding: bindingMeta } } };
        }
      },
    }),
    [],
  );

  return useLocalRuntime(adapter);
}
