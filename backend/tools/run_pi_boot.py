"""Check a Raspberry Pi 3B direct kernel boot against a guest serial marker."""

import argparse
import hashlib
import json
import re
import stat
import subprocess
import threading
import time
from pathlib import Path

MACHINE = "raspi3b"
QEMU = "qemu-system-aarch64"
BUNDLE = Path("/artifacts")
KERNEL = "kernel8.img"
DTB = "bcm2710-rpi-3-b.dtb"
DISK = "sd.img"
INITRD = "initrd.img"
SERIAL_LIMIT = 8192
DIAGNOSTIC_LIMIT = 4096
ROOT_DEVICE = re.compile(r"(?:/dev/mmcblk0p[1-9][0-9]*|PARTUUID=[a-fA-F0-9-]+)")


def fingerprint(path):
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or not info.st_size:
        raise ValueError(f"{path.name} must be a nonempty regular file.")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def verify_bundle(bundle, fingerprints):
    for name, prior in fingerprints.items():
        if fingerprint(bundle / name) != prior:
            raise ValueError(f"{name} changed while the runner was using it.")


def hash_bundle(bundle):
    names = [KERNEL, DTB, DISK]
    optional_initrd = bundle / INITRD
    if optional_initrd.exists() or optional_initrd.is_symlink():
        names.append(INITRD)
    fingerprints = {name: fingerprint(bundle / name) for name in names}
    disk_size = fingerprints[DISK][2]
    if disk_size < 512 or disk_size & (disk_size - 1):
        raise ValueError("sd.img must have a power-of-two size of at least 512 bytes.")
    artifacts = {}
    for name in names:
        with (bundle / name).open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        artifacts[name] = {"sha256": digest, "sizeBytes": fingerprints[name][2]}
    verify_bundle(bundle, fingerprints)
    return artifacts, fingerprints


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
        "--ready-marker",
        required=True,
        help="Exact newline-terminated guest serial line",
    )
    parser.add_argument("--boot-timeout", type=int, default=120, metavar="SECONDS")
    parser.add_argument("--root-device", default="/dev/mmcblk0p2")
    args = parser.parse_args()
    if not 1 <= args.boot_timeout <= 600:
        parser.error("--boot-timeout must be 1–600 seconds.")
    if not args.ready_marker.strip() or not re.fullmatch(
        r"[ -~]{1,128}", args.ready_marker
    ):
        parser.error("--ready-marker must contain 1–128 printable ASCII characters.")
    if not ROOT_DEVICE.fullmatch(args.root_device):
        parser.error("--root-device must be a Pi SD partition or PARTUUID= identifier.")
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
    try:
        version = subprocess.check_output([QEMU, "--version"], timeout=5)
        version_line, _, _ = version.decode("utf-8", errors="replace").partition("\n")
        version_line = version_line.strip()
        if not version_line:
            raise ValueError("QEMU returned no version information.")
        report["emulatorVersion"] = version_line[:256]
        artifacts, fingerprints = hash_bundle(BUNDLE)
        report["artifacts"] = artifacts
        command = boot_command(QEMU, BUNDLE, args.root_device, INITRD in artifacts)
        result = check_boot(command, args.ready_marker, args.boot_timeout)
        verify_bundle(BUNDLE, fingerprints)
        report.update(result)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report.update(verdict="error", reason="runnerError", error=str(error))
    print(json.dumps(report))
    return {"passed": 0, "failed": 1, "error": 2}[report["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
