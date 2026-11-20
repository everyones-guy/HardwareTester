import hashlib
import json
import shutil
import subprocess
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools import flash_openocd as flash

REAL_RUN = subprocess.run
MODEL = "Synthetic board rev A"
TARGET = "synthetic-rack-rev-a"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


@pytest.fixture
def flash_job(tmp_path, monkeypatch):
    return FlashJob(tmp_path, monkeypatch)


class FlashJob:
    def __init__(self, root, monkeypatch):
        self.root = root
        self.monkeypatch = monkeypatch
        self.key = Ed25519PrivateKey.generate()
        self.trust = root / "trusted-publishers.json"
        self.profile = root / "board.json"
        self.report = root / "events.jsonl"
        write_json(
            self.trust,
            {
                "schemaVersion": 1,
                "keys": {
                    "fixture-publisher": self.key.public_key().public_bytes_raw().hex()
                },
            },
        )
        (root / "board.cfg").write_text(
            "# inert configuration for the mock programmer\n"
        )
        write_json(
            self.profile,
            {
                "schemaVersion": 1,
                "model": MODEL,
                "architecture": "arm",
                "targetIdentity": TARGET,
                "openocdConfig": "board.cfg",
                "flashAddress": "0x08000000",
                "maxRegionBytes": 1024,
                "eraseBlockBytes": 256,
                "timeoutSeconds": 1,
            },
        )
        self.candidate = self.release("candidate")

    def release(self, name, *, data=None, **changes):
        binary = self.root / f"{name}.bin"
        manifest = self.root / f"{name}.json"
        signature = self.root / f"{name}.signature.json"
        if data is None:
            data = f"synthetic {name} bytes".encode()
        binary.write_bytes(data)
        write_json(
            manifest,
            {
                "schemaVersion": 1,
                "format": "bin",
                "name": "Flash test fixture",
                "version": name,
                "model": MODEL,
                "architecture": "arm",
                "sizeBytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            | changes,
        )
        self.sign(manifest, signature)
        return binary, manifest, signature

    def sign(self, manifest, signature, *, key=None, key_id="fixture-publisher"):
        key = key or self.key
        write_json(
            signature,
            {
                "schemaVersion": 1,
                "keyId": key_id,
                "signature": key.sign(manifest.read_bytes()).hex(),
            },
        )

    def run(self, programmer=None, *, apply=False, recovery=None):
        binary, manifest, signature = self.candidate
        argv = [
            "flash_openocd",
            "--profile",
            str(self.profile),
            "--manifest",
            str(manifest),
            "--signature",
            str(signature),
            "--binary",
            str(binary),
            "--trust-store",
            str(self.trust),
            "--report",
            str(self.report),
            "--openocd",
            "SYNTHETIC_PROGRAMMER",
        ]
        if apply:
            argv.append("--apply")
        if recovery:
            binary, manifest, signature = recovery
            argv.extend(
                [
                    "--recovery-binary",
                    str(binary),
                    "--recovery-manifest",
                    str(manifest),
                    "--recovery-signature",
                    str(signature),
                ],
            )

        def unexpected(*args, **kwargs):
            raise AssertionError("Programmer was called without trusted preflight.")

        self.monkeypatch.setattr("sys.argv", argv)
        self.monkeypatch.setattr(flash.subprocess, "run", programmer or unexpected)
        code = flash.main()
        return code, [
            json.loads(line)
            for line in self.report.read_text(encoding="utf-8").splitlines()
        ]


def test_signed_dry_run_records_the_trusted_publisher_without_invoking_openocd(
    flash_job,
):
    code, events = flash_job.run()
    final = events[-1]
    assert code == 0 and final["status"] == "preflightPassed"
    assert final["targetState"] == "writeNotAttempted"
    assert "attempt" not in final
    _, manifest, _ = flash_job.candidate
    public_key = flash_job.key.public_key().public_bytes_raw()
    assert final["firmwareSignature"] == {
        "algorithm": "Ed25519",
        "keyId": "fixture-publisher",
        "publicKeySha256": hashlib.sha256(public_key).hexdigest(),
        "manifestSha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("unsigned", "signature.json"),
        ("untrusted", "outside the local trust store"),
        ("forged", "verification failed"),
        ("edited-manifest", "verification failed"),
        ("edited-binary", "SHA-256"),
        ("wrong-board", "do not match"),
        ("ambiguous-manifest", "Duplicate JSON field"),
        ("untrusted-recovery", "outside the local trust store"),
        ("undersized-recovery", "cover the candidate's erase blocks"),
    ],
)
def test_preflight_rejects_unsafe_inputs_without_starting_programmer(
    flash_job, case, message
):
    binary, manifest, signature = flash_job.candidate
    recovery = None
    if case == "unsigned":
        signature.unlink()
    elif case == "untrusted":
        flash_job.sign(manifest, signature, key_id="unknown-publisher")
    elif case == "forged":
        flash_job.sign(manifest, signature, key=Ed25519PrivateKey.generate())
    elif case == "edited-manifest":
        write_json(manifest, json.loads(manifest.read_bytes()) | {"version": "edited"})
    elif case == "edited-binary":
        binary.write_bytes(b"x" + binary.read_bytes()[1:])
    elif case == "wrong-board":
        flash_job.candidate = flash_job.release("incompatible", model="Other board")
    elif case == "ambiguous-manifest":
        raw = manifest.read_bytes()
        manifest.write_bytes(b'{"format":"zip",' + raw[1:])
        flash_job.sign(manifest, signature)
    elif case == "untrusted-recovery":
        recovery = flash_job.release("fallback")
        flash_job.sign(recovery[1], recovery[2], key_id="unknown-publisher")
    elif case == "undersized-recovery":
        flash_job.candidate = flash_job.release("two-blocks", data=b"x" * 257)
        recovery = flash_job.release("fallback")

    code, events = flash_job.run(apply=True, recovery=recovery)
    assert [event["status"] for event in events] == ["started", "preflightRejected"]
    final = events[-1]
    assert code == 2 and final["targetState"] == "writeNotAttempted"
    assert message in final["error"]
    assert "attempt" not in final


def tcl_programmer(tclsh, calls, case):
    def run(argv, **options):
        assert argv[0] == "SYNTHETIC_PROGRAMMER"
        assert argv[2] == "gdb_port disabled; telnet_port disabled; tcl_port disabled"
        script = argv[-1]
        recovering = "verify_image recovery.bin" in script
        image = "recovery.bin" if recovering else "firmware.bin"
        calls.append(image)
        identity = "wrong-board" if case == "wrong-identity" else TARGET
        corrupt = case == "recovery-fails" or (
            case in ("verification-fails", "recover") and not recovering
        )
        stall = case == "timeout" and not recovering
        variables = f"set identity {identity}\nset corrupt {int(corrupt)}\nset stall {int(stall)}\n"
        test_driver = r"""
fconfigure stdout -buffering line
proc echo {line} {puts $line}
proc init {} {}
proc hardware_tester_probe {} {return $::identity}
proc reset {mode} {puts "MOCK_RESET $mode"}
proc bytes {path} {
    set f [open $path rb]
    set data [read $f]
    close $f
    return $data
}
proc flash {command erase path address format} {
    if {$command ne "write_image" || $erase ne "erase" || $address ne "0x08000000" || $format ne "bin"} {
        error "Unexpected programming arguments"
    }
    set contents [bytes $path]
    if {$::corrupt} { append contents ! }
    set target [open target-region.bin wb]
    puts -nonewline $target $contents
    close $target
    puts "MOCK_WRITE $path"
    if {$::stall} { after 60000 }
}
proc verify_image {path address format} {
    if {[bytes target-region.bin] ne [bytes $path]} { error "Readback differs" }
    puts "MOCK_READBACK $path"
}
proc shutdown {args} { if {[llength $args]} { exit 1 }; exit 0 }
"""
        tcl_file = options["cwd"] / "synthetic-programmer.tcl"
        tcl_file.write_text(variables + test_driver + script, encoding="utf-8")
        return REAL_RUN([tclsh, str(tcl_file)], **options)

    return run


@pytest.mark.parametrize(
    ("case", "status", "target_state", "code", "writes"),
    [
        ("verified", "verified", "candidateVerified", 0, ["firmware.bin"]),
        ("wrong-identity", "targetRejected", "writeNotAttempted", 2, []),
        ("timeout", "interrupted", "unknown", 2, ["firmware.bin"]),
        ("verification-fails", "verificationFailed", "unknown", 2, ["firmware.bin"]),
        (
            "recover",
            "recovered",
            "recoveryVerified",
            2,
            ["firmware.bin", "recovery.bin"],
        ),
        (
            "recovery-fails",
            "recoveryFailed",
            "unknown",
            2,
            ["firmware.bin", "recovery.bin"],
        ),
    ],
)
def test_tcl_programmer_double_checks_identity_readback_and_recovery(
    flash_job, case, status, target_state, code, writes
):
    tclsh = shutil.which("tclsh")
    if not tclsh:
        pytest.skip(
            "Install Tcl to run the OpenOCD script against the mock programmer."
        )
    calls = []
    fallback = None if case == "verification-fails" else flash_job.release("fallback")
    exit_code, events = flash_job.run(
        tcl_programmer(tclsh, calls, case), apply=True, recovery=fallback
    )
    assert exit_code == code
    assert (
        events[1]["status"] == "programming" and events[1]["targetState"] == "unknown"
    )
    final = events[-1]
    assert final["status"] == status and final["targetState"] == target_state
    attempt = final["attempt"]
    log = attempt["openocdLogTail"]
    if "recovery" in final:
        assert events[-2]["status"] == "recovering"
        assert final["recoveryFirmwareSignature"]["keyId"] == "fixture-publisher"
        log += final["recovery"]["openocdLogTail"]
    assert [
        line.split()[-1] for line in log.splitlines() if line.startswith("MOCK_WRITE ")
    ] == writes
    if status == "targetRejected":
        assert attempt["outcome"] == "targetMismatch" and not attempt["identityMatched"]
        assert "MOCK_RESET" not in log
    if status == "interrupted":
        assert attempt["timedOut"] and not attempt["verified"]
    if case in ("recover", "recovery-fails"):
        assert attempt["verifyFailed"] and not attempt["passed"]
    if status in ("verified", "recovered"):
        assert log.index("MOCK_READBACK") < log.index("MOCK_RESET run")
    else:
        assert "MOCK_RESET run" not in log
    assert calls == (
        ["firmware.bin", "recovery.bin"] if "recovery" in final else ["firmware.bin"]
    )


def test_unordered_programmer_markers_cannot_confirm_deployment(flash_job):
    def out_of_order(argv, **options):
        output = [
            "HT_TARGET_MATCH",
            "HT_WRITE_STARTED",
            "HT_VERIFIED",
            "HT_WRITE_COMPLETED",
            "HT_RESET_COMPLETED",
        ]
        options["stdout"].write("\n".join(output).encode())
        return SimpleNamespace(returncode=0)

    code, events = flash_job.run(out_of_order, apply=True)
    final = events[-1]
    assert code == 2 and final["status"] == "operatorReview"
    assert final["targetState"] == "unknown"
    assert not final["attempt"]["verified"]
