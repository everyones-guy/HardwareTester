# Hardware Tester development workbench

The default React app is now an interactive, browser-local simulation lab. It works without Flask, a database, MQTT broker, WSL, or physical hardware.

## Run on Windows

Requires Node.js 22.12 or newer (Node 22 recommended).

From the repository root:

```powershell
.\start-workbench.ps1
```

Open http://localhost:5173. Or use `cd frontend`, `npm ci`, and `npm run dev`.

## Run with Docker

Start Docker Desktop's Linux engine, then:

```powershell
.\start-workbench.ps1 -Docker
```

Alternatively: `docker compose up --build -d`. Open http://localhost:8080. Stop with `docker compose down`.

This deployment serves the simulation workbench through nginx, including direct-route fallback and a `/health` endpoint. It does not run Flask or connect to physical devices. API calls return an explicit 503. The original Docker and Compose files are preserved as `Dockerfile.legacy` and `docker-compose.legacy.yml` for reference; they have known path/dependency/configuration problems and are not a supported launch path.

Docker Compose configuration was validated on the development machine. Image execution could not be verified because the Docker Linux engine was stopped.

## Try the complete flow

1. Select **Connect bench** on Overview. Three virtual devices connect: MQTT temperature sensor, Serial proportional valve, USB relay.
2. Select a device and run **Connection & health**. Handshake, telemetry, and range checks should pass.
3. Choose **Out-of-range reading** in the inspector and run again. The range check should fail with the observed value.
4. Choose **Transport timeout** and run again. Checks fail because no acknowledgement arrives.
5. Clear the fault. Run **Control response** to send a command, verify the actual simulated response, and restore the original state.
6. Change valve position or switch the relay manually in the inspector.
7. Visit Results, inspect individual runs, and export a JSON report. Filter or export Activity log events.
8. Add another virtual device from Devices. Search by name or protocol, connect it, then test it.

Connections and transport behavior are explicitly simulated. There is no wire-level MQTT, serial port, USB device access, firmware execution, or timing fidelity claim. Temperature telemetry updates once per second. Tests execute one step every 750 ms, use current device state, and respond to disconnects/fault changes during execution.

## Persistence and cleanup

Device configurations, the last 100 test runs, and 250 events live in browser localStorage. Reload disconnects devices, cancels interrupted runs, and restores their saved control values. Stopping a control test also restores the original value. Browser storage failure displays a warning; JSON export still works. Settings offers a complete workspace export and a confirmed local reset. Exports are reports/backups; import is not implemented yet.

## Verification

```powershell
.\start-workbench.ps1 -Verify
cd frontend
npm run test:e2e
```

`npm test` runs simulator behavior tests with Node's test runner. `npm run build` checks the entire production import graph (including loaded legacy dashboards) with strict TypeScript before building with Vite.

For browser tests, install Playwright Chromium with `npx playwright install chromium`, or use an installed Edge browser:

```powershell
$env:PLAYWRIGHT_CHANNEL = 'msedge'
npm run test:e2e
```

`npm run type-check:all` additionally audits every source file, including disconnected legacy contexts, hooks, and components. Those older files contain existing mismatched service imports and missing services; this broader audit currently fails. It is deliberately retained to keep that backlog visible rather than hide it with type suppression.

## Existing backend and dashboards

The original dashboards remain under `/legacy/emulator`, `/legacy/connect`, `/legacy/tests`, and the other legacy routes. They require the existing Flask backend and are not covered by the simulation engine. Original API retries, firmware container props/imports, confirmation dialog props, hardware detail method usage, and sidebar navigation were repaired where necessary to build these reachable screens.

The existing `setup_universal_hardware_tester.ps1` was pushed to this repository. It installs system infrastructure (WSL, PostgreSQL, Docker, Kubernetes tools, AWS CLI), then clones/pulls a repository in the home directory. It does not install this clone's frontend/backend dependencies or start the application. Its missing parenthesis has been repaired, but its installers were not executed. The self-healing Python runner still contains placeholder script paths and is not used by the new launcher.

## Next product milestones

- Repair Flask startup, dependency declarations, SPA serving paths, and migration bootstrapping; exercise APIs against an isolated database.
- Define one device adapter contract, then implement real MQTT and serial adapters with timeouts/cancellation and the same test result model.
- Add editable test plans with assertions, versioned configuration import, reconnect behavior, and reproducible runs across backend sessions.
- Validate on physical devices and harden authentication, authorization, deployment, and telemetry retention before production use.

This milestone is a working simulation product foundation, not a completed real-hardware or production deployment.

## Verified for this milestone

- 11 simulator tests passed.
- 6 Chromium browser tests passed, covering healthy/faulted runs, all control profiles, cancellation, disconnects, reload recovery, device management, JSON export, and mobile layout.
- Strict type checking of the production import graph and Vite production build passed.
- Docker Compose configuration, PowerShell script parsing, and Git whitespace checks passed.
- Desktop and mobile screenshots were visually inspected.
- Docker image execution and physical-device/backend integration remain unverified.

