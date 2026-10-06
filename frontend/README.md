# Hardware Tester React frontend

The default app is a browser-local hardware simulation workbench. See [WORKBENCH.md](../WORKBENCH.md) for the complete setup and example test flows.

```powershell
npm ci
npm run dev
```

Verification:

```powershell
npm test
npm run build
$env:PLAYWRIGHT_CHANNEL = 'msedge'
npm run test:e2e
```

The browser suite can use installed Edge, or Playwright Chromium after `npx playwright install chromium`. The original dashboards are available at `/legacy/emulator` and need Flask. `npm run type-check:all` also reports existing errors in unused legacy scaffolding; the production build checks all reachable application modules.
