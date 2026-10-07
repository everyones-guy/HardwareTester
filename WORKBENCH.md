# Hardware Tester workbench

Hardware Tester now supports two execution engines through the same React UI:

- **Browser simulator:** private localStorage state; no backend needed.
- **Flask workspace:** shared SQLite persistence, server-side telemetry and tests, simulated devices, and optional serial/MQTT adapters.

## Launch locally

Requires Node.js 22.12+ and Python 3.11+ (verified here with Node 22 and Python 3.13).

From the repository root, in separate terminals:

```powershell
.\start-backend.ps1
.\start-workbench.ps1
```

Open http://localhost:5173. Choose **Workspace settings > Connect Flask backend**. The browser bench and server bench are separate; switching engines never silently migrates or overwrites either workspace. A tab remembers its engine selection. API token storage is scoped to the browser session.

The backend binds to 127.0.0.1:5000 and uses `backend/instance/workbench.sqlite3`. `start-backend.ps1` creates an isolated Python environment, installs the declared runtime, and reinstalls when the requirements file changes. It does not need PostgreSQL, WSL, or the older infrastructure installer.

## Run the complete stack with Docker

Start Docker Desktop's Linux engine, then:

```powershell
.\start-workbench.ps1 -Docker
```

Or `docker compose up --build -d`. Open http://localhost:8080. Docker builds React with server mode as its default; nginx proxies `/api/` to Flask, and the backend keeps state in the named `lab-data` volume. The only published application port is bound to loopback. `docker compose down` preserves the volume; removing it deletes the server workspace.

Both Compose configurations were validated. Image execution remains unverified on this machine because Docker Desktop's Linux engine is not running.

## Exercise the workflow

1. Connect the Flask workspace through Settings.
2. Select **Connect bench**. This bulk action connects simulated devices only.
3. Run **Connection & health** on the temperature sensor, valve, or relay. Inspect the handshake, telemetry, and range checks.
4. Inject **Transport timeout** or **Out-of-range reading** and run again. Checks fail with an observed reason.
5. Clear the fault and run **Control response**. The engine sends a command, reads the response, verifies it, then restores the original output.
6. Reload or close the page during a server test. The test continues on Flask. Return to inspect its result.
7. Cancel a test, add/remove devices, control the valve/relay, filter logs, and export results.
8. Stop and restart Flask. Stored history persists. Devices disconnect, interrupted tests become cancelled, and simulated outputs recover to their saved values.

Server state retains 100 runs and 250 events. Exports are portable JSON reports/backups; import and custom editable plans are not implemented yet. Polling uses a state revision to reject old responses. A backend outage visibly disables commands; it never falls back to a fake successful result.

## Optional hardware adapters

Start the backend with hardware enabled:

```powershell
.\start-backend.ps1 -Hardware
```

In Flask mode, Add device now offers real Serial and MQTT transports. These adapters require the following **Hardware Tester JSON protocol**; arbitrary commercial hardware does not automatically implement it. Connect is explicit, and adding a device never opens the transport. Bulk Connect bench skips physical transports. Fault injection applies only to simulations.

Serial uses a local port such as `COM3` or `/dev/ttyUSB0`, 115200 baud, and newline-delimited JSON:

```json
{"id":"unique-request-id","command":"read"}
{"id":"unique-request-id","command":"set","value":75}
```

The device must respond with the same ID and a finite numeric value:

```json
{"id":"unique-request-id","value":75}
```

An error response may include `error`. Serial replies are bounded to 4 KB; stale IDs and malformed frames are ignored, and requests time out after two seconds.

MQTT endpoints use `mqtt://broker:1883/device/topic`. The adapter subscribes to `<topic>/reply`, waits for subscription acknowledgement, then publishes correlated JSON requests to `<topic>/command` at QoS 1 without retain. It ignores retained responses and unmatched IDs. MQTT connection readiness has a three-second timeout; device responses have a two-second timeout. This initial adapter supports an unauthenticated local development broker, not MQTT TLS/authentication provisioning.

Control plans skip output commands after a failed handshake. Missing acknowledgements do not prove an output stayed unchanged: cleanup attempts to restore the original output and records failures explicitly. A failed physical restoration remains visible in the inspector even after telemetry resumes. A server crash cannot guarantee hardware restoration; restart records that physical output state needs inspection. A successful intentional manual command establishes a new desired state and clears that warning.

Serial framing is tested against controlled port peers; MQTT was tested through Paho against a controlled TCP MQTT peer. No physical device has been connected or validated.

## MQTT mock fixture

An optional Mosquitto broker and mock valve peer let you exercise the wire-level adapter without physical hardware:

```powershell
docker compose -f docker-compose.yml -f docker-compose.fixture.yml up --build -d
```

For the local Flask backend, enable hardware and add a valve with endpoint `mqtt://127.0.0.1:1883/lab/demo-valve`. For the backend running inside Compose, set `LAB_ALLOW_HARDWARE=true` before bringing up the stack and use `mqtt://broker:1883/lab/demo-valve`. The fixture broker is for development only, with its published port bound to loopback.

Alternatively run the mock peer against an existing local broker:

```powershell
backend\.venv\Scripts\python.exe backend\tools\mqtt_fixture.py
```

## Verification

```powershell
.\start-backend.ps1 -Verify
.\start-workbench.ps1 -Verify
cd frontend
npm run test:e2e
npm run test:integration
```

Browser tests need Playwright Chromium (`npx playwright install chromium`) or installed Edge (`$env:PLAYWRIGHT_CHANNEL = 'msedge'`). Integration tests use isolated ports 5001/5174 and a separate database under `work/`; they do not reset your ordinary server workspace. In an environment with supervised test services, `LAB_TEST_REUSE_SERVERS=true` can reuse those exact isolated services.

Verified for this milestone:

- 21 backend tests: all device/plan profiles, persistence recovery, cancellation, API validation, origin/token checks, transport errors, real response validation, cleanup failures, and controlled serial/MQTT peers.
- 11 browser simulator unit tests.
- 6 browser-only end-to-end tests.
- 3 React/Flask integration tests: stateful commands, reload survival, faults, cancellation, and visible backend outages.
- Strict type checking of the production import graph and Vite production build.
- PowerShell launcher parsing, both Compose configurations, and Git whitespace checks.

`npm run type-check:all` still audits disconnected older scaffolding and reports its existing mismatched imports/missing services. That backlog is retained rather than suppressed.

## API and configuration

`GET /api/health` is the health probe. `GET /api/lab` returns `state` and capabilities. JSON mutations are under `/api/lab/devices`, `/devices/<id>/connection`, `/devices/<id>/fault`, `/devices/<id>/command`, `/connect-bench`, `/runs`, `/runs/cancel`, and `/reset`. `GET /api/lab/export` returns a complete workspace snapshot.

Optional environment variables:

- `LAB_DB_PATH`: SQLite file path.
- `LAB_ALLOW_HARDWARE=true`: enable explicit physical transports.
- `LAB_API_TOKEN`: require a bearer token for every lab route. Enter it in React Settings. The health probe remains public.
- `LAB_ALLOWED_ORIGINS`: comma-separated origins permitted to issue commands. Defaults include the documented local Vite/Compose origins; no general CORS access is enabled.
- `VITE_API_TARGET`: Vite proxy target, default `http://127.0.0.1:5000`.
- `VITE_LAB_MODE=server`: frontend default engine, selected at build/start time.

Run one backend owner process per database. Waitress serves concurrent HTTP requests while one lab worker owns the test/transport lifecycle. Multiple independent workers against one SQLite workspace are not supported.

## Older application and next steps

The original factory and launcher are retained as `legacy_app.py` and `runserver_legacy.py`; old models, services, and React dashboards are reference material for further migration. The clean default factory deliberately does not import their duplicate database objects, broker setup, or mismatched route registrations. The old API contract is not served by the new workbench backend. `Dockerfile.legacy` and `docker-compose.legacy.yml` preserve the original deployment attempts.

Remaining work includes physical-device validation, TLS/authenticated MQTT, device-specific protocol adapters, editable test plans/assertion limits, configuration import, and migration of firmware/user-management features. This is a working local test product foundation; production multiuser deployment and arbitrary hardware compatibility are not claimed.
