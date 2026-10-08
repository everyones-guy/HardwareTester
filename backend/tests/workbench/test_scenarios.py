import copy
import time
import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.scenarios import normalize
from Hardware_Tester_App.lab import LabError
from Hardware_Tester_App.transports import SimulationTransport, TransportError


@pytest.fixture
def app(tmp_path):
    app = create_app(
        "testing",
        {"LAB_DB_PATH": str(tmp_path / "scenarios.sqlite3"), "LAB_WORKER": False},
    )
    yield app
    app.extensions["lab"].close()


def apply(app, device, identity="preset-recovery"):
    result = app.test_client().post(
        f"/api/lab/devices/{device['id']}/scenario", json={"scenarioId": identity}
    )
    assert result.status_code == 200


def test_recovery_sequence_restarts_and_does_not_open_device(app):
    lab = app.extensions["lab"]
    d = lab.state["devices"][0]
    apply(app, d)
    lab.diagnose(d["id"])
    assert d["scenarioCursor"] == 0 and not d["connected"]
    lab.connect(d["id"], True)
    for expected in ["failed", "failed", "passed", "passed"]:
        lab.diagnose(d["id"])
        assert d["diagnostics"][0]["status"] == expected
    assert d["scenarioCursor"] == 3
    assert lab.state["logs"][0]["deviceId"] == d["id"]
    assert (
        app.test_client()
        .post(f"/api/lab/devices/{d['id']}/scenario", json={"restart": True})
        .status_code
        == 200
    )
    lab.diagnose(d["id"])
    assert d["diagnostics"][0]["status"] == "failed"
    assert d["scenarioCursor"] == 1


def test_clearing_then_reapplying_uses_current_output(app):
    lab = app.extensions["lab"]
    d = lab.state["devices"][1]
    lab.connect(d["id"], True)
    lab.command(d["id"], 20)
    apply(app, d, "preset-healthy")
    assert (
        app.test_client()
        .post(f"/api/lab/devices/{d['id']}/scenario", json={"scenarioId": None})
        .status_code
        == 200
    )
    lab.command(d["id"], 30)
    apply(app, d, "preset-healthy")
    lab.diagnose(d["id"])
    assert d["value"] == d["scenarioOutput"] == 30


def test_bad_telemetry_recovers_without_changing_output(app):
    lab = app.extensions["lab"]
    d = lab.state["devices"][1]
    lab.connect(d["id"], True)
    lab.command(d["id"], 20)
    apply(app, d, "preset-bad-reading")
    for expected in ["warning", "warning", "passed"]:
        lab.diagnose(d["id"])
        assert d["diagnostics"][0]["status"] == expected
    assert d["value"] == 20
    lab.start(d["id"], "control")
    snapshot = copy.deepcopy(lab.state["runs"][0]["configuration"])
    while lab.active:
        lab.advance()
    assert d["value"] == d["scenarioOutput"] == 20
    assert lab.state["runs"][0]["status"] == "passed"
    assert lab.state["runs"][0]["configuration"] == snapshot


def test_delay_obeys_adapter_timeout(monkeypatch, app):
    d = app.extensions["lab"].state["devices"][0]
    apply(app, d, "preset-delayed")
    adapter = SimulationTransport(d)
    adapter.timeout = 0.1
    sleeps = []
    monkeypatch.setattr("Hardware_Tester_App.transports.time.sleep", sleeps.append)
    with pytest.raises(TransportError, match="exceeded its timeout"):
        adapter.read()
    assert sleeps == [0.1] and d["scenarioCursor"] == 1
    adapter.timeout = 1
    assert adapter.read() == 24
    assert sleeps[-1] == 0.2


def test_snapshots_survive_library_edits_delete_and_restart(app):
    client = app.test_client()
    lab = app.extensions["lab"]
    d = lab.state["devices"][0]
    payload = {
        "name": "Custom",
        "frames": [
            {"behavior": "timeout", "count": 1},
            {"behavior": "healthy", "count": 1},
        ],
    }
    identity = client.post("/api/lab/scenarios", json=payload).json["scenarioId"]
    apply(app, d, identity)
    changed = dict(payload, version=1, frames=[{"behavior": "healthy", "count": 1}])
    assert client.put(f"/api/lab/scenarios/{identity}", json=changed).status_code == 200
    assert d["scenario"]["version"] == 1
    assert client.put(f"/api/lab/scenarios/{identity}", json=changed).status_code == 409
    assert (
        client.delete(f"/api/lab/scenarios/{identity}", json={"version": 2}).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/lab/devices/{d['id']}/scenario", json={"restart": True}
        ).status_code
        == 200
    )
    assert d["scenario"]["frames"][0]["behavior"] == "timeout"
    lab.save()
    path = app.config["LAB_DB_PATH"]
    lab.close()
    restored = create_app("testing", {"LAB_DB_PATH": path, "LAB_WORKER": False})
    try:
        device = restored.extensions["lab"].state["devices"][0]
        assert device["scenario"]["version"] == 1 and not device["connected"]
    finally:
        restored.extensions["lab"].close()


def test_scenario_mutations_blocked_during_run_and_on_real_hardware(app):
    client = app.test_client()
    lab = app.extensions["lab"]
    d = lab.state["devices"][0]
    lab.connect(d["id"], True)
    lab.start(d["id"], "smoke")
    assert (
        client.post(
            f"/api/lab/devices/{d['id']}/scenario",
            json={"scenarioId": "preset-healthy"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/lab/scenarios",
            json={"name": "S", "frames": [{"behavior": "healthy", "count": 1}]},
        ).status_code
        == 409
    )
    lab.cancel()
    d["adapter"] = "serial"
    assert (
        client.post(
            f"/api/lab/devices/{d['id']}/scenario",
            json={"scenarioId": "preset-healthy"},
        ).status_code
        == 403
    )


@pytest.mark.parametrize(
    "frames",
    [
        [],
        [{"behavior": "timeout", "count": True}],
        [{"behavior": "timeout", "count": 0}],
        [{"behavior": "delay", "count": 1, "delayMs": float("inf")}],
        [{"behavior": "delay", "count": 1, "delayMs": 2001}],
        [{"behavior": "healthy", "count": 100}] * 3,
    ],
)
def test_invalid_scenario_limits(frames):
    with pytest.raises(LabError):
        normalize({"name": "S", "frames": frames})


def test_background_worker_does_not_consume_sequence(tmp_path):
    app = create_app(
        "testing", {"LAB_DB_PATH": str(tmp_path / "worker.sqlite3"), "LAB_WORKER": True}
    )
    try:
        lab = app.extensions["lab"]
        d = lab.state["devices"][0]
        apply(app, d)
        lab.connect(d["id"], True)
        time.sleep(1.2)
        assert d["scenarioCursor"] == 0
    finally:
        app.extensions["lab"].close()


def test_presets_protected_and_reset_preserves_library(app):
    client = app.test_client()
    lab = app.extensions["lab"]
    d = lab.state["devices"][0]
    payload = {"name": "Reusable", "frames": [{"behavior": "healthy", "count": 1}]}
    identity = client.post("/api/lab/scenarios", json=payload).json["scenarioId"]
    assert (
        client.put(
            "/api/lab/scenarios/preset-healthy", json=dict(payload, version=1)
        ).status_code
        == 409
    )
    apply(app, d, identity)
    lab.reset()
    assert any(s["id"] == identity for s in lab.state["scenarios"])
    assert all(not device.get("scenario") for device in lab.state["devices"])
