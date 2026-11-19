import hashlib
import json
from types import SimpleNamespace

from tools import flash_openocd as flash


def test_preflight_checks_files_without_running_programmer(monkeypatch, tmp_path):
    profile = tmp_path / "board.json"
    cfg = tmp_path / "board.cfg"
    manifest = tmp_path / "manifest.json"
    binary = tmp_path / "firmware.bin"
    logs = tmp_path / "events.jsonl"
    cfg.write_text("# only used when a rack operator explicitly applies\n")
    profile.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "model": "Test board rev A",
                "architecture": "arm",
                "targetIdentity": "rack-test-rev-a",
                "openocdConfig": "board.cfg",
                "flashAddress": "0x08000000",
                "maxRegionBytes": 1024,
                "eraseBlockBytes": 256,
                "timeoutSeconds": 1,
            }
        )
    )
    data = b"fake firmware test bytes"
    binary.write_bytes(data)
    manifest.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "format": "bin",
                "name": "Fixture",
                "version": "1.0",
                "model": "Test board rev A",
                "architecture": "arm",
                "sizeBytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "flash_openocd",
            "--profile",
            str(profile),
            "--manifest",
            str(manifest),
            "--binary",
            str(binary),
            "--report",
            str(logs),
        ],
    )

    def unexpected(*args, **kwargs):
        raise AssertionError("Default preflight must not invoke OpenOCD")

    monkeypatch.setattr(flash.subprocess, "run", unexpected)
    assert flash.main() == 0
    assert json.loads(logs.read_text().splitlines()[-1])["status"] == "preflightPassed"


def test_program_checks_live_identity_before_write_and_verifies_before_reset(
    monkeypatch, tmp_path
):
    profile = {
        "targetIdentity": "test-rev-a",
        "flashAddress": "0x0",
        "timeoutSeconds": 1,
    }

    def fake(args, **kwargs):
        assert args[2] == "gdb_port disabled; telnet_port disabled; tcl_port disabled"
        script = args[-1]
        assert script.index("hardware_tester_probe") < script.index("flash write_image")
        assert (
            script.index("flash write_image")
            < script.index("verify_image")
            < script.index("reset run")
        )
        kwargs["stdout"].write(
            b"HT_TARGET_MATCH\nHT_WRITE_STARTED\nHT_WRITE_COMPLETED\nHT_VERIFY_FAILED\n"
        )
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(flash.subprocess, "run", fake)
    result = flash.program(
        "openocd", tmp_path / "board.cfg", profile, tmp_path, "firmware.bin", "flash"
    )
    assert result["identityMatched"] and result["verifyFailed"]
    assert not result["verified"] and not result["passed"]
