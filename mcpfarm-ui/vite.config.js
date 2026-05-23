import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/services':  { target: 'http://localhost', changeOrigin: true },
      '/health':    { target: 'http://localhost', changeOrigin: true },
      '/admin':     { target: 'http://localhost', changeOrigin: true },
      '/verify':    { target: 'http://localhost', changeOrigin: true },
      // MCP server routes: all server names end with -mcp
      // matches /{anything}-mcp, /{anything}-mcp/mcp, etc.
      '^/[^/]+-mcp': { target: 'http://localhost', changeOrigin: true },
    },
  },
});
