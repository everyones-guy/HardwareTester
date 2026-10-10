# Hardware Tester workbench

Hardware Tester now supports two execution engines through the same React UI:

- **Browser simulator:** private localStorage state; no backend needed.
- **Flask workspace:** shared SQLite persistence, server-side telemetry and tests, simulated devices, and optional serial/MQTT adapters.

## Reusable emulator scenarios

The scenario catalog shows 1–5 compact pattern cards per page. Search names/descriptions, filter preset/custom patterns or response behavior, and sort presets first, alphabetically, or by stage count. Response strips use a labeled color legend and an accessible description. Open one card for its ordered stages, repeating final behavior, edit/duplicate/export/delete actions, and applied device snapshots. Saving or importing a pattern reveals it in the catalog. Editing moves keyboard focus to the editor heading.

Stage editors collapse individually or all at once. Loading a saved pattern starts with stages closed; new stages open automatically. Stage summaries show response type, read count, and delay. Invalid stage values remain flagged when collapsed and block saving. Reordering/removing stages keeps the editor state associated with the same stage. Applying library edits does not alter existing device snapshots; the catalog displays the versions each device is using.

**Emulator scenarios** is a shared Flask library for simulated devices. It includes five protected presets: Healthy device, Intermittent timeout, Delayed responses, Bad telemetry, and Timeout and recovery. Duplicate a preset to customize it, or create, reorder, import, export, edit, and delete custom sequences. Admins manage the library; operators apply, restart, and clear scenarios from the selected device inspector. Browser-only mode keeps the existing manual fault injection; reusable scenarios require the Flask engine. Serial/MQTT hardware adapters reject scenario application.

Each stage selects healthy responses, timeouts, out-of-range readings, or delayed responses for a specified number of read attempts. Command acknowledgements also count as reads; a control step can make several reads. The final response behavior repeats after the staged sequence is consumed. Restart resets the applied snapshot's cursor to zero without replacing its definition. Reapplying a library entry picks up its latest version. Editing or deleting the saved entry does not affect devices already using its snapshot, and a deleted applied sequence can still be restarted or cleared.

Background telemetry polling does not advance scenarios. Diagnostic checks, manual command reads, and test steps do. Application and restart do not connect a device. Scenario changes require an idle bench, clear manual fault injection, and preserve the simulated output; clear the scenario before using manual faults again. Out-of-range readings do not replace the underlying simulated output. Delays really wait and obey each step's remaining response timeout; cancellation is processed after an in-flight bounded read completes. Maximum delay is 2000 ms, with 1–20 stages and at most 200 staged read attempts. Counts are 1–100 per stage. A preset timeout is an immediate simulated missing acknowledgement; delayed scenarios measure actual waiting.

The library, applied snapshot, and current position persist in SQLite. After a server restart, transports are disconnected and the sequence position is retained. Workspace reset preserves the library and clears device applications. Results capture the scenario definition, version, and starting position in their device configuration; reruns continue at the current sequence position and warn when it differs. Restart from the device inspector to reproduce the initial experiment.

API: `POST /api/lab/scenarios`, `PUT/DELETE /api/lab/scenarios/<id>` (version checked), and `POST /api/lab/devices/<id>/scenario` with `scenarioId`, `scenarioId: null`, or `restart: true`. Scenario JSON exports can be imported as new custom entries.

## Compact plan editing

The plan editor shows numbered action rows. Open a row to edit it, or use **Expand all / Collapse all**. Loading or duplicating a saved plan starts with its editors collapsed; newly added steps open automatically. The summary shows configured step count and explicit wait time, not an estimated run duration.

The information button previews values, ranges, tolerances, and response timeouts on hover, keyboard focus, or tap. Escape dismisses the preview. Validation messages remain visible when an invalid step is collapsed and prevent saving until corrected. Reordering and removal preserve the edited steps and track which editors are open. Saved library cards hide their step indexes until **View steps** is selected; each saved row can be expanded or previewed independently.

## Results and event logs

Select **Inspect** in Results to open a report with a prominent verdict, passed-check count, total elapsed time, and output restoration status. Expand a step for recorded expected and actual values, a range/target marker, execution timing, and its explanation. Failed steps and validation checks open automatically. Charts show discrete recorded measurements, not continuous telemetry. Total elapsed time includes scheduling; step timing measures execution (including an explicit wait). Browser simulation steps execute immediately and report 0 ms. Older reports explicitly indicate unavailable fields.

**Rerun test** uses the original target device and plan identifier with their current settings. It requires a connected target, operator/admin access, an available matching plan, and an idle engine. Changed device settings, attached peripherals, or saved-plan versions require confirmation. Removed devices/plans cannot be rerun. A rerun creates a separate history record. Exporting a run includes its original captured configuration and all recorded metrics.

**View run logs** opens Activity log filtered to the report. Logs support text search, severity, device, run, local date/time bounds, and newest/oldest/errors-first sorting. Export logs exports all matching events in the selected order. Filters combine; clear filters restores the complete retained stream. New server events and simulated run events have structured device/run identifiers. Older events without identifiers remain available in the full stream but cannot be attributed reliably by those filters. The event history retains at most 250 entries.

## Connection diagnostics

The selected device inspector includes **Test connection** for operators and admins. It reads telemetry through the existing adapter without sending an output command or opening a disconnected transport. Connect the device explicitly first. Checks are blocked while a test is running.

The panel shows the adapter, endpoint, last recorded successful response, and up to five checks with timestamps and durations. A response outside the profile range is a warning; a timeout or disconnected device is a failure. Simulator timings describe an immediate simulated read, not network latency. Use fault injection to exercise timeout, out-of-range readings, and recovery. Diagnostic history persists with the selected workspace, is included in exports, and remains historical after a restart; connection state still resets to disconnected.

`POST /api/lab/devices/<id>/diagnostics` returns the updated workspace. An executed failed check is recorded with HTTP 200; forbidden, missing-device, and running-test requests use the normal API errors. Diagnostic checks are separate from test runs and do not count toward run pass rates.

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

The test bench uses an instrument-style panel: choose an input, connect it, select a compatible saved or built-in plan, and review engine/connection/sequence/access readiness before running. The signal display shows up to 40 recent received readings from the selected connected device; it issues no reads and does not advance emulator scenarios. Its horizontal axis is sample order, not a calibrated timebase, and it is not an oscilloscope. Expand emulator setup to apply, restart, or clear a response sequence. Run progress, per-step outcomes, report/export actions, and a repeat-selected-setup action appear below the controls. Repeated tests continue the scenario at its current cursor unless explicitly restarted.

1. Connect the Flask workspace through Settings.
2. Select **Connect bench**. This bulk action connects simulated devices only.
3. Run **Connection & health** on the temperature sensor, valve, or relay. Inspect the handshake, telemetry, and range checks.
4. Inject **Transport timeout** or **Out-of-range reading** and run again. Checks fail with an observed reason.
5. Clear the fault and run **Control response**. The engine sends a command, reads the response, verifies it, then restores the original output.
6. Reload or close the page during a server test. The test continues on Flask. Return to inspect its result.
7. Cancel a test, add/remove devices, control the valve/relay, filter logs, and export results.
8. Stop and restart Flask. Stored history persists. Devices disconnect, interrupted tests become cancelled, and simulated outputs recover to their saved values.

Server state retains 100 runs and 250 events. Exports are portable JSON reports/backups; the plan library supports importing and editing custom plans. Polling uses a state revision to reject old responses. A backend outage visibly disables commands; it never falls back to a fake successful result.

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

Remaining work includes physical-device validation, TLS/authenticated MQTT, device-specific protocol adapters, and migration of firmware/legacy dashboard features. This is a working local test product foundation; production multiuser deployment and arbitrary hardware compatibility are not claimed.

## Accounts, roles, and environment identity

Authentication is enabled by default for normal local and Docker servers. In Flask mode the first launch asks you to create an admin account; there is no default password or open registration afterward. Usernames contain 3–50 letters, numbers, dots, underscores, or hyphens and are stored in lowercase. Passwords require 12–128 characters. The original `UserManagementService` create/list/authenticate methods are used with a workbench repository, and the existing email validator is reused. Legacy accounts in the older database are not automatically migrated.

In **Settings**, the hardware-inspired account index shows one to five compact rows per page. Select a row to expand its full record, access controls, and optional password reset. Search names or emails, filter by role and status, and use the page controls to browse larger directories. The signed-in account is marked YOU. Admins create accounts, choose their role, enable/disable them, and reset passwords. The last enabled admin cannot be disabled or demoted. Account changes are version checked. Password resets and disabling accounts revoke sessions; role changes apply on the next server request and update the UI when its session poll refreshes. Signed-in users can sign out in Settings. Running tests continue after sign-out, and new authenticated runs record their initiating account in the result.

| Role | Permissions |
| --- | --- |
| Viewer | Read devices, plans, blueprints, logs, and results; export reports. |
| Operator | Viewer permissions plus connect/disconnect, control outputs, inject simulator faults, run and cancel tests. |
| Admin | Operator permissions plus device/configuration CRUD, workspace reset, and account management. |

Flask enforces every shared-workspace operation even if a caller bypasses React. The private browser simulator remains independent of the authenticated server and cannot control its hardware. Read-only library views remain available to viewers/operators; editing requires admin.

Accounts and sessions persist in separate SQLite tables alongside the bench. They survive workspace reset and are excluded from workspace exports. Passwords use Werkzeug's salted scrypt hashing. Sessions use random opaque tokens stored as hashes, last eight hours, and are sent only in HttpOnly, SameSite=Strict cookies. Each database has its own cookie name so two environments on different localhost ports do not overwrite each other's login. Mutating authenticated requests require a session-bound `X-CSRF-Token`; the existing origin/JSON checks remain active. Failed login attempts are limited to five per username/client address in ten minutes.

`LAB_AUTH_ENABLED=false` explicitly opts into unrestricted local development mode; automated non-auth regression servers use this setting. `LAB_COOKIE_SECURE=true` requires HTTPS cookies when deployed behind HTTPS. For the documented loopback HTTP setup it defaults to false. A configured `LAB_API_TOKEN` remains an additional gate for lab routes, and does not replace user login when accounts are enabled. The old legacy-dashboard authentication/API contract is still separate.

**Settings → Environment and build** shows application version, a frontend source fingerprint and build time, backend source fingerprint, backend address, deployment type, and persistent workspace instance ID. `/api/version` exposes only that build information; it contains no filesystem paths, credentials, or bench data. Frontend fingerprints are calculated at build/dev-server startup; rebuild or restart to refresh them after source changes. Backend fingerprints are calculated at server startup. Optional `VITE_BUILD_ID` and `LAB_BUILD_ID` override source fingerprints for deployment labels.

Rebuild Docker normally with `.\start-workbench.ps1 -Docker`, open http://localhost:8080, and create an admin for that separate Docker workspace. For authenticated MQTT verification, provide an admin account through `LAB_SMOKE_USERNAME` and `LAB_SMOKE_PASSWORD` environment variables in your PowerShell session, then use `.\start-workbench.ps1 -Docker -Verify`. The script forwards those environment variables by name; the smoke checker logs in using a cookie session and CSRF token. It does not create an admin or print credentials. Clear the environment variables afterward. Without them, authenticated verification reports how to configure it and performs no device commands.

Auth APIs: `/api/auth/session` GET; `/api/auth/setup`, `/login`, `/logout` POST; `/api/auth/users` GET/POST; `/api/auth/users/<id>` PATCH. User creation takes username/email/password/role. PATCH supports role, enabled, and optional password, plus the current version. Logout and administrative mutations require the CSRF header. Run auth browser verification with `npx playwright test -c playwright.auth.config.ts` in frontend.

## Editable test plans and reproducible results

Saved plans use a compact card catalog with 1–5 cards per page. Search names and descriptions, filter by device profile or included action, and sort by name, step count, or version. The labeled color strip previews each sequence; open a card for description, checks, configured waits, expandable step details, and edit/duplicate/export/delete actions. Saving or importing reveals the saved card; editing moves focus to the plan editor. Existing permissions, version checks, and result snapshots still apply.

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

Saved blueprints use expandable cards with 1–5 visible per page. Search blueprint names, descriptions, or contained device names; filter by device profile and sort by name or device count. Each card previews its device mix and expands into a device lineup, import notes, and apply/export/delete actions. Import previews show notes immediately; saving an import or capturing a bench reveals the saved card. Applying adds disconnected simulations without replacing existing bench devices.

Select Flask mode in Settings, then open **Blueprints**. Preview a JSON file before saving it to the library. Supported input layouts are root `peripherals`, `controller.peripherals`, and canonical `devices`. Temperature sensors, valves, and relays become disconnected simulated devices when you select **Add to bench**. Generic `Sensor` entries with temperature in their name map to temperature profiles with a visible warning. Unsupported definitions remain in the sanitized source configuration and are reported in the preview; their commands are not executed. Credential fields are excluded from saved/exported blueprints. Original protocol/connection definitions remain metadata and do not open physical connections.

**Save current bench** captures device profiles and peripheral properties for reuse. Applying a saved blueprint appends devices without replacing the bench. Saved blueprints survive workspace reset; reset clears attached peripherals along with devices, history, and logs. Deleting a device also removes its attached peripheral settings.

The workbench routes call the existing `PeripheralService` CRUD methods using an injected SQLite workspace repository, and `BlueprintService.normalize_configuration` uses the original `validate_json` utility. Legacy SQLAlchemy implementations remain opt-in. Utility modules now load individually instead of eagerly importing hardware, deployment, and database modules during startup. The legacy machine-scanning operation is not exposed by these new routes.

Peripheral `threshold` settings affect server health/control operating-range checks. A number is an upper bound; an object can contain `min`, `max`, or both. A missing bound is unbounded. When several peripherals specify limits for one device, every limit must pass. Without configured thresholds, profile defaults apply (temperature 0–50, valve 0–100, relay 0–1). Other properties remain metadata. Control command limits still follow the device profile. Configuration changes are blocked during a run, and stale peripheral edits/deletes receive HTTP 409 instead of overwriting a newer version.

API routes: `/api/lab/blueprints` (GET/POST), `/preview` and `/capture` beneath that path (POST), `/api/lab/blueprints/<id>/apply` (POST), `/api/lab/blueprints/<id>` (DELETE); `/api/lab/peripherals` (GET/POST), `/api/lab/peripherals/<id>` (PATCH/DELETE). PATCH and peripheral DELETE require the current `version`. Blueprint requests wrap input in `configuration`; capture takes `name` and optional `description`.

## Saved validation suites

Open **Validation suites** (`/suites`) in Flask mode. Save the starter suite, connect a matching simulated device on the bench, select the saved suite and device, and run it. Administrators create, edit, duplicate, and delete suites; operators run and stop them; viewers inspect reports. Suites support built-in or compatible saved plans, 1–10 named cases, up to 3 attempts per case, and 20 attempts total.

The editor and saved catalog each collapse independently. Cases expand individually or together, retaining draft edits when collapsed; compact rows show their scenario and expected outcomes. Browse saved suites with search, profile and expectation filters, sorting, and 1–5 cards per page. Open a card to inspect its cases, select it for a run, edit, duplicate, export, or delete it. Saving reveals the updated card automatically. Missing dependencies and invalid case names remain visible in the editor.

Each case applies a fresh snapshot of its chosen scenario at cursor zero. Multiple attempts within that case continue the sequence, allowing expectations such as **Fail → Pass** for timeout recovery. The runner compares the entire test outcome with each expectation: an expected failure earns **Expected failure detected**, while an unexpected pass or failure makes the suite fail. A fail expectation matches any failed test; inspect the embedded test report to confirm its cause. The original short **Bad telemetry** preset can recover before the built-in health plan reaches its range check; use **Sustained bad telemetry** for repeatable rejection checks.

The suite holds the shared bench for its duration. Other workspace commands and library edits are rejected until it completes or is stopped. Runs continue when the page closes or reloads. Completion, cancellation, and server restart restore the device's original simulation output, fault, applied scenario snapshot, and cursor; server restart cancels interrupted suites and disconnects devices. Suites never open physical transports. Restarting a saved suite uses current source versions; missing plans/scenarios must be replaced before running.

The last 10 suite reports retain independent suite/plan/scenario snapshots and full test results, including results that have aged out of ordinary run history. Export a complete report as `validation-suite-report.json`. Saved suite definitions survive workspace reset; reset clears their run reports along with normal history. There are up to 100 saved definitions, with version checks on edits and deletes.

API: POST `/api/lab/validation-suites`; PUT/DELETE `/api/lab/validation-suites/<id>` with `version`; POST `/api/lab/validation-suites/<id>/run` with `deviceId`; POST `/api/lab/suite-runs/cancel`. Definitions and reports are included in `/api/lab` as `validationSuites` and `suiteRuns`. The normal run-cancel endpoint also stops an owning suite.

## Product regression checks

Keep `work/` ignored. Reusable checks live in tracked `backend/tests/workbench`, `frontend/tests`, and the Playwright configurations. Temporary databases, traces, and scratch files are disposable artifacts, not source code or a list of outstanding work.

After the development environment and Playwright Chromium are installed, run `./regression.ps1` from the repository root in PowerShell. It stops on the first failed group and checks backend tests/Black, frontend formatting, simulator unit tests, the production build, browser workflows, Flask integration, and account permissions. Use `./regression.ps1 -SkipBrowsers` for the backend/unit/build checks only. Browser tests use isolated test ports 5001, 5003, 5174, 5175, and 5176; leave those free. The normal development app at 5000/5173 is not used by this command. Test databases stay under `work/`; browser groups use separate ignored output folders.

## Code formatting

The workbench uses Prettier for TypeScript, JSX, CSS, frontend tests, and Vite/Playwright configuration. From `frontend`, run `npm run format` to format or `npm run format:check` to verify. Prettier is pinned in the development dependencies; run `npm ci` after pulling the formatting setup.

The Python workbench modules and regression tests use Black with an 88-column target. From `backend`, install development tools with `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`, then run `.\.venv\Scripts\python.exe -m black .` or add `--check` to verify. The Black include pattern scopes this command to the workbench files. Black is a development dependency and is not added to the Docker runtime.

The root `.editorconfig` specifies UTF-8, final newlines, two-space frontend indentation, and four-space Python indentation. Formatters may retain individual long strings where wrapping would change their contents.
