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

Or run `docker compose up --build -d --wait --wait-timeout 180` from the repository root. Open http://localhost:8080. This launches React/nginx, Flask, Mosquitto, and a mock MQTT valve. Startup waits for health checks, including a correlated read from the mock valve. Docker builds React with server mode as its default; nginx proxies `/api/` to Flask, and the backend keeps state in the named `lab-data` volume. Application port 8080 and broker port 1883 are published only on loopback. `docker compose down` preserves the volume; removing it deletes the server workspace. `docker compose logs -f` shows all service logs.

The user launched the Docker stack and its published application API passed an MQTT smoke check: connect, command 75%, verify, restore 0%. A custom plan on an isolated local backend also passed against the Docker Mosquitto broker and mock valve (set 60%, wait, equality/range assertions, restore 0%). This session cannot access Docker's API pipe directly, so rebuilding the latest images is performed from the user's PowerShell window. You can issue the command directly in Windows PowerShell; the application does not require a separate WSL shell. The Docker workspace is a separate named volume from a locally launched Flask database.

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

A Mosquitto broker and mock valve peer are included in the default stack so you can exercise the wire-level adapter without physical hardware:

```powershell
docker compose up --build -d --wait --wait-timeout 180
```

At http://localhost:8080 select **Add device**, choose the valve profile and MQTT adapter, and enter `mqtt://broker:1883/lab/demo-valve`. Connect that device and run **Control response** to send a real MQTT command through Mosquitto to the emulator, verify its response, and restore its original value. **Connect all** applies to simulation adapters; connect this MQTT device individually. The Docker stack defaults `LAB_ALLOW_HARDWARE=true` to enable its MQTT adapter; no host hardware devices are mounted. Set it to false to disable transport adapters. For a separately launched local Flask backend, enable hardware explicitly and use `mqtt://127.0.0.1:1883/lab/demo-valve`. The broker is for local development, allows anonymous connections, and publishes its port only on loopback. The old `docker-compose.fixture.yml` command remains compatible as a no-op overlay.

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

Remaining work includes physical-device validation, TLS/authenticated MQTT, device-specific protocol adapters, role-based access, and migration of firmware/user-management features. This is a working local test product foundation; production multiuser deployment and arbitrary hardware compatibility are not claimed.

## Editable test plans and reproducible results

In Flask mode, open **Plan library** (`/plans`). Create, edit, duplicate, import, export, and delete plans. Each plan declares its device profile and contains 1–30 ordered steps. The runner adds a connection check and, for plans with output commands, an automatic restoration step. Choose a matching target device and a saved plan from **Test bench**. Browser-only mode retains the two existing built-in plans.

Supported actions:

| Action | Parameters | Behavior |
| --- | --- | --- |
| `read` | `timeout` | Read fresh telemetry. |
| `set` | `value`, `timeout` | Send a numeric profile-limited output command. |
| `assert_equal` | `value`, `tolerance`, `timeout` | Read and check the expected numeric value within tolerance. |
| `assert_range` | `min`, `max`, `timeout` | Read and check explicit inclusive limits. |
| `wait` | `seconds` | Yield while allowing an output to settle; cancellation remains available. |

Response timeouts default to 2 seconds and accept 0.1–10 seconds. They bound each step's transport work; they are not polling/retry windows for an assertion. Waits accept 0–30 seconds. Command limits are temperature 0–50, valve 0–100, and relay 0 or 1. Explicit custom assertions use their own limits/tolerances; the built-in plans continue to use peripheral thresholds or profile defaults. After a failed check, subsequent `set` operations fail as skipped instead of issuing more output commands. Restoration is attempted on success, failure, cancellation, or graceful shutdown; a real-transport cleanup failure remains a failed result with a persistent device warning. Server restarts cancel interrupted runs and require hardware inspection if output state is unknown.

The original `TestPlanService` list/create/preview/run methods now accept a workspace repository. The default workbench uses validated executable plans and the existing single-owner runner; the original SQLAlchemy/file-upload path remains opt-in. Legacy PDF plans, arbitrary shell commands, and protocol-specific free-text steps are not executed by this editor.

Every new server run stores a deep copy of the selected plan/version, device configuration, attached peripherals, and workspace revision. **Results** shows the captured configuration and exports individual runs. Updating or deleting a plan does not rewrite earlier results. Saved plan libraries survive restart and workspace reset. Stale edits/deletes return HTTP 409, and plan changes are blocked during an active run.

Plan APIs: `/api/lab/test-plans` GET/POST; `/api/lab/test-plans/<id>` GET/PUT/DELETE; `/api/lab/test-plans/<id>/run` POST with `deviceId`. The existing `/api/lab/runs` endpoint also accepts saved plan IDs. PUT and DELETE require the saved `version`. Import JSON contains `name`, `kind`, optional `description`, and `steps`. A ready-to-import example is `deployment/plans/valve-response.json`.

Rebuild and verify Docker with `.\start-workbench.ps1 -Docker -Verify`. The verification creates an isolated temporary MQTT valve device, runs a control check, verifies restoration, and removes the temporary device; the result remains in history. It refuses a busy bench or an already-connected peer at the same endpoint. To rerun only the check: `docker compose exec -T backend python tools/smoke_mqtt.py`. A host Python can also run `backend/tools/smoke_mqtt.py --url http://127.0.0.1:8080`.

## Original blueprints and peripherals

Select Flask mode in Settings, then open **Blueprints**. Preview a JSON file before saving it to the library. Supported input layouts are root `peripherals`, `controller.peripherals`, and canonical `devices`. Temperature sensors, valves, and relays become disconnected simulated devices when you select **Add to bench**. Generic `Sensor` entries with temperature in their name map to temperature profiles with a visible warning. Unsupported definitions remain in the sanitized source configuration and are reported in the preview; their commands are not executed. Credential fields are excluded from saved/exported blueprints. Original protocol/connection definitions remain metadata and do not open physical connections.

**Save current bench** captures device profiles and peripheral properties for reuse. Applying a saved blueprint appends devices without replacing the bench. Saved blueprints survive workspace reset; reset clears attached peripherals along with devices, history, and logs. Deleting a device also removes its attached peripheral settings.

The workbench routes call the existing `PeripheralService` CRUD methods using an injected SQLite workspace repository, and `BlueprintService.normalize_configuration` uses the original `validate_json` utility. Legacy SQLAlchemy implementations remain opt-in. Utility modules now load individually instead of eagerly importing hardware, deployment, and database modules during startup. The legacy machine-scanning operation is not exposed by these new routes.

Peripheral `threshold` settings affect server health/control operating-range checks. A number is an upper bound; an object can contain `min`, `max`, or both. A missing bound is unbounded. When several peripherals specify limits for one device, every limit must pass. Without configured thresholds, profile defaults apply (temperature 0–50, valve 0–100, relay 0–1). Other properties remain metadata. Control command limits still follow the device profile. Configuration changes are blocked during a run, and stale peripheral edits/deletes receive HTTP 409 instead of overwriting a newer version.

API routes: `/api/lab/blueprints` (GET/POST), `/preview` and `/capture` beneath that path (POST), `/api/lab/blueprints/<id>/apply` (POST), `/api/lab/blueprints/<id>` (DELETE); `/api/lab/peripherals` (GET/POST), `/api/lab/peripherals/<id>` (PATCH/DELETE). PATCH and peripheral DELETE require the current `version`. Blueprint requests wrap input in `configuration`; capture takes `name` and optional `description`.
