"""Preflight or program an approved NOR-flash binary on a dedicated OpenOCD rack."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

MAX_BINARY = 16 * 1024 * 1024
TOKEN = re.compile(r"[A-Za-z0-9_.:-]{1,80}")
HEX_ADDRESS = re.compile(r"0x[0-9a-fA-F]{1,8}")
DIGEST = re.compile(r"[a-f0-9]{64}")
PROFILE_FIELDS = {
    "schemaVersion",
    "model",
    "architecture",
    "targetIdentity",
    "openocdConfig",
    "flashAddress",
    "maxRegionBytes",
    "eraseBlockBytes",
    "timeoutSeconds",
}
MANIFEST_FIELDS = {
    "schemaVersion",
    "format",
    "name",
    "version",
    "model",
    "architecture",
    "sha256",
    "sizeBytes",
}


def read_object(path, fields):
    with path.open("rb") as source:
        raw = source.read(16385)
    if len(raw) > 16384:
        raise ValueError(f"{path.name} exceeds 16 KiB.")
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or value.keys() != fields
        or type(value["schemaVersion"]) is not int
        or value["schemaVersion"] != 1
    ):
        raise ValueError(f"{path.name} does not match the version 1 schema.")
    return value


def load_profile(path):
    profile = read_object(path, PROFILE_FIELDS)
    for key in ("model", "architecture", "openocdConfig"):
        if not isinstance(profile[key], str) or not profile[key].strip():
            raise ValueError(f"{key} is required in the programmer profile.")
    identity, address = profile["targetIdentity"], profile["flashAddress"]
    if not isinstance(identity, str) or not TOKEN.fullmatch(identity):
        raise ValueError("targetIdentity must be a plain hardware identifier.")
    if not isinstance(address, str) or not HEX_ADDRESS.fullmatch(address):
        raise ValueError("flashAddress must be a 32-bit hexadecimal address.")
    region, erase, timeout = (
        profile[key] for key in ("maxRegionBytes", "eraseBlockBytes", "timeoutSeconds")
    )
    if any(type(value) is not int for value in (region, erase, timeout)) or not (
        1 <= erase <= region <= MAX_BINARY and 1 <= timeout <= 600
    ):
        raise ValueError("Check the configured region, erase block, and timeout.")
    start = int(address, 16)
    if start % erase or region % erase or start + region > 2**32:
        raise ValueError(
            "The approved flash region must use whole aligned erase blocks."
        )
    cfg = (path.parent / profile["openocdConfig"]).resolve(strict=True)
    if not cfg.is_file() or cfg.suffix.lower() != ".cfg":
        raise ValueError("The profile must identify a trusted local OpenOCD .cfg file.")
    return profile, cfg


def stage_binary(manifest_path, binary_path, profile, destination):
    manifest = read_object(manifest_path, MANIFEST_FIELDS)
    if any(manifest[key] != profile[key] for key in ("model", "architecture")):
        raise ValueError(
            "Firmware board model and architecture do not match the profile."
        )
    size, expected = manifest["sizeBytes"], manifest["sha256"]
    if (
        manifest["format"] != "bin"
        or binary_path.suffix.lower() != ".bin"
        or type(size) is not int
        or not 1 <= size <= profile["maxRegionBytes"]
        or not isinstance(expected, str)
        or not DIGEST.fullmatch(expected)
    ):
        raise ValueError(
            "Use a raw .bin manifest and an image within the approved region."
        )
    digest = hashlib.sha256()
    with binary_path.open("rb") as source, destination.open("xb") as output:
        remaining = size
        while remaining:
            chunk = source.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            digest.update(chunk)
            output.write(chunk)
        if remaining or source.read(1) or digest.hexdigest() != expected:
            raise ValueError("Firmware size or SHA-256 disagrees with the manifest.")
    return manifest


def program(executable, cfg, profile, scratch, filename, label):
    address = profile["flashAddress"]
    identity = profile["targetIdentity"]
    script = "\n".join(
        [
            "if {[catch {init}]} { shutdown error }",
            f"if {{[catch {{hardware_tester_probe}} actual] || $actual ne {{{identity}}}}} {{ shutdown error }}",
            "echo HT_TARGET_MATCH",
            "if {[catch {reset init}]} { shutdown error }",
            "echo HT_WRITE_STARTED",
            f"if {{[catch {{flash write_image erase {filename} {address} bin}}]}} {{ shutdown error }}",
            "echo HT_WRITE_COMPLETED",
            f"if {{[catch {{verify_image {filename} {address} bin}}]}} {{",
            "    echo HT_VERIFY_FAILED; shutdown error",
            "}",
            "echo HT_VERIFIED",
            "if {[catch {reset run}]} { shutdown error }",
            "echo HT_RESET_COMPLETED",
            "shutdown",
        ]
    )
    log = scratch / f"{label}.log"
    timed_out = False
    with log.open("wb") as output:
        try:
            result = subprocess.run(
                [
                    executable,
                    "-c",
                    "gdb_port disabled; telnet_port disabled; tcl_port disabled",
                    "-f",
                    str(cfg),
                    "-c",
                    script,
                ],
                cwd=scratch,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=profile["timeoutSeconds"],
                check=False,
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = None
    with log.open("rb") as output:
        output.seek(max(0, log.stat().st_size - 65536))
        evidence = output.read().decode("utf-8", errors="replace")
    markers = {line.strip() for line in evidence.splitlines() if line.startswith("HT_")}
    complete = {
        "HT_TARGET_MATCH",
        "HT_WRITE_STARTED",
        "HT_WRITE_COMPLETED",
        "HT_VERIFIED",
        "HT_RESET_COMPLETED",
    }
    return {
        "exitCode": exit_code,
        "timedOut": timed_out,
        "identityMatched": "HT_TARGET_MATCH" in markers,
        "writeObserved": "HT_WRITE_STARTED" in markers,
        "verified": "HT_VERIFIED" in markers,
        "verifyFailed": {"HT_WRITE_COMPLETED", "HT_VERIFY_FAILED"} <= markers,
        "passed": exit_code == 0 and complete <= markers,
        "openocdLogTail": evidence[-8192:],
    }


@contextmanager
def reserve_programmer(cfg):
    lock = cfg.with_suffix(cfg.suffix + ".hardware-tester.lock")
    try:
        reservation = lock.open("x", encoding="ascii")
    except FileExistsError as exc:
        raise ValueError(
            "This configuration already has an active or interrupted rack job."
        ) from exc
    try:
        with reservation:
            reservation.write(f"process {os.getpid()}\n")
            reservation.flush()
            os.fsync(reservation.fileno())
        yield
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("profile", "manifest", "binary", "report"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--openocd", default="openocd")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--recovery-manifest", type=Path)
    parser.add_argument("--recovery-binary", type=Path)
    args = parser.parse_args()
    if bool(args.recovery_manifest) != bool(args.recovery_binary):
        parser.error("Provide both recovery files together.")
    report = {
        "schemaVersion": 1,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "requestedApply": args.apply,
        "status": "started",
    }
    try:
        output = args.report.open("x", encoding="utf-8")
    except OSError as exc:
        parser.exit(2, f"Could not create a new report: {exc}\n")
    with output:
        # The opening event remains available if the tool or rack loses power.
        output.write(json.dumps(report) + "\n")
        output.flush()
        os.fsync(output.fileno())
        try:
            profile, cfg = load_profile(args.profile)
            report["expectedIdentity"] = profile["targetIdentity"]
            with tempfile.TemporaryDirectory(prefix="ht-openocd-") as temporary:
                scratch = Path(temporary)
                report["firmware"] = stage_binary(
                    args.manifest, args.binary, profile, scratch / "firmware.bin"
                )
                if args.recovery_binary:
                    report["recoveryFirmware"] = stage_binary(
                        args.recovery_manifest,
                        args.recovery_binary,
                        profile,
                        scratch / "recovery.bin",
                    )
                report["status"] = "preflightPassed"
                if args.apply:
                    with reserve_programmer(cfg):
                        report["status"] = "programming"
                        output.write(json.dumps(report) + "\n")
                        output.flush()
                        os.fsync(output.fileno())
                        attempt = program(
                            args.openocd, cfg, profile, scratch, "firmware.bin", "flash"
                        )
                        report["attempt"] = attempt
                        report["status"] = (
                            "verified" if attempt["passed"] else "operatorReview"
                        )
                        if (
                            args.recovery_binary
                            and attempt["identityMatched"]
                            and attempt["verifyFailed"]
                        ):
                            recovery = program(
                                args.openocd,
                                cfg,
                                profile,
                                scratch,
                                "recovery.bin",
                                "recovery",
                            )
                            report["recovery"] = recovery
                            if recovery["passed"]:
                                report["status"] = "recovered"
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            if report["status"] != "operatorReview":
                report["status"] = (
                    "operatorReview" if report["status"] == "programming" else "error"
                )
            report["error"] = str(exc)
        except KeyboardInterrupt:
            report["status"] = "interrupted"
        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        output.write(json.dumps(report) + "\n")
    print(json.dumps(report))
    return 0 if report["status"] in {"preflightPassed", "verified"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
