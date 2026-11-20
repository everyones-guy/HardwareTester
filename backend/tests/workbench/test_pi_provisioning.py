import hashlib
import json
from types import SimpleNamespace

import pytest

from tools import capture_pi_inventory as capture
from tools import pi_provisioning as provisioning
from tools import run_pi_boot as runner

from test_pi_inventories import API, INVENTORY, app, db_config


def write(root, name, content):
    destination = root / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination


def pi_root(root):
    write(root, "proc/device-tree/model", INVENTORY["model"].encode() + b"\0")
    write(root, "etc/os-release", b'ID=debian\nVERSION_ID="13"\n')
    write(root, "proc/meminfo", b"MemTotal: 943104 kB\n")
    write(root, "boot/firmware/start.elf", b"start firmware")
    write(root, "boot/firmware/config.txt", b"enable_uart=0\n")
    write(root, "boot/firmware/cmdline.txt", b"console=serial0\n")
    return root


@pytest.fixture
def release(tmp_path):
    for name, content in {
        provisioning.KERNEL: b"kernel",
        provisioning.DTB: b"tree",
        provisioning.DISK: b"d" * 512,
    }.items():
        write(tmp_path, name, content)
    for name in provisioning.BOOTSTRAP_FILES:
        write(tmp_path, name, b"bootstrap input\r\n")
    manifest = {
        "schemaVersion": 1,
        "profile": provisioning.PROFILE,
        "release": "Synthetic Pi 3B release",
        "os": {"id": "debian", "version": "13"},
        "artifacts": provisioning.hash_bundle(tmp_path)[0],
        "bootstrap": provisioning.hash_bootstrap(tmp_path),
        "boot": {
            "rootDevice": "PARTUUID=27b94958-02",
            "readyMarker": "READY",
            "timeoutSeconds": 20,
        },
    }
    return manifest


def test_read_only_captures_and_drift_endpoint(app, tmp_path):
    root = pi_root(tmp_path / "pi")
    system = SimpleNamespace(machine="arm64", release="test-kernel")
    current = {"ssh": "inactive", "revision": "a" * 40}
    calls = []

    def observe(argv):
        calls.append(argv)
        if argv == ["vcgencmd", "version"]:
            return f"sample build\nversion {current['revision']} (release)\n"
        assert argv == [
            "systemctl",
            "show",
            "--no-pager",
            "--property=Id,LoadState,ActiveState,UnitFileState",
            *capture.SERVICE_UNITS,
        ]
        return (
            "Id=ssh.service\nLoadState=loaded\n"
            f"ActiveState={current['ssh']}\nUnitFileState=enabled\n\n"
            "Id=mosquitto.service\nLoadState=not-found\nActiveState=inactive\nUnitFileState=\n"
        )

    before = capture.collect_inventory(root, system, observe)
    boot_config = write(root, "boot/firmware/config.txt", b"enable_uart=1\n")
    current.update(ssh="active", revision="b" * 40)
    after = capture.collect_inventory(root, system, observe)
    before["capturedAt"] = "2026-01-10T13:30:00Z"
    after["capturedAt"] = "2026-01-10T13:31:00Z"
    assert before["schemaVersion"] == after["schemaVersion"] == 2
    assert len(calls) == 4
    assert (
        after["observations"]["configuration"]["bootConfigSha256"]
        == hashlib.sha256(boot_config.read_bytes()).hexdigest()
    )
    assert "enable_uart" not in json.dumps(after)
    client = app.test_client()

    def save(name, inventory):
        result = client.post(API, json={"name": name, "inventory": inventory})
        assert result.status_code == 201
        return result.json["inventories"][0]["id"]

    baseline = save("Before", before)
    updated = save("After", after)
    archived = save("Older schema", INVENTORY)
    comparison = client.get(f"{API}/{updated}/drift?baselineId={baseline}")
    assert comparison.status_code == 200
    items = {item["name"]: item for item in comparison.json["items"]}
    assert {name for name, item in items.items() if item["status"] == "changed"} == {
        "ssh.service",
        "bootConfigSha256",
        "videoCoreRevision",
    }
    assert items["ssh.service"]["after"]["activeState"] == "active"
    assert items["mosquitto.service"]["status"] == "unchanged"
    assert items["NetworkManager.service"]["status"] == "unavailable"
    older = client.get(f"{API}/{updated}/drift?baselineId={archived}").json["items"]
    assert all(
        item["status"] == "unavailable" for item in older if item["group"] != "platform"
    )
    assert client.get(f"{API}/{baseline}/drift?baselineId={updated}").status_code == 400

    (tmp_path / "before.json").write_text(json.dumps(before, indent=2), "utf-8")
    (tmp_path / "after.json").write_text(json.dumps(after, indent=2), "utf-8")
    (tmp_path / "drift.json").write_text(json.dumps(comparison.json, indent=2), "utf-8")


def test_api_generates_plan_for_aarch64_inventory(app, release):
    client = app.test_client()
    for architecture, status in [("aarch64", 200), ("armv7l", 400)]:
        imported = client.post(
            API,
            json={
                "name": architecture,
                "inventory": INVENTORY | {"architecture": architecture},
            },
        )
        identity = imported.json["inventories"][0]["id"]
        result = client.post(
            f"{API}/{identity}/provisioning-plan", json={"manifest": release}
        )
        assert result.status_code == status
        if status == 200:
            assert result.json["plan"] == provisioning.make_plan(INVENTORY, release)
        else:
            assert "aarch64" in result.json["error"]


@pytest.mark.parametrize(
    "change", ["altered-image", "wrong-architecture", "unexpected-initramfs"]
)
def test_plan_rejection_precedes_qemu_launch(
    tmp_path, monkeypatch, release, capsys, change
):
    plan = provisioning.make_plan(INVENTORY, release)
    if change == "altered-image":
        write(tmp_path, provisioning.DISK, b"x" + b"d" * 511)
    elif change == "wrong-architecture":
        plan["target"]["architecture"] = "armv7l"
    else:
        write(tmp_path, provisioning.INITRD, b"unexpected file")
    path = write(tmp_path, "plan.json", json.dumps(plan).encode())
    monkeypatch.setattr(runner, "BUNDLE", tmp_path)
    monkeypatch.setattr("sys.argv", ["run_pi_boot", "--plan", str(path)])

    def unexpected(*args, **kwargs):
        raise AssertionError(
            "QEMU must not start before the provisioning plan is verified."
        )

    monkeypatch.setattr(runner.subprocess, "check_output", unexpected)
    monkeypatch.setattr(runner, "check_boot", unexpected)
    assert runner.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["reason"] == "provisioningPlanRejected"
    assert report["emulatorVersion"] is None


def test_bootstrap_gate_compares_local_inputs_board_and_os(tmp_path, release):
    plan = provisioning.make_plan(INVENTORY, release)
    device = pi_root(tmp_path / "pi")
    provisioning.check_bootstrap(plan, tmp_path, device, "aarch64")
    with pytest.raises(ValueError, match="aarch64"):
        provisioning.check_bootstrap(plan, tmp_path, device, "armv7l")
    write(device, "etc/os-release", b"ID=debian\nVERSION_ID=12\n")
    with pytest.raises(ValueError, match="running OS"):
        provisioning.check_bootstrap(plan, tmp_path, device, "aarch64")
    write(tmp_path, "backend/tools/capture_pi_inventory.py", b"modified collector")
    with pytest.raises(ValueError, match="capture_pi_inventory.py SHA-256"):
        provisioning.check_bootstrap(plan, tmp_path, device, "aarch64")
