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

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

MAX_BINARY = 16 * 1024 * 1024
TOKEN = re.compile(r"[A-Za-z0-9_.:-]{1,80}")
HEX_ADDRESS = re.compile(r"0x[0-9a-fA-F]{1,8}")
DIGEST = re.compile(r"[a-f0-9]{64}")
SIGNATURE = re.compile(r"[a-f0-9]{128}")
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
PROGRAM_PROGRESS = [
    "HT_TARGET_MATCH",
    "HT_WRITE_STARTED",
    "HT_WRITE_COMPLETED",
    "HT_VERIFIED",
    "HT_RESET_COMPLETED",
]
PROGRAM_FAILURES = {
    "HT_INIT_FAILED": (0, "initializationFailed"),
    "HT_PROBE_FAILED": (0, "probeFailed"),
    "HT_TARGET_MISMATCH": (0, "targetMismatch"),
    "HT_PREPARE_FAILED": (1, "prepareFailed"),
    "HT_WRITE_FAILED": (2, "writeFailed"),
    "HT_VERIFY_FAILED": (3, "verificationFailed"),
    "HT_RESET_FAILED": (4, "resetFailed"),
}
BEFORE_WRITE = {
    "initializationFailed",
    "probeFailed",
    "targetMismatch",
    "prepareFailed",
}


def unique_fields(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate JSON field: {key}.")
        value[key] = item
    return value


def read_object(path, fields):
    with path.open("rb") as source:
        raw = source.read(16385)
    if len(raw) > 16384:
        raise ValueError(f"{path.name} exceeds 16 KiB.")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_fields)
    if (
        not isinstance(value, dict)
        or value.keys() != fields
        or type(value["schemaVersion"]) is not int
        or value["schemaVersion"] != 1
    ):
        raise ValueError(f"{path.name} does not match the version 1 schema.")
    return value, raw


def load_trust_store(path):
    store, _ = read_object(path, {"schemaVersion", "keys"})
    keys = store["keys"]
    if (
        not isinstance(keys, dict)
        or not keys
        or any(
            not TOKEN.fullmatch(key_id)
            or not isinstance(public_key, str)
            or not DIGEST.fullmatch(public_key)
            for key_id, public_key in keys.items()
        )
    ):
        raise ValueError(
            "Trust store needs key IDs and raw Ed25519 public keys in lowercase hex."
        )
    if len(set(keys.values())) != len(keys):
        raise ValueError("Each trusted public key must have a single key ID.")
    return {key_id: bytes.fromhex(key) for key_id, key in keys.items()}


def verify_manifest(manifest_path, signature_path, trusted_keys):
    manifest, raw = read_object(manifest_path, MANIFEST_FIELDS)
    signature, _ = read_object(signature_path, {"schemaVersion", "keyId", "signature"})
    key_id, encoded = signature["keyId"], signature["signature"]
    if not isinstance(key_id, str) or key_id not in trusted_keys:
        raise ValueError("Firmware manifest signer is outside the local trust store.")
    if not isinstance(encoded, str) or not SIGNATURE.fullmatch(encoded):
        raise ValueError("Use a 64-byte Ed25519 signature in lowercase hex.")
    trusted_key = trusted_keys[key_id]
    try:
        Ed25519PublicKey.from_public_bytes(trusted_key).verify(
            bytes.fromhex(encoded), raw
        )
    except InvalidSignature as exc:
        raise ValueError("Firmware manifest signature verification failed.") from exc
    if any(
        not isinstance(manifest[key], str)
        or not manifest[key].strip()
        or len(manifest[key]) > 160
        for key in ("name", "version", "model", "architecture")
    ):
        raise ValueError(
            "The signed manifest requires a name, version, model, and architecture."
        )
    return manifest, {
        "algorithm": "Ed25519",
        "keyId": key_id,
        "publicKeySha256": hashlib.sha256(trusted_key).hexdigest(),
        "manifestSha256": hashlib.sha256(raw).hexdigest(),
    }


def load_profile(path):
    profile, _ = read_object(path, PROFILE_FIELDS)
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


def stage_binary(manifest, binary_path, profile, destination):
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


def program(executable, cfg, profile, scratch, filename, label):
    address = profile["flashAddress"]
    identity = profile["targetIdentity"]
    script = "\n".join(
        [
            "if {[catch {init}]} { echo HT_INIT_FAILED; shutdown error }",
            "if {[catch {hardware_tester_probe} actual]} { echo HT_PROBE_FAILED; shutdown error }",
            f"if {{$actual ne {{{identity}}}}} {{ echo HT_TARGET_MISMATCH; shutdown error }}",
            "echo HT_TARGET_MATCH",
            "if {[catch {reset init}]} { echo HT_PREPARE_FAILED; shutdown error }",
            "echo HT_WRITE_STARTED",
            f"if {{[catch {{flash write_image erase {filename} {address} bin}}]}} {{",
            "    echo HT_WRITE_FAILED; shutdown error",
            "}",
            "echo HT_WRITE_COMPLETED",
            f"if {{[catch {{verify_image {filename} {address} bin}}]}} {{",
            "    echo HT_VERIFY_FAILED; shutdown error",
            "}",
            "echo HT_VERIFIED",
            "if {[catch {reset run}]} { echo HT_RESET_FAILED; shutdown error }",
            "echo HT_RESET_COMPLETED",
            "shutdown",
        ]
    )
    log = scratch / f"{label}.log"
    timed_out = False
    interrupted = False
    exit_code = None
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
        except KeyboardInterrupt:
            interrupted = True
    with log.open("rb") as output:
        output.seek(max(0, log.stat().st_size - 65536))
        evidence = output.read().decode("utf-8", errors="replace")
    markers = [line.strip() for line in evidence.splitlines() if line.startswith("HT_")]
    progress = 0
    outcome = "programmerError"
    if markers == PROGRAM_PROGRESS[: len(markers)]:
        progress = len(markers)
        if progress == len(PROGRAM_PROGRESS) and exit_code == 0:
            outcome = "verified"
    elif markers and markers[-1] in PROGRAM_FAILURES:
        expected_progress, failure = PROGRAM_FAILURES[markers[-1]]
        if markers[:-1] == PROGRAM_PROGRESS[:expected_progress]:
            progress = expected_progress
            if exit_code == 1:
                outcome = failure
    if timed_out or interrupted:
        outcome = "interrupted"
    return {
        "outcome": outcome,
        "exitCode": exit_code,
        "timedOut": timed_out,
        "interrupted": interrupted,
        "identityMatched": progress >= 1,
        "writeObserved": progress >= 2,
        "verified": progress >= 4,
        "verifyFailed": outcome == "verificationFailed",
        "passed": outcome == "verified",
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


def append_event(output, report):
    output.write(json.dumps(report) + "\n")
    output.flush()
    os.fsync(output.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("profile", "manifest", "signature", "binary", "trust-store", "report"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--openocd", default="openocd")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--recovery-manifest", type=Path)
    parser.add_argument("--recovery-signature", type=Path)
    parser.add_argument("--recovery-binary", type=Path)
    args = parser.parse_args()
    recovery_files = (
        args.recovery_manifest,
        args.recovery_signature,
        args.recovery_binary,
    )
    if any(recovery_files) and not all(recovery_files):
        parser.error("Provide the recovery manifest, signature, and binary together.")
    report = {
        "schemaVersion": 1,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "requestedApply": args.apply,
        "status": "started",
        "targetState": "writeNotAttempted",
    }
    try:
        output = args.report.open("x", encoding="utf-8")
    except OSError as exc:
        parser.exit(2, f"Could not create a new report: {exc}\n")
    with output:
        append_event(output, report)
        try:
            profile, cfg = load_profile(args.profile)
            report["expectedIdentity"] = profile["targetIdentity"]
            trusted_keys = load_trust_store(args.trust_store)
            report["firmware"], report["firmwareSignature"] = verify_manifest(
                args.manifest, args.signature, trusted_keys
            )
            with tempfile.TemporaryDirectory(prefix="ht-openocd-") as temporary:
                scratch = Path(temporary)
                stage_binary(
                    report["firmware"], args.binary, profile, scratch / "firmware.bin"
                )
                if args.recovery_binary:
                    recovery_firmware, recovery_signature = verify_manifest(
                        args.recovery_manifest, args.recovery_signature, trusted_keys
                    )
                    report["recoveryFirmware"] = recovery_firmware
                    report["recoveryFirmwareSignature"] = recovery_signature
                    if recovery_firmware["sha256"] == report["firmware"]["sha256"]:
                        raise ValueError("Choose a distinct known-good recovery image.")
                    stage_binary(
                        recovery_firmware,
                        args.recovery_binary,
                        profile,
                        scratch / "recovery.bin",
                    )
                    block = profile["eraseBlockBytes"]
                    if (recovery_firmware["sizeBytes"] - 1) // block < (
                        report["firmware"]["sizeBytes"] - 1
                    ) // block:
                        raise ValueError(
                            "The recovery image must cover the candidate's erase blocks."
                        )
                report["status"] = "preflightPassed"
                if args.apply:
                    with reserve_programmer(cfg):
                        report.update(status="programming", targetState="unknown")
                        append_event(output, report)
                        attempt = program(
                            args.openocd, cfg, profile, scratch, "firmware.bin", "flash"
                        )
                        report["attempt"] = attempt
                        outcome = attempt["outcome"]
                        report["status"] = {
                            "verified": "verified",
                            "targetMismatch": "targetRejected",
                            "verificationFailed": "verificationFailed",
                            "interrupted": "interrupted",
                        }.get(outcome, "operatorReview")
                        if attempt["verified"]:
                            report["targetState"] = "candidateVerified"
                        elif outcome in BEFORE_WRITE:
                            report["targetState"] = "writeNotAttempted"
                        if args.recovery_binary and attempt["verifyFailed"]:
                            report.update(status="recovering", targetState="unknown")
                            append_event(output, report)
                            recovery = program(
                                args.openocd,
                                cfg,
                                profile,
                                scratch,
                                "recovery.bin",
                                "recovery",
                            )
                            report["recovery"] = recovery
                            report["status"] = {
                                "verified": "recovered",
                                "interrupted": "interrupted",
                            }.get(recovery["outcome"], "recoveryFailed")
                            if recovery["verified"]:
                                report["targetState"] = "recoveryVerified"
        except (OSError, ValueError, RecursionError, subprocess.SubprocessError) as exc:
            report["status"] = {
                "programming": "operatorReview",
                "recovering": "recoveryFailed",
            }.get(report["status"], "preflightRejected")
            report["error"] = str(exc)
        except KeyboardInterrupt:
            report["status"] = "interrupted"
        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        append_event(output, report)
    print(json.dumps(report))
    return 0 if report["status"] in {"preflightPassed", "verified"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
