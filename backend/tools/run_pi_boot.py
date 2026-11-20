"""Check a Raspberry Pi 3B direct kernel boot against a guest serial marker."""

import argparse
import hashlib
import json
import subprocess
import threading
import time
from pathlib import Path

if __package__:
    from . import pi_provisioning as provisioning
else:
    import pi_provisioning as provisioning

MACHINE = provisioning.MACHINE
QEMU = "qemu-system-aarch64"
BUNDLE = Path("/artifacts")
KERNEL, DTB, DISK, INITRD = (
    provisioning.KERNEL,
    provisioning.DTB,
    provisioning.DISK,
    provisioning.INITRD,
)
SERIAL_LIMIT = 8192
DIAGNOSTIC_LIMIT = 4096


def boot_command(qemu, bundle, root, with_initrd):
    disk = str(bundle / DISK).replace(",", ",,")
    command = [
        qemu,
        "-machine",
        MACHINE,
        "-accel",
        "tcg",
        "-display",
        "none",
        "-monitor",
        "none",
        "-serial",
        "stdio",
        "-nic",
        "none",
        "-no-reboot",
        "-snapshot",
        "-kernel",
        str(bundle / KERNEL),
        "-dtb",
        str(bundle / DTB),
        "-drive",
        f"file={disk},format=raw,if=sd",
        "-append",
        f"console=ttyAMA0,115200 root={root} rootwait ro",
    ]
    if with_initrd:
        command.extend(["-initrd", str(bundle / INITRD)])
    return command


class OutputCapture:
    def __init__(self, limit, marker=None):
        self.limit = limit
        self.marker = marker
        self.tail = b""
        self.truncated = False
        self.matched = threading.Event()
        self.matched_at = None
        self.partial_line = b""
        self.read_failed = False

    def read(self, stream):
        try:
            with stream:
                while chunk := stream.read1(4096):
                    if len(self.tail) + len(chunk) > self.limit:
                        self.truncated = True
                    self.tail = (self.tail + chunk)[-self.limit :]
                    if self.marker is not None and not self.matched.is_set():
                        self.check_lines(chunk)
        except OSError:
            self.read_failed = True

    def check_lines(self, chunk):
        lines = chunk.split(b"\n")
        remainder = lines.pop()
        if lines:
            # An overflowed line cannot match, even if its final fragment does.
            prefix = self.partial_line
            lines[0] = b"" if prefix is None else prefix + lines[0]
            if any(line.removesuffix(b"\r") == self.marker for line in lines):
                self.matched_at = time.monotonic()
                self.matched.set()
                return
            self.partial_line = b""
        if self.partial_line is not None:
            partial = self.partial_line + remainder
            max_length = len(self.marker) + 1  # Allow the CR in CRLF.
            self.partial_line = partial if len(partial) <= max_length else None

    def as_text(self):
        return self.tail.decode("utf-8", errors="replace")


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)


def check_boot(command, marker, timeout_seconds):
    started = time.monotonic()
    deadline = started + timeout_seconds
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    serial = OutputCapture(SERIAL_LIMIT, marker.encode("ascii"))
    diagnostics = OutputCapture(DIAGNOSTIC_LIMIT)
    readers = [
        threading.Thread(target=capture.read, args=(stream,), daemon=True)
        for capture, stream in ((serial, process.stdout), (diagnostics, process.stderr))
    ]
    try:
        for reader in readers:
            reader.start()
        while process.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or serial.matched.wait(min(remaining, 0.05)):
                break
        natural_exit = process.poll()
        ended = time.monotonic()
    finally:
        stop(process)
        for reader in readers:
            reader.join(timeout=1)
    marker_observed = serial.matched_at is not None and serial.matched_at <= deadline
    if (
        serial.read_failed
        or diagnostics.read_failed
        or any(reader.is_alive() for reader in readers)
    ):
        verdict, reason = "error", "captureIncomplete"
    elif natural_exit not in (None, 0):
        verdict, reason = "error", "emulatorExitedWithError"
    elif marker_observed:
        verdict, reason = "passed", "serialMarkerObserved"
    elif ended >= deadline:
        verdict, reason = "failed", "bootTimedOut"
    else:
        verdict, reason = "failed", "emulatorExitedWithoutMarker"
    return {
        "verdict": verdict,
        "reason": reason,
        "markerObserved": marker_observed,
        "bootElapsedMs": round((ended - started) * 1000),
        "emulatorExitCode": natural_exit,
        "serialTail": serial.as_text(),
        "serialTruncated": serial.truncated,
        "emulatorStderrTail": diagnostics.as_text(),
        "emulatorStderrTruncated": diagnostics.truncated,
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        help="Use the boot settings and image pins in an exported plan.",
    )
    parser.add_argument(
        "--ready-marker",
        help="Exact newline-terminated guest serial line",
    )
    parser.add_argument("--boot-timeout", type=int, metavar="SECONDS")
    parser.add_argument("--root-device")
    args = parser.parse_args()
    overrides = (args.ready_marker, args.boot_timeout, args.root_device)
    if args.plan is not None and any(value is not None for value in overrides):
        parser.error("Boot settings come from the plan. Omit individual overrides.")
    if args.plan is None:
        args.boot_timeout = 120 if args.boot_timeout is None else args.boot_timeout
        args.root_device = (
            "/dev/mmcblk0p2" if args.root_device is None else args.root_device
        )
        try:
            provisioning.validate_boot(
                {
                    "readyMarker": args.ready_marker,
                    "timeoutSeconds": args.boot_timeout,
                    "rootDevice": args.root_device,
                }
            )
        except ValueError as error:
            parser.error(str(error))
    return args


def main():
    args = parse_args()
    report = {
        "schemaVersion": 1,
        "check": "directKernelSerialBoot",
        "machine": MACHINE,
        "rootDevice": args.root_device,
        "readyMarker": args.ready_marker,
        "bootTimeoutSeconds": args.boot_timeout,
        "emulatorVersion": None,
        "artifacts": {},
    }
    identity = None
    plan_checked = args.plan is None
    try:
        if args.plan is not None:
            plan = provisioning.validate_plan(provisioning.read_document(args.plan))
            report["rootDevice"] = plan["boot"]["rootDevice"]
            report["readyMarker"] = plan["boot"]["readyMarker"]
            report["bootTimeoutSeconds"] = plan["boot"]["timeoutSeconds"]
            identity = {
                "profile": plan["profile"],
                "release": plan["release"],
                "target": plan["target"],
                "planSha256": hashlib.sha256(
                    json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                "imagePinsVerified": False,
            }
            report["provisioning"] = identity
        artifacts, fingerprints = provisioning.hash_bundle(BUNDLE)
        report["artifacts"] = artifacts
        if identity is not None:
            provisioning.check_pins(artifacts, plan["artifacts"])
            identity["imagePinsVerified"] = True
        plan_checked = True
        version = subprocess.check_output([QEMU, "--version"], timeout=5)
        version_line, _, _ = version.decode("utf-8", errors="replace").partition("\n")
        version_line = version_line.strip()
        if not version_line:
            raise ValueError("QEMU returned no version information.")
        report["emulatorVersion"] = version_line[:256]
        command = boot_command(QEMU, BUNDLE, report["rootDevice"], INITRD in artifacts)
        result = check_boot(
            command, report["readyMarker"], report["bootTimeoutSeconds"]
        )
        provisioning.verify_bundle(BUNDLE, fingerprints)
        report.update(result)
    except (OSError, ValueError, RecursionError, subprocess.SubprocessError) as error:
        reason = "runnerError" if plan_checked else "provisioningPlanRejected"
        report.update(verdict="error", reason=reason, error=str(error))
    print(json.dumps(report))
    return {"passed": 0, "failed": 1, "error": 2}[report["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
