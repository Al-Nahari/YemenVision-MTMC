import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/** Read the first API key from backend/.env so it never reaches the browser. */
function localApiKey(): string {
  try {
    const envFile = readFileSync(join(process.cwd(), '..', 'backend', '.env'), 'utf8');
    const match = envFile.match(/^API_KEYS_JSON=(.*)$/m);
    if (!match) return '';
    const keys = JSON.parse(match[1].trim()) as Record<string, unknown>;
    return Object.keys(keys)[0] || '';
  } catch {
    return '';
  }
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 4200,
    proxy: {
      '/api': {
          // The local FastAPI service runs on 8001. Keep the environment
          // override for deployments, but make the default work out of the box.
          target: process.env.YV_BACKEND_TARGET || 'http://127.0.0.1:8001',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            const key = localApiKey();
            if (key && !proxyReq.getHeader('X-API-Key')) {
              proxyReq.setHeader('X-API-Key', key);
            }
          });
        },
      },
    },
  },
});
