import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 5120,
    host: 'localhost',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 300000,
        proxyTimeout: 300000,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            proxyReq.setHeader('Connection', 'keep-alive');
            proxyReq.setHeader('Keep-Alive', 'timeout=300');
          });
          proxy.on('error', (err, req, res) => {
            console.error('Proxy error:', err);
            if (!res.headersSent) {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ detail: '代理连接错误，请稍后重试' }));
            }
          });
        }
      }
    },
    hmr: {
      protocol: 'ws',
      host: 'localhost',
      port: 5120
    }
  },
  test: {
    environment: 'jsdom',
    globals: true
  }
})
