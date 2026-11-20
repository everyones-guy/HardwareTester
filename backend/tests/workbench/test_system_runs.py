import hashlib
import io
import json
import time
from pathlib import Path
from threading import Event

from Hardware_Tester_App import create_app
from Hardware_Tester_App.workspace_backup import recorded_run

from test_auth import setup, user

ROOT = Path(__file__).resolve().parents[3] / "deployment"


def completed(lab, identity):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        run = next(item for item in lab.snapshot()["runs"] if item["id"] == identity)
        if run["status"] != "running":
            return run
        time.sleep(0.01)
    raise AssertionError("The system run did not complete.")


def test_model_and_device_share_durable_operator_release_and_request_history(tmp_path):
    config = {
        "LAB_DB_PATH": str(tmp_path / "runs.sqlite3"),
        "LAB_WORKER": False,
        "LAB_AUTH_ENABLED": True,
        "LAB_ALLOW_HARDWARE": False,
    }
    app = create_app("testing", config)
    lab = app.extensions["lab"]
    try:
        admin = app.test_client()
        credentials = setup(admin)
        headers = {"X-CSRF-Token": credentials["csrf"]}
        firmware = b"synthetic firmware identity"
        sha = hashlib.sha256(firmware).hexdigest()
        uploaded = admin.post(
            "/api/lab/firmware",
            headers=headers,
            data={
                "metadata": json.dumps(
                    {
                        "name": "Bench fixture",
                        "version": "1.0",
                        "model": "Synthetic",
                        "architecture": "fixture",
                        "sha256": sha,
                    }
                ),
                "binary": (io.BytesIO(firmware), "fixture.bin"),
            },
        )
        assert uploaded.status_code == 201
        plan = json.loads((ROOT / "plans/controller-start-stop.json").read_bytes())
        model = json.loads((ROOT / "fixtures/controller-start-stop.json").read_bytes())
        payload = {"plan": plan, "bench": model, "releaseSha256": sha}
        viewer, csrf = user(app, admin, credentials["csrf"], "viewer")
        assert (
            viewer.post(
                "/api/lab/system-runs", headers={"X-CSRF-Token": csrf}, json=payload
            ).status_code
            == 403
        )
        assert (
            app.test_client().post("/api/lab/system-runs", json=payload).status_code
            == 401
        )
        operator, csrf = user(app, admin, credentials["csrf"], "operator")
        operator_headers = {"X-CSRF-Token": csrf}
        assert (
            operator.post(
                "/api/lab/system-runs",
                headers=operator_headers,
                json=payload | {"releaseSha256": "f" * 64},
            ).status_code
            == 400
        )
        fx = operator.post(
            "/api/lab/system-runs", headers=operator_headers, json=payload
        )
        assert fx.status_code == 202
        system = completed(lab, fx.json["runId"])
        assert system["status"] == "passed" and len(system["steps"]) == 22
        audit = system["audit"]
        assert (
            audit["operator"]["role"] == "operator"
            and audit["operator"] == system["startedBy"]
        )
        assert audit["release"]["sha256"] == sha
        assert len({event["requestId"] for event in audit["requests"]}) == len(
            audit["requests"]
        )
        assert {event["idSource"] for event in audit["requests"]} == {"local"}
        assert {event["phase"] for event in audit["requests"]} == {
            "step",
            "restoration",
        }
        assert set(audit["restorationByRole"].values()) == {"verified"}
        assert recorded_run(system) == system

        device_id = lab.state["devices"][0]["id"]
        lab.connect(device_id, True)
        fx = operator.post(
            "/api/lab/runs",
            headers=operator_headers,
            json={"deviceId": device_id, "plan": "smoke", "releaseSha256": sha},
        )
        assert fx.status_code == 202
        for _ in range(8):
            lab.advance()
        individual = completed(lab, fx.json["runId"])
        assert individual["audit"]["kind"] == "device"
        assert individual["audit"]["operator"] == audit["operator"]
        assert individual["audit"]["release"] == audit["release"]
        assert individual["audit"]["requests"]
        assert recorded_run(individual) == individual
    finally:
        lab.close()

    reopened = create_app("testing", config)
    try:
        assert reopened.extensions["lab"].snapshot()["runs"][:2] == [individual, system]
    finally:
        reopened.extensions["lab"].close()


def test_connected_system_owns_the_bench_until_cancel_restores_relay(tmp_path):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "cancel.sqlite3"),
            "LAB_WORKER": False,
            "LAB_AUTH_ENABLED": False,
            "LAB_ALLOW_HARDWARE": True,
        },
    )
    lab = app.extensions["lab"]
    waiting = Event()
    release = Event()

    class Relay:
        state = 0

        def read(self):
            return self.state

        def write(self, value):
            self.state = value
            return value

    class Sensor:
        def read(self):
            waiting.set()
            assert release.wait(3)
            return 24

    try:
        client = app.test_client()
        relay = lab.add(
            {
                "name": "Synthetic relay",
                "kind": "relay",
                "adapter": "mqtt",
                "endpoint": "mqtt://127.0.0.1/relay",
            }
        )
        sensor = lab.add(
            {
                "name": "Synthetic sensor",
                "kind": "temperature",
                "adapter": "mqtt",
                "endpoint": "mqtt://127.0.0.1/sensor",
            }
        )
        actuator = Relay()
        for identity, provider in ((relay, actuator), (sensor, Sensor())):
            lab.device(identity)["connected"] = True
            lab.adapters[identity] = provider
            provider.close = lambda: None

        plan = {
            "name": "Cancellation probe",
            "roles": {"relay": "commandRelay", "sensor": "telemetry"},
            "steps": [
                {
                    "name": "Enable",
                    "role": "relay",
                    "action": "command",
                    "active": True,
                },
                {
                    "name": "Read",
                    "role": "sensor",
                    "action": "expect",
                    "value": 24,
                    "tolerance": 0,
                    "withinSeconds": 2,
                },
            ],
        }
        devices = {
            "relay": {"deviceId": relay, "approvedCommandRelay": False},
            "sensor": {"deviceId": sensor},
        }
        body = {"plan": plan, "bench": {"mode": "connected", "devices": devices}}
        assert client.post("/api/lab/system-runs", json=body).status_code == 400
        assert actuator.state == 0
        devices["relay"]["approvedCommandRelay"] = True
        started = client.post("/api/lab/system-runs", json=body)
        assert started.status_code == 202
        assert waiting.wait(3) and actuator.state == 1
        assert (
            client.post(
                f"/api/lab/devices/{relay}/connection", json={"connected": False}
            ).status_code
            == 409
        )
        assert client.post("/api/lab/runs/cancel", json={}).status_code == 200
        release.set()
        finish = completed(lab, started.json["runId"])
        assert actuator.state == 0
        assert finish["status"] == "cancelled" and finish["restoration"] == "restored"
        assert finish["audit"]["restorationByRole"] == {"relay": "verified"}
    finally:
        release.set()
        lab.close()
