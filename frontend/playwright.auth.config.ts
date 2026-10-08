import { defineConfig } from '@playwright/test';
import path from 'node:path';
export default defineConfig({
  testDir: './tests/auth',
  workers: 1,
  reporter: 'list',
  outputDir: './test-results-auth',
  use: { baseURL: 'http://127.0.0.1:5175', trace: 'retain-on-failure' },
  webServer: [
    {
      command: '".venv/Scripts/python.exe" runserver.py --port 5003',
      cwd: path.resolve(__dirname, '../backend'),
      url: 'http://127.0.0.1:5003/api/health',
      reuseExistingServer: process.env.LAB_TEST_REUSE_SERVERS === 'true',
      env: {
        PYTHONPATH: '',
        LAB_AUTH_ENABLED: 'true',
        LAB_DB_PATH: path.resolve(__dirname, '../work/auth-browser.sqlite3'),
        LAB_ALLOWED_ORIGINS: 'http://127.0.0.1:5175',
        LAB_API_TOKEN: '',
      },
    },
    {
      command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5175 --strictPort',
      url: 'http://127.0.0.1:5175',
      reuseExistingServer: process.env.LAB_TEST_REUSE_SERVERS === 'true',
      env: { VITE_API_TARGET: 'http://127.0.0.1:5003', VITE_LAB_MODE: 'server' },
    },
  ],
});
