import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const farmTarget = `http://localhost:${process.env.FARM_PORT || '8485'}`;
const ollamaTarget = process.env.OLLAMA_URL || 'http://localhost:11434';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    strictPort: true,
    port: Number(process.env.UI_DEV_PORT || 5173),
    allowedHosts: true,
    proxy: {
      '/services':  { target: farmTarget, changeOrigin: true, rewrite: (path) => path },
      '/health':    { target: farmTarget, changeOrigin: true },
      '/admin':     { target: farmTarget, changeOrigin: true },
      '/verify':    { target: farmTarget, changeOrigin: true },
      '/ui-config': { target: farmTarget, changeOrigin: true },
      '/claude':    { target: farmTarget, changeOrigin: true },
      '/chat':      { target: farmTarget, changeOrigin: true },
      '/vectors':   { target: farmTarget, changeOrigin: true },
      '/llm-keys':  { target: farmTarget, changeOrigin: true },
      '^/[^/]+-mcp': { target: farmTarget, changeOrigin: true },
    },
  },
});
