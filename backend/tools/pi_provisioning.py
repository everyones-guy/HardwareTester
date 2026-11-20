#!/usr/bin/env python3
"""Build and check an offline provisioning plan for a 64-bit Raspberry Pi 3B."""

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

PROFILE = "pi3b-aarch64"
MACHINE = "raspi3b"
PI3B_MODEL = re.compile(r"Raspberry Pi 3 Model B(?: Rev [0-9]+(?:\.[0-9]+)*)?")
ROOT_DEVICE = re.compile(r"(?:/dev/mmcblk0p[1-9][0-9]*|PARTUUID=[a-fA-F0-9-]+)")
SHA256 = re.compile(r"[a-f0-9]{64}")
KERNEL = "kernel8.img"
DTB = "bcm2710-rpi-3-b.dtb"
DISK = "sd.img"
INITRD = "initrd.img"
BOOTSTRAP_FILES = {
    "deployment/raspberry-pi/bootstrap.sh",
    "backend/tools/capture_pi_inventory.py",
    "backend/tools/pi_provisioning.py",
}
MANIFEST_FIELDS = {
    "schemaVersion",
    "profile",
    "release",
    "os",
    "artifacts",
    "bootstrap",
    "boot",
}
TARGET_FIELDS = {"model", "architecture", "capturedAt"}


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}.")
        result[key] = value
    return result


def read_document(path):
    with path.open("rb") as source:
        data = source.read(32769)
    if len(data) > 32768:
        raise ValueError(f"{path.name} exceeds 32 KiB.")
    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique_fields)


def valid_text(value, limit=160):
    return (
        isinstance(value, str)
        and 1 <= len(value) <= limit
        and value.isprintable()
        and bool(value.strip())
    )


def check_target(inventory):
    if not isinstance(inventory, dict) or not isinstance(inventory.get("model"), str):
        raise ValueError("Select a Raspberry Pi inventory.")
    if (
        not PI3B_MODEL.fullmatch(inventory["model"])
        or inventory.get("architecture") != "aarch64"
    ):
        raise ValueError(
            "This profile requires a Raspberry Pi 3 Model B with an aarch64 kernel."
        )


def validate_boot(boot):
    if not isinstance(boot, dict) or boot.keys() != {
        "rootDevice",
        "readyMarker",
        "timeoutSeconds",
    }:
        raise ValueError("Specify the boot root device, readiness marker, and timeout.")
    root, marker, timeout = (
        boot["rootDevice"],
        boot["readyMarker"],
        boot["timeoutSeconds"],
    )
    if not isinstance(root, str) or len(root) > 100 or not ROOT_DEVICE.fullmatch(root):
        raise ValueError("Use a Pi SD partition or PARTUUID as the root device.")
    if (
        not isinstance(marker, str)
        or not marker.strip()
        or not re.fullmatch(r"[ -~]{1,128}", marker)
    ):
        raise ValueError("Use a readiness marker of 1–128 printable ASCII characters.")
    if type(timeout) is not int or not 1 <= timeout <= 600:
        raise ValueError("Boot timeout must be 1–600 seconds.")


def validate_pins(pins, required, optional=()):
    if not isinstance(pins, dict) or not required <= pins.keys() <= required.union(
        optional
    ):
        raise ValueError("The pinned filenames do not match this provisioning profile.")
    for name, pin in pins.items():
        if (
            not isinstance(pin, dict)
            or pin.keys() != {"sha256", "sizeBytes"}
            or not isinstance(pin["sha256"], str)
            or not SHA256.fullmatch(pin["sha256"])
            or type(pin["sizeBytes"]) is not int
            or not 1 <= pin["sizeBytes"] <= 2**53 - 1
        ):
            raise ValueError(
                f"Specify the SHA-256 and a positive byte count for {name}."
            )


def validate_manifest(manifest):
    if (
        not isinstance(manifest, dict)
        or manifest.keys() != MANIFEST_FIELDS
        or type(manifest["schemaVersion"]) is not int
        or manifest["schemaVersion"] != 1
        or manifest["profile"] != PROFILE
        or not valid_text(manifest["release"])
    ):
        raise ValueError(
            "Use a version 1 release manifest for the pi3b-aarch64 profile."
        )
    os_release = manifest["os"]
    if (
        not isinstance(os_release, dict)
        or os_release.keys() != {"id", "version"}
        or not all(valid_text(value, 80) for value in os_release.values())
    ):
        raise ValueError("Specify the OS ID and version expected after imaging.")
    validate_boot(manifest["boot"])
    validate_pins(manifest["artifacts"], {KERNEL, DTB, DISK}, {INITRD})
    validate_pins(manifest["bootstrap"], BOOTSTRAP_FILES)
    check_disk_size(manifest["artifacts"][DISK]["sizeBytes"])


def make_plan(inventory, manifest):
    check_target(inventory)
    validate_manifest(manifest)
    captured = inventory.get("capturedAt")
    if not valid_text(captured, 40):
        raise ValueError("The selected inventory must contain a capture time.")
    return {
        **manifest,
        "target": {key: inventory[key] for key in sorted(TARGET_FIELDS)},
    }


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.keys() != MANIFEST_FIELDS | {"target"}:
        raise ValueError("Use an exported Raspberry Pi provisioning plan.")
    target = plan["target"]
    if not isinstance(target, dict) or target.keys() != TARGET_FIELDS:
        raise ValueError("The plan must identify its source inventory.")
    make_plan(target, {key: plan[key] for key in MANIFEST_FIELDS})
    return plan


def fingerprint(path):
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or not info.st_size:
        raise ValueError(f"{path.name} must be a nonempty regular file.")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def verify_bundle(bundle, fingerprints):
    for name, prior in fingerprints.items():
        if fingerprint(bundle / name) != prior:
            raise ValueError(f"{name} changed while the runner was using it.")


def check_disk_size(size):
    if size < 512 or size & (size - 1):
        raise ValueError("sd.img must have a power-of-two size of at least 512 bytes.")


def hash_bundle(bundle):
    names = [KERNEL, DTB, DISK]
    initrd = bundle / INITRD
    if initrd.exists() or initrd.is_symlink():
        names.append(INITRD)
    fingerprints = {name: fingerprint(bundle / name) for name in names}
    check_disk_size(fingerprints[DISK][2])
    artifacts = {}
    for name in names:
        with (bundle / name).open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        artifacts[name] = {"sha256": digest, "sizeBytes": fingerprints[name][2]}
    verify_bundle(bundle, fingerprints)
    return artifacts, fingerprints


def hash_bootstrap(root):
    pins = {}
    for name in sorted(BOOTSTRAP_FILES):
        path = root / name
        with path.open("rb") as source:
            data = source.read(1048577).replace(b"\r\n", b"\n")
        if not data or len(data) > 1048576 or path.stat().st_size > 1048576:
            raise ValueError(f"{name} must be a nonempty file up to 1 MiB.")
        pins[name] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "sizeBytes": len(data),
        }
    return pins


def check_pins(recorded, expected):
    if recorded.keys() != expected.keys():
        raise ValueError("Local files do not match the pinned file list.")
    for name, pin in expected.items():
        if recorded[name] != pin:
            raise ValueError(
                f"{name} SHA-256 or byte count does not match the provisioning plan."
            )


def check_bootstrap(plan, source_root, root, architecture):
    if __package__:
        from .capture_pi_inventory import read_model, read_os_release
    else:
        from capture_pi_inventory import read_model, read_os_release

    check_pins(hash_bootstrap(source_root), plan["bootstrap"])
    model = read_model(root)
    check_target({"model": model, "architecture": architecture})
    if model != plan["target"]["model"]:
        raise ValueError(
            "The running board model and revision differ from the selected capture."
        )
    os_id, version = read_os_release(root)
    if plan["os"] != {"id": os_id, "version": version}:
        raise ValueError("The running OS differs from the OS in the provisioning plan.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    manifest = commands.add_parser(
        "manifest", help="Record the local inputs for release review."
    )
    manifest.add_argument("--bundle", type=Path, required=True)
    manifest.add_argument(
        "--source-root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    for name in ("release", "os-id", "os-version", "ready-marker"):
        manifest.add_argument(f"--{name}", required=True)
    manifest.add_argument("--root-device", default="/dev/mmcblk0p2")
    manifest.add_argument("--boot-timeout", type=int, default=120)
    plan = commands.add_parser(
        "plan", help="Match release inputs to a saved inventory."
    )
    plan.add_argument("--inventory", type=Path, required=True)
    plan.add_argument("--manifest", type=Path, required=True)
    bootstrap = commands.add_parser(
        "check-bootstrap", help="Check a plan on the booted Pi."
    )
    bootstrap.add_argument("--plan", type=Path, required=True)
    bootstrap.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "manifest":
            artifacts, _ = hash_bundle(args.bundle)
            result = {
                "schemaVersion": 1,
                "profile": PROFILE,
                "release": args.release,
                "os": {"id": args.os_id, "version": args.os_version},
                "artifacts": artifacts,
                "bootstrap": hash_bootstrap(args.source_root),
                "boot": {
                    "rootDevice": args.root_device,
                    "readyMarker": args.ready_marker,
                    "timeoutSeconds": args.boot_timeout,
                },
            }
            validate_manifest(result)
        elif args.command == "plan":
            result = make_plan(
                read_document(args.inventory), read_document(args.manifest)
            )
        else:
            if sys.platform != "linux":
                raise ValueError("Check bootstrap on the running Raspberry Pi.")
            result = validate_plan(read_document(args.plan))
            architecture = os.uname().machine.lower()
            check_bootstrap(
                result,
                args.source_root,
                Path("/"),
                {"arm64": "aarch64"}.get(architecture, architecture),
            )
            result = {"status": "bootstrapPreflightPassed", "profile": PROFILE}
    except (OSError, ValueError, RecursionError) as error:
        parser.exit(2, f"Provisioning check failed: {error}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
