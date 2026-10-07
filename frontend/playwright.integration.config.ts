import { defineConfig } from '@playwright/test';
import path from 'node:path';
export default defineConfig({
  testDir: './tests/integration', workers: 1, reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5174', channel: process.env.PLAYWRIGHT_CHANNEL || undefined, trace: 'retain-on-failure' },
  webServer: [
    { command: '".venv/Scripts/python.exe" runserver.py --port 5001', cwd: path.resolve(__dirname, '../backend'), url: 'http://127.0.0.1:5001/api/health', reuseExistingServer: process.env.LAB_TEST_REUSE_SERVERS === 'true', env: { PYTHONPATH: '', LAB_AUTH_ENABLED: 'false', LAB_DB_PATH: path.resolve(__dirname, '../work/integration.sqlite3'), LAB_API_TOKEN: '', LAB_ALLOW_HARDWARE: 'false', LAB_ALLOWED_ORIGINS: 'http://127.0.0.1:5174' } },
    { command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174 --strictPort', url: 'http://127.0.0.1:5174', reuseExistingServer: process.env.LAB_TEST_REUSE_SERVERS === 'true', env: { VITE_API_TARGET: 'http://127.0.0.1:5001', VITE_LAB_MODE: 'server' } },
  ],
});
