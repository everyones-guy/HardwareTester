# Hardware Tester

A shared hardware test bench with a React workbench, Flask/SQLite persistence,
reusable test plans and emulator scenarios, validation suites, graphical results,
and role-based administration. Simulation works without physical hardware; the
Docker stack includes Mosquitto and a mock MQTT valve for transport testing.

## Start the bench

With Docker Desktop running **Linux containers**, run from this directory:

```powershell
docker compose up --build -d --wait --wait-timeout 180
```

Open [Hardware Tester](http://localhost:8080) and create the first administrator.
Use **Test bench > Start guided setup** for your first simulated test. To exercise
MQTT, add a valve with endpoint `mqtt://broker:1883/lab/demo-valve`, connect it,
and run **Control response**.

The four services are the web workbench, backend, broker, and MQTT fixture.
`docker compose stop` stops them; the startup command restarts them and builds
updates. `docker compose down` removes containers while keeping saved data in the
project's `lab-data` volume. Do not add `--volumes` when stopping your normal bench.
Ports default to loopback 8080 (web) and 1883 (MQTT); `LAB_HTTP_PORT` and
`LAB_MQTT_PORT` can select alternatives for separate installations. Each
installation needs its own Compose project name and free ports.

## Check a release from a clean installation

```powershell
.\release-check.ps1
```

Requires Docker Compose v2 with `up --wait` support. No host Python or Node
installation is needed. The check builds two randomly named disposable stacks,
uses automatically allocated loopback ports and separate volumes, and ignores
the normal `.env`. Your existing bench can keep running.

It checks all four services become healthy, compiled frontend assets load,
first-admin setup, an operator account, saved plans/scenarios/suites, healthy and
expected-failure outcomes, recovery, MQTT command/verification/output restoration,
persistence after a full stack restart, and archive recovery into a second fresh
installation. The restored suite must run successfully and target accounts must
remain independent. Imported and restarted devices must be disconnected.

Test containers and volumes are removed on success or failure. Ignored
`work/release-check/<run-id>/` retains the test workspace archive and a result or
failure diagnostics. Generated passwords remain inside disposable volumes.
Failures return a PowerShell error; a passing message confirms that invocation,
not physical hardware compatibility. The release check exercises HTTP workflows;
browser interaction coverage lives in the regression suite.

## Develop and verify

For local development, run `./start-backend.ps1` and `./start-workbench.ps1` in
separate terminals. Open [the development workbench](http://localhost:5173).
Run `./regression.ps1` for backend, simulator, build, and browser regression checks.

See [WORKBENCH.md](WORKBENCH.md) for features, roles, backups, physical transport
protocols, configuration, and verification details. The older universal setup
scripts and legacy Docker files belong to the original application; they are
unnecessary for the current workbench. PostgreSQL, Kubernetes, and a separate WSL
shell are not required for this stack.
