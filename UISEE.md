# UISee and compiled controller testing

The workbench reads UTF-8 UISee SQL source files containing `PagesInstalled`
and `WidgetsInstalled` inserts. It extracts the original page and widget IDs,
names, resource tags, and file and line references. Numeric controls need
source-declared `MinValue`, `MaxValue`, and `Step`. Imports accept up to 16 files
and 512 KiB of SQL text. Discovery parses the data without executing SQL or
JavaScript, and leaves unsupported or ambiguous records in the discovery messages.

## Discover a control and bind its handler

The two example SQL files under `deployment/ui-fixtures/uisee-controller` use
the legacy UISee schema. They are synthetic. A real package should come from one
approved firmware release, together with the source or interface contract for
the handler that the touchscreen calls.

1. Open **UISee** in Flask mode as an administrator. Give the catalog a name and
   import both example SQL files. Select the **Valve Station** page and the
   discovered **ValveTarget** control. Its numeric range, original IDs, handler
   hint and SQL location come from the imported rows.
2. Review the handler against the provider contract. With the example, the
   `setValveTarget` implementation is in
   `deployment/firmware-fixtures/uisee-controller/controller.cpp`. Save a
   reviewed binding to the **Valve** profile and enter the source reference.
   A handler hint can name an action. The reviewed binding selects the existing
   typed Workbench operation and the compatible device profile.
3. Enter `54` for Command value and `54` for Expected device reading. Confirm
   and save the test, select a connected compatible valve, and run it. The plan
   reads the initial output, sends the setpoint and waits for acknowledgment,
   then checks an independent device readback. Workbench restores the previous
   setpoint and records the result. Generate a second plan with expected `55`
   to verify that a bad expectation fails against an observed `54`.
4. Export the saved plan from **Plan library**. Importing the unchanged JSON
   preserves source provenance. A generated test stores the catalog SHA-256,
   control ID, handler, reviewed reference, SQL location and step digest. The
   result captures the plan and target. Editing the steps in the standard plan
   editor clears the original source-generated attribution.

Import a second release as its own catalog to compare pages and controls. The
comparison reports additions, removals and changes using original IDs. Shared
names under different IDs are shown for review. The catalogs and reviews live
in the server SQLite database. Portable workspace backups preserve generated
plans and runs. Retain the SQL sources and binding references to reconstruct a
catalog in another installation.

## Run the compiled fixture

Use a separate Docker Compose project from the repository root. The compiled
fixture is a reviewed local C++ program for a synthetic valve. Its bridge uses
HardwareTester's normal MQTT protocol and runs the fixed executable built by the
image. [Compiled fixture setup and smoke check](deployment/firmware-fixtures/uisee-controller/README.md)

Start `workbench` and `compiled-controller` in that disposable project. Add a
**Valve** with the **MQTT** adapter and endpoint
`mqtt://broker:1883/lab/compiled-valve`, then connect it. The UISee workflow uses
the same plan definition on this target and the in-memory valve simulator. This
fixture verifies the compiled handler and its reported setpoint. Physical valve
travel, pump interlocks, sensor calibration and safety timing require the
approved controller, wiring and independent measurements.

## Legacy archive intake

Legacy firmware source inspection stages files privately and publishes the
extraction only after validation. It rejects absolute and parent paths, links,
special files, filename collisions, encrypted ZIP entries and expansion past
the configured limits. It supports ZIP source bundles, the historical
ZIP-wrapped `.img` convention, `newc` and CRC CPIO, and version 4 RPM with a
gzip, bzip2 or uncompressed CPIO payload. Unsupported compressors require a
separate reviewed unpacking workflow. Raw disk images belong to the Pi boot
workflow. Archive extraction performs structural validation. Release identity
and signing trust need an approved manifest and trust anchors.

## Multi-device sequence

The synthetic controller bench includes two valves, a temperature sensor and a
pump. Its finite states respond to a controller enable relay and two distinct
fault relays. From `backend`, run the normal start and stop and then exercise
the sensor and stuck-outlet paths:

```powershell
python -m tools.run_system_plan `
  --plan ..\deployment\plans\controller-start-stop.json `
  --bench ..\deployment\fixtures\controller-start-stop.json `
  --report .\controller-start-stop-report.json
```

The expectation values describe the synthetic bench. On an approved connected
bench, use compatible MQTT or serial role bindings with `approvedCommandRelay`
on the controller enable binding and `approvedFaultRelay` on each fault
binding. The runner verifies acknowledgments and restores the initial relay
states. Reports record which steps passed and which restoration checks need
operator review.

GitHub Actions runs backend and frontend checks without hardware and builds
the compiled fixture in a disposable Compose project. Its artifacts include
test results, the compiled fixture's SHA-256 and the static ELF report.
