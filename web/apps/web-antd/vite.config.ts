import { fileURLToPath, URL } from 'node:url';

import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      resolve: {
        alias: {
          '@': fileURLToPath(
            new URL('./src/sicherplan-legacy', import.meta.url),
          ),
        },
      },
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            target: 'http://localhost:8000',
            ws: true,
          },
        },
      },
    },
  };
});
