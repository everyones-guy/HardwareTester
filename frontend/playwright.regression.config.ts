import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/browser',
  outputDir: './test-results-browser',
  workers: 1,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5176', trace: 'retain-on-failure' },
  webServer: {
    command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5176 --strictPort',
    url: 'http://127.0.0.1:5176',
    reuseExistingServer: false,
    env: { VITE_LAB_MODE: 'browser' },
  },
});
