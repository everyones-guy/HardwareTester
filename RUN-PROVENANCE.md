# System runs and run provenance

Open **Test bench** in Flask mode as an operator or administrator. Choose a
firmware release if you want its library SHA-256 and version recorded. The
selected release is attribution to a library artifact. Confirming what is
installed on a connected target requires separate evidence.

For the two-valve, pump, and temperature demo, expand **Run a multi-device
system plan**. Choose `deployment/plans/controller-start-stop.json` and
`deployment/fixtures/controller-start-stop.json`, then run the plan. The
Workbench opens **Results** while the run proceeds. **Run provenance** shows
the account, selected release, provider roles, correlated requests, and the
restoration result for each touched relay. Export the report to retain its
full audit data.

Ordinary Flask device tests share the same report fields. MQTT and serial
records retain the request ID used by the adapter. Simulation gives each
request a local ID. A failed exchange records the attempted ID and error.
A run retains its first 256 exchanges and counts any later ones. Earlier
reports display the data they recorded at the time.

## Connected system runs

Use `POST /api/lab/system-runs` or the same Test bench form for a reviewed
connected setup. The payload has `plan`, `bench`, and an optional
`releaseSha256`. Use the same plan definition on each provider. The Workbench
compares system runs by the canonical plan digest. Select the other bench
under **Compare & track** to compare the corresponding checks.

A connected binding names an already registered and connected Workbench
device for every role. `LAB_ALLOW_HARDWARE` must be enabled for that workspace.
Assign each role its own endpoint. A `commandRelay` needs
`approvedCommandRelay: true`. A `faultRelay` needs `approvedFaultRelay: true`.
Telemetry roles only need `deviceId`. In this abbreviated example, replace
the device IDs with the IDs of your approved bench. A full binding lists every
role declared by the selected plan.

```json
{
  "mode": "connected",
  "devices": {
    "controllerEnable": {"deviceId": "controller-relay-id", "approvedCommandRelay": true},
    "temperatureFaultRelay": {"deviceId": "fault-relay-id", "approvedFaultRelay": true},
    "temperatureSensor": {"deviceId": "sensor-id"}
  }
}
```

The authenticated launch reserves the bench for the system plan. Cancel from
the Test bench to stop further steps and verify restoration of any relay
already touched. Cancellation waits for the current bounded exchange. A
restart during a connected run marks affected relay outputs for inspection.

The existing `python -m tools.run_system_plan` command uses the same execution
logic and includes request provenance in its local report. Local CLI runs
have no authenticated Workbench operator. Use the Workbench launch for an
attributable run in shared history.
