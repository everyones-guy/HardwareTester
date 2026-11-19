# Raspberry Pi testing

Use the shared workbench to inspect a Pi inventory and check it against expected
properties. Use the separate QEMU runner to check boot milestones on compatible
Pi 3 Model B image variants. Each boot starts from the supplied image with
temporary writes, so a tester can change versions by choosing another bundle.

## Capture and check inventory

On the Pi, run the collector from the repository root as a regular user:

```bash
python3 backend/tools/capture_pi_inventory.py > pi-inventory.json
```

You can also stream the collector to a Pi over SSH. Use an approved host with a
verified key already in `known_hosts` and key-based login. From Bash:

```bash
ssh -T -o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=10 \
  USER@PI_HOST python3 - < backend/tools/capture_pi_inventory.py > pi-inventory.json
```

From PowerShell 7.4 or later:

```powershell
Get-Content -Raw -LiteralPath .\backend\tools\capture_pi_inventory.py |
  ssh -T -o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=10 USER@PI_HOST python3 - |
  Set-Content -Encoding utf8NoBOM -LiteralPath .\pi-inventory.json
```

In the Flask workbench, open **Raspberry Pi**. An administrator names and imports
the JSON. Viewers can inspect the model, kernel architecture, OS release,
Linux-visible memory, capture time, and interface categories. Operators and
administrators can run the recommended OS and architecture checks, the Pi 3B
boot-candidate check, and custom assertions on inventory values. The results show
the expected value and the recorded value. A new capture gives a new snapshot.

Inventory checks describe data at capture time. An observed I²C or GPIO interface
indicates that Linux exposes it. Verify attached peripherals and wiring separately.
The Pi inventory library persists in the workspace SQLite database across restarts.
Keep the original JSON for sharing or restoring inventories. The workbench's
portable workspace archive covers the test bench and its existing libraries.

## Run a Pi 3B boot check

Have a lab device owner supply an approved 64-bit Raspberry Pi 3 Model B test
bundle. Build it from a sanitized golden image or a consistent lab snapshot.
Replace deployment credentials and device identity in the test image. Keep one
bundle per firmware or OS version with these filenames:

| File | Contents |
| --- | --- |
| `sd.img` | Raw Pi SD-card image with a power-of-two size in bytes. |
| `kernel8.img` | The matching 64-bit Pi 3B Linux kernel. |
| `bcm2710-rpi-3-b.dtb` | The matching QEMU-compatible Pi 3B device tree, with the PL011 serial console available. |
| `initrd.img` | Matching initramfs, if the image needs one. |

Configure your guest test service to write the exact line
`HARDWARETESTER_BOOT_READY` to the PL011 console after the milestone you care
about. A stock image may require a guest-side test fixture to emit this line.
Use serial evidence for a testable milestone such as completing application
startup with local fixtures.

Start Docker Desktop in Linux container mode. Build the runner from the repo root
and run a bundle from PowerShell:

```powershell
docker build -f deployment/Dockerfile.pi-runner -t hardware-tester-pi-runner .

$bundle = (Resolve-Path 'C:\path\to\approved-pi3b-bundle').Path
docker run --rm --init --read-only --network none --cap-drop ALL `
  --security-opt no-new-privileges --memory 2g --cpus 2 --pids-limit 128 `
  --tmpfs /var/tmp:rw,noexec,nosuid,nodev,size=512m,mode=1777 `
  --mount "type=bind,src=$bundle,dst=/artifacts,readonly" `
  hardware-tester-pi-runner --ready-marker HARDWARETESTER_BOOT_READY |
  Set-Content -Encoding utf8NoBOM -LiteralPath .\boot-report.json
```

The runner defaults to `/dev/mmcblk0p2` for the root filesystem and 120 seconds
for boot. Override with `--root-device` or `--boot-timeout`. It outputs a JSON
report with the QEMU version, machine, SHA-256 of each artifact, verdict, and a
bounded serial log. Exit code 0 means the marker was observed, 1 means the boot
check failed, and 2 means a runner error. Docker can return its own exit code if
the container fails to start. Keep the JSON with the corresponding test run.

This is a direct Linux kernel boot. It bypasses the physical Pi's EEPROM and
boot firmware. The guest uses a Pi 3B QEMU machine with a virtual SD card and
serial console, with networking disabled for this boot check. The passed marker
establishes only that the configured guest milestone was observed. QEMU support
for Pi boards and devices depends on the version. [QEMU Raspberry Pi boards](https://www.qemu.org/docs/master/system/arm/raspi.html)

## Ecolab acceptance

Use the first real controller inventory, approved image, and peripheral list to
define a bootable baseline and one second version. Use both versions to verify
the same guest milestone and one Ecolab-specific application check. The workbench
already has MQTT fixtures, scenarios, and validation suites for protocol behavior
that can be reproduced against a simulated peer. Board revisions, electrical
behavior, and external relays or sensors require a connected physical fixture.
A shared lab fixture lets testers queue those checks remotely while running
software-only regressions on isolated image variants.

## Test a controller and its peripherals

Provision an additional Pi with the [Raspberry Pi OS bootstrap](deployment/raspberry-pi/README.md).
To exercise the complete sequence with the included two-state demo model, run
from `backend` with the workbench Python environment:

```powershell
python -m tools.run_system_plan `
  --plan ..\deployment\plans\controller-sensor-fault.json `
  --bench ..\deployment\fixtures\controller-sensor-fault.json `
  --report .\modeled-sensor-fault.json
```

The plan checks two valve positions, temperature, and the running pump. Its
only write enables or clears the fault relay. The next checks observe whether
the pump stopped and the valves closed. The example's positions, timing, and
temperature are sample requirements. Use the approved controller requirements
when creating an Ecolab plan. The modeled run exercises the test sequence and
report. It uses configured responses for both sensor states.

On a dedicated rack, make a bench JSON file with `mode` set to `connected` and
a `devices` object keyed by all five role names from the plan. Each entry has
`adapter` (`mqtt` or `serial`) and `endpoint` (the workbench's `mqtt://` URL or
serial port). Serial bindings can declare `baudrate`. Bind `temperatureFaultRelay`
to a separately reviewed relay that isolates or substitutes the sensor signal.
Set `approvedFaultRelay` to `true` on that binding. The runner blocks before
opening devices if a binding or the approved fault relay is missing.

The same plan file runs against this bench. Use a new output filename for each run:

```powershell
python -m tools.run_system_plan `
  --plan ..\deployment\plans\controller-sensor-fault.json `
  --bench .\approved-rack-bindings.json `
  --allow-connected --reference .\modeled-sensor-fault.json `
  --report .\rack-sensor-fault.json
```

The report captures the plan, plan and binding hashes, expectations, readings,
timing, and fault-relay restoration. An unverified restoration requires
operator attention. A connected run compares its executed steps against a
reference generated from the same plan file. In the React workbench, ordinary
single-device results also support comparing different target devices for the
same plan under **Compare & track**.

For component-level simulation, the MQTT fixture accepts a declarative model
of guarded `read` and `set` commands with state transitions and delayed, missing,
or error replies. A sample valve model is at
[`deployment/fixtures/valve-state-machine.json`](deployment/fixtures/valve-state-machine.json).
Start the example next to the normal bench broker:

```powershell
docker compose run --rm --no-deps `
  -v "${PWD}/deployment/fixtures/valve-state-machine.json:/model.json:ro" `
  mqtt-fixture python tools/mqtt_fixture.py --broker broker --topic lab/valve-model --model /model.json
```

Use the same valve test plan on `mqtt://broker:1883/lab/valve-model` and a
physical valve speaking the workbench MQTT protocol. Connection and diagnostic
reads can advance the model when the active state has a read transition.

## Firmware library and rack programming

Administrators use **Firmware** to upload a `.bin` image up to 16 MiB with its
expected SHA-256, version, target board model and revision, and architecture.
Use the digest supplied with the approved build. Model and architecture match
against imported Pi inventory. Operators can export both the binary and its
manifest for rack programming. The binaries live next to the workbench
database. Retain both together for a full installation backup.

For an OpenOCD-supported NOR-flash target, configure the local rack before
programming. The profile is a JSON file with `schemaVersion` 1, `model`,
`architecture`, `targetIdentity`, `openocdConfig`, `flashAddress` (hex string),
`maxRegionBytes`, `eraseBlockBytes`, and `timeoutSeconds`. Derive the address
and complete, uniformly sized erase blocks from the actual board's flash
layout. Use a dedicated firmware region. The trusted local OpenOCD `.cfg`
configures the adapter, board, and target. Its `hardware_tester_probe` Tcl
procedure must read a live board identifier and return the exact approved
`targetIdentity`. Configure adapter selection in the board profile and use
a board/revision-specific identity supported by the hardware.

From the repository root, preflight the binary on the rack:

```powershell
python backend/tools/flash_openocd.py --profile .\rack-profile.json `
  --manifest .\approved-firmware.json --binary .\approved-firmware.bin `
  --report .\flash-preflight.jsonl
```

For a permitted programming cycle on the lab target, supply `--apply` and a
fresh report filename. Optionally supply `--recovery-manifest` and
`--recovery-binary` for a known-good approved image. The tool checks live
identity, writes, verifies flash contents, and resets into run mode after
verification. With recovery configured, a completed write followed by failed
verification can trigger a separate recovery attempt. The recovery attempt
checks the live identity and verifies the known-good image. A write failure or
unknown device state requires rack inspection. Review the JSONL attempt log
and use the target's documented recovery procedure. [OpenOCD programming](https://openocd.org/doc/html/Flash-Programming.html)

## Hardware and firmware catalog design

The universal workbench should open a saved machine configuration with its
controller and peripherals already filled in wherever inventory and catalog
records agree. A tester can review unresolved devices, choose firmware from a
compatible-versions dropdown, select a test plan, and queue a run.

| Record | Data the workbench needs |
| --- | --- |
| Machine inventory | Source and capture time, board model and revision, CPU and architecture, OS/kernel, and enumerated device identifiers. A tester identifies devices on buses without reliable enumeration. |
| Hardware profile | Manufacturer, part number, revisions, bus/protocol, documented limits, and references to the source specification and its revision. |
| Firmware or OS build | Version, architecture, supported board revisions, boot requirements, and immutable artifact digest. |
| Fixture | Supported devices and commands, modeled ranges and faults, and the available backends for QEMU, protocol simulation, or a remote rack. |
| Bench configuration | Controller, approved hardware/firmware pairs, wiring or connection model, firmware digests, and fixture versions. |

Import approved spec bundles into a review queue. Extract proposed part numbers,
board revisions, interfaces, limits, and firmware compatibility with page or
section references. Publish reviewed entries to the catalog. When a capture has
a stable identifier, match it against that catalog. An interface without a part
identifier can suggest candidates for review. Conflicting revisions and missing
compatibility metadata stay visible with the reason the pair needs review.

Recommend tests from the selected bench's declared capabilities. Specialized
Ecolab suites can exercise documented behavior and failure limits, while custom
plans reuse the workbench's declarative assertions. Record the resolved bench,
test plan version, artifacts, and execution backend with every result. A required
capability that the selected backend cannot exercise should show as blocked.
