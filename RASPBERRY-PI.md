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

Administrators use **Firmware** to upload a `.bin` image or a `.zip` release
bundle up to 16 MiB. Enter the expected SHA-256 supplied with the approved
build, version, target board model and revision, and architecture. A release
bundle can include source, build manifests, executables, libraries, service
definitions, and UI resources. ZIP entries must be regular files or directories
using stored or deflated compression. A bundle can expand to at most 64 MiB
across 512 entries, with a 16 MiB limit per file.

Open **Inspect release** to see file hashes, source and manifest evidence, ELF
headers and linked libraries. The scan reads file data and records uncertainty
when format or architecture is unrecognized. Libraries absent from the bundle
may be provided by the target operating system. Supported SQL sources link to
their discovered UI catalog. A previously saved binary can be reuploaded
with its exact metadata and digest to add an inspection.

Choose a saved Pi capture, then select a **Compatible firmware** candidate.
Pairing uses the declared board model and revision, declared architecture, and
any available ELF headers. An exact declaration with no observed ELF is labeled
**Declared match**. Architecture conflicts are excluded and ambiguous ELF results
require review. The capture records kernel architecture. Bootability, userspace
compatibility, and live target identity require separate checks.

Operators can download hash-checked uploads and export the manifest. Use a
publisher-signed manifest with approved `.bin` images on the rack programmer.
Release ZIPs support inspection and
comparison. Firmware files live next to the Workbench database. Retain both
together for a full installation backup.

From an inspected release, export a runtime profile to review library
resolution and smoke-test approved binaries against a pinned Debian image.
[Pinned firmware smoke tests](FIRMWARE-RUNTIME.md)

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

Install the verifier on the rack operator's environment with
`python -m pip install -r backend/requirements-programmer.txt`. Obtain the
version 1 JSON manifest and detached Ed25519 signature from the release
publisher. The signer signs the exact UTF-8 manifest bytes, including
whitespace and line endings. The manifest includes the binary's SHA-256,
size, model, and architecture. A Workbench export can serve as the input to
the publisher's signing process.

The signature sidecar has `schemaVersion` set to `1`, a `keyId`, and a
`signature` containing the 64-byte signature as 128 lowercase hex characters.
For a Python Ed25519 signing key, this value is
`release_key.sign(manifest_path.read_bytes()).hex()`. The rack operator keeps
an independently provisioned trust store with `schemaVersion` set to `1` and
a `keys` object mapping each approved key ID to its raw 32-byte Ed25519 public
key in lowercase hex. For a Python Ed25519 public key, use
`public_key.public_bytes_raw().hex()`. Store only public keys on the rack and
manage the trust store separately from release bundles. [Ed25519 signing and verification](https://cryptography.io/en/50.0.2/hazmat/primitives/asymmetric/ed25519/)

From the repository root, preflight the signed binary on the rack:

```powershell
python backend/tools/flash_openocd.py --profile .\rack-profile.json `
  --manifest .\approved-firmware.json --binary .\approved-firmware.bin `
  --signature .\approved-firmware.signature.json `
  --trust-store .\trusted-publishers.json `
  --report .\flash-preflight.jsonl
```

Preflight checks the signature, image, and profile locally. For an approved
programming cycle, supply `--apply` and a fresh report filename. The tool checks
live identity before the write, verifies the programmed bytes, and then resets
into run mode. The JSONL report records the signer key ID, public key fingerprint,
manifest digest, programmer outcome, and the last confirmed target state.

Optional recovery requires `--recovery-manifest`, `--recovery-signature`, and
`--recovery-binary` for a distinct known-good image that covers the candidate's
erase blocks. The tool verifies both releases before it calls OpenOCD. It
attempts recovery once after a completed write and an explicit verification
failure. It checks the live identity again before the recovery write and
verifies the recovery bytes before reset. A timeout or interruption skips
automatic recovery. Review the report and inspect the rack when the target
state is unknown. A successful recovery still returns a failing exit code
for the requested deployment. [OpenOCD programming](https://openocd.org/doc/html/Flash-Programming.html)

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
