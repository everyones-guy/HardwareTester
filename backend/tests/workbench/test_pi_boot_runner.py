import hashlib
import sys

import pytest

from tools import pi_provisioning as provisioning
from tools import run_pi_boot as runner


def fake_boot(script, timeout=5):
    return runner.check_boot([sys.executable, "-u", "-c", script], "READY", timeout)


def test_serial_ready_line_and_bounded_evidence():
    result = fake_boot(
        "import sys, time; "
        "print('s' * 12000); print('d' * 6000, file=sys.stderr); "
        "sys.stdout.buffer.write(b'RE'); time.sleep(.08); "
        "sys.stdout.buffer.write(b'ADY\\r\\n'); time.sleep(30)"
    )
    assert result["verdict"] == "passed"
    assert result["markerObserved"] is True
    assert result["serialTruncated"] and result["emulatorStderrTruncated"]
    assert len(result["serialTail"].encode()) == runner.SERIAL_LIMIT
    assert len(result["emulatorStderrTail"].encode()) == runner.DIAGNOSTIC_LIMIT


def test_embedded_stdout_and_exact_stderr_markers_are_insufficient():
    result = fake_boot(
        "import sys; print('waiting for READY'); print('READY', file=sys.stderr)"
    )
    assert result["verdict"] == "failed"
    assert result["reason"] == "emulatorExitedWithoutMarker"
    assert result["markerObserved"] is False


def test_emulator_error_and_boot_timeout_have_distinct_reasons():
    error = fake_boot("import sys; sys.exit(3)")
    timeout = fake_boot("import time; time.sleep(30)", timeout=0.25)
    assert (error["verdict"], error["reason"], error["emulatorExitCode"]) == (
        "error",
        "emulatorExitedWithError",
        3,
    )
    assert (timeout["verdict"], timeout["reason"]) == ("failed", "bootTimedOut")


def test_bundle_hashes_and_source_change_detection(tmp_path):
    files = {
        runner.KERNEL: b"kernel",
        runner.DTB: b"tree",
        runner.DISK: b"d" * 512,
        runner.INITRD: b"initrd",
    }
    for name, content in files.items():
        (tmp_path / name).write_bytes(content)
    artifacts, fingerprints = provisioning.hash_bundle(tmp_path)
    assert artifacts == {
        name: {"sha256": hashlib.sha256(content).hexdigest(), "sizeBytes": len(content)}
        for name, content in files.items()
    }
    command = runner.boot_command(runner.QEMU, tmp_path, "/dev/mmcblk0p2", True)
    assert "-snapshot" in command
    assert command[command.index("-nic") + 1] == "none"
    assert command[-2:] == ["-initrd", str(tmp_path / runner.INITRD)]
    (tmp_path / runner.DISK).write_bytes(b"shorter")
    with pytest.raises(ValueError, match="changed"):
        provisioning.verify_bundle(tmp_path, fingerprints)
    with pytest.raises(ValueError, match="power-of-two"):
        provisioning.hash_bundle(tmp_path)
