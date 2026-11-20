"""Verify a Workbench runtime lock and optionally smoke-test approved release bytes."""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import threading
import uuid
from pathlib import Path

from Hardware_Tester_App.firmware_artifacts import FIRMWARE_UPLOAD_LIMIT
from Hardware_Tester_App.firmware_inventory import firmware_members, summarize_inventory
from Hardware_Tester_App.firmware_runtime import canonical_json, make_runtime_profile

PROFILE_LIMIT = 512 * 1024
OUTPUT_LIMIT = 16 * 1024
RUNTIME_TIMEOUT = 20


def read_file(path, limit):
    if not path.is_file():
        raise ValueError(f"Use a regular file for {path.name}.")
    with path.open("rb") as source:
        raw = source.read(limit + 1)
    if not raw or len(raw) > limit:
        raise ValueError(f"{path.name} is empty or exceeds {limit} bytes.")
    return raw


def run_container(profile, payload):
    name = f"uht-firmware-{uuid.uuid4().hex}"
    if "," in str(payload):
        raise ValueError(
            "Use a temporary directory path without commas for the Docker mount."
        )
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--pull=never",
        "--platform",
        profile["platform"],
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=65532:65532",
        "--memory=128m",
        "--cpus=1",
        "--pids-limit=32",
        "--log-driver=none",
        "--mount",
        f"type=bind,source={payload},target=/release,readonly",
        "--entrypoint",
        profile["interpreter"],
        profile["baseImage"],
        "--library-path",
        "/release/lib",
        "/release/app",
        *profile["arguments"],
    ]
    output = bytearray()
    truncated = False
    timed_out = False
    interrupted = False
    cleanup_error = None
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
    ) as process:

        def collect():
            nonlocal truncated
            while chunk := process.stdout.read(8192):
                take = max(0, OUTPUT_LIMIT - len(output))
                output.extend(chunk[:take])
                truncated |= len(chunk) > take

        reader = threading.Thread(target=collect, daemon=True)
        reader.start()
        try:
            process.wait(timeout=RUNTIME_TIMEOUT)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            timed_out = isinstance(error, subprocess.TimeoutExpired)
            interrupted = not timed_out
            process.kill()
            process.wait()
        finally:
            reader.join()
            if timed_out or interrupted:
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", name],
                        timeout=10,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as error:
                    cleanup_error = str(error)
    return {
        "command": command,
        "exitCode": 124 if timed_out else 130 if interrupted else process.returncode,
        "timedOut": timed_out,
        "output": output.decode("utf-8", errors="replace"),
        "outputTruncated": truncated,
        "interrupted": interrupted,
        "cleanupError": cleanup_error,
    }


def verify_and_run(profile_path, bundle, *, run, approved_sha256):
    supplied = json.loads(read_file(profile_path, PROFILE_LIMIT))
    if not isinstance(supplied, dict) or not isinstance(
        supplied.get("entrypoint"), dict
    ):
        raise ValueError("Use a runtime profile exported from the Firmware library.")
    arguments = supplied.get("arguments")
    if (
        not isinstance(arguments, list)
        or len(arguments) > 1
        or any(not isinstance(arg, str) for arg in arguments)
    ):
        raise ValueError(
            "The profile requires an argument list with at most one smoke flag."
        )

    raw = read_file(bundle, FIRMWARE_UPLOAD_LIMIT)
    release_sha256 = hashlib.sha256(raw).hexdigest()
    if release_sha256 != supplied.get("releaseSha256"):
        raise ValueError("The release ZIP does not match the profile SHA-256.")

    # Use the same byte snapshot for inspection and staging. A changed source path cannot swap in other bytes.
    with tempfile.TemporaryDirectory(prefix="uht-runtime-") as directory:
        root = Path(directory).resolve()
        snapshot = root / "release.zip"
        snapshot.write_bytes(raw)
        with firmware_members(snapshot, "zip", scratch=root) as paths:
            inventory, _, _ = summarize_inventory(release_sha256, "zip", paths)
            profile = make_runtime_profile(
                inventory,
                supplied["entrypoint"].get("path"),
                arguments[0] if arguments else None,
            )
            if canonical_json(profile) != canonical_json(supplied):
                raise ValueError(
                    "The exported profile differs from the lock regenerated from the release bytes."
                )
            report = {
                "status": profile["status"],
                "releaseSha256": release_sha256,
                "profileSha256": profile["profileSha256"],
                "dockerInvoked": False,
                "profile": profile,
            }
            if profile["status"] == "blocked":
                return 2, report
            if not run:
                return 0, report
            if approved_sha256 != release_sha256:
                raise ValueError(
                    "Running requires --approved-sha256 from your reviewed release."
                )

            payload = root / "payload"
            library_dir = payload / "lib"
            library_dir.mkdir(parents=True)
            shutil.copyfile(paths[profile["entrypoint"]["path"]], payload / "app")
            for library in profile["bundledLibraries"]:
                shutil.copyfile(paths[library["path"]], library_dir / library["loadAs"])
            payload.chmod(0o755)
            library_dir.chmod(0o755)
            for member in (payload / "app", *library_dir.iterdir()):
                member.chmod(0o555)
            # Docker receives only the staged ELF and its selected libraries as a read-only mount.
            runtime = run_container(profile, payload)
    report.update(
        status="passed" if runtime["exitCode"] == 0 else "runtimeFailed",
        dockerInvoked=True,
        runtime=runtime,
    )
    return (0 if runtime["exitCode"] == 0 else 1), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--approved-sha256",
        help="Digest supplied by the operator after reviewing the release",
    )
    args = parser.parse_args()
    with args.report.open("x", encoding="utf-8") as output:
        try:
            status, report = verify_and_run(
                args.profile,
                args.bundle,
                run=args.run,
                approved_sha256=args.approved_sha256,
            )
        except (ValueError, OSError, RecursionError) as error:
            status, report = 2, {"status": "rejected", "message": str(error)}
        json.dump(report, output, indent=2)
        output.write("\n")
    print(f"{report['status']}: {args.report}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
