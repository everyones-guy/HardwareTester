"""Loss and replay checks over a real, isolated MQTT broker."""

import json
import shutil
import socket
import subprocess
import time
import uuid
from threading import Event

import paho.mqtt.client as mqtt
import pytest

from Hardware_Tester_App import create_app
from Hardware_Tester_App.transports import (
    MQTTTransport,
    TransportError,
    UncertainDelivery,
)
from test_mqtt_fixture import fixture_module
from test_system_runs import completed


@pytest.fixture(scope="module")
def broker_port(tmp_path_factory):
    executable = shutil.which("mosquitto")
    if not executable:
        pytest.skip("Install Mosquitto to run the loopback fault tests.")
    with socket.socket() as socket_reservation:
        socket_reservation.bind(("127.0.0.1", 0))
        port = socket_reservation.getsockname()[1]
    folder = tmp_path_factory.mktemp("mqtt-recovery")
    config = folder / "mosquitto.conf"
    config.write_text(f"listener {port} 127.0.0.1\nallow_anonymous true\n", "ascii")
    with (folder / "broker.log").open("w+") as log:
        broker = subprocess.Popen(
            [executable, "-c", str(config)], stdout=log, stderr=subprocess.STDOUT
        )
        try:
            deadline = time.monotonic() + 5
            while broker.poll() is None and time.monotonic() < deadline:
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                        break
                except OSError:
                    time.sleep(0.02)
            else:
                log.seek(0)
                pytest.fail(f"Loopback broker failed to start: {log.read()}")
            yield port
        finally:
            if broker.poll() is None:
                broker.terminate()
                try:
                    broker.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    broker.kill()
                    broker.wait(timeout=3)


class FaultPeer:
    def __init__(self, port):
        self.topic = f"lab/recovery/{uuid.uuid4().hex}"
        self.endpoint = f"mqtt://127.0.0.1:{port}/{self.topic}"
        self.fixture = fixture_module()
        self.replies = self.fixture.RequestReplies()
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.port = port
        self.ready = Event()
        self.lost = Event()
        self.state = 0
        self.applied = []
        self.received = []
        self.suppress_restore_reply = False
        self.ignore_restore = False
        self.client.on_connect = lambda client, *_: client.subscribe(
            self.topic + "/command", qos=1
        )
        self.client.on_subscribe = lambda *_: self.ready.set()
        self.client.on_message = self.receive

    def receive(self, client, userdata, message):
        request = self.fixture.decode_request(message)
        if request is None:
            return
        identity, command, value = request
        first_delivery = request not in self.received
        self.received.append(request)

        def execute(command, value):
            if command == "set" and (value != 0 or not self.ignore_restore):
                self.state = value
                self.applied.append((identity, value))
            return {"value": self.state}, 0

        reply, _ = self.replies.resolve(request, execute)
        if command == "set" and first_delivery:
            if value == 0 and self.suppress_restore_reply:
                return
            if value == 1:
                # The command took effect. Replace its first reply with invalid frames.
                for payload in (
                    "{",
                    json.dumps({"id": "stale", "value": value}),
                    json.dumps({"id": identity, "value": "unreadable"}),
                    json.dumps({"id": identity, "error": {"invalid": True}}),
                ):
                    client.publish(self.topic + "/reply", payload, qos=1)
                self.lost.set()
                return
        client.publish(self.topic + "/reply", json.dumps(reply), qos=1)

    def adapter(self):
        return MQTTTransport({"endpoint": self.endpoint})


@pytest.fixture
def peer(broker_port):
    fixture = FaultPeer(broker_port)
    fixture.client.connect("127.0.0.1", broker_port)
    fixture.client.loop_start()
    try:
        assert fixture.ready.wait(3)
        yield fixture
    finally:
        fixture.client.disconnect()
        fixture.client.loop_stop()


def test_lost_reply_same_id_replay_applies_one_effect(peer, tmp_path):
    adapter = peer.adapter()
    observer = peer.adapter()
    try:
        adapter.connect()
        observer.connect()
        adapter.timeout = 0.3
        identity = str(uuid.uuid4())
        with pytest.raises(UncertainDelivery, match="timed out"):
            adapter._exchange(identity, "set", 1)
        assert peer.applied == [(identity, 1)]
        first_read = observer.read()
        assert first_read == 1
        assert adapter._exchange(identity, "set", 1) == 1
        with pytest.raises(TransportError, match="already used"):
            adapter._exchange(identity, "set", 0)
        assert peer.applied == [(identity, 1)]
        assert peer.received.count((identity, "set", 1)) == 2
        replay_read = observer.read()
        assert replay_read == 1
        assert adapter.write(0) == 0
        final_read = observer.read()
        assert final_read == 0
        (tmp_path / "replay.json").write_text(
            json.dumps(
                {
                    "requestId": identity,
                    "firstReplyLost": True,
                    "matchingDeliveries": peer.received.count((identity, "set", 1)),
                    "appliedWrites": peer.applied,
                    "conflictingIdRejected": True,
                    "independentReadbacks": {
                        "beforeReplay": first_read,
                        "afterReplay": replay_read,
                        "afterRestoration": final_read,
                    },
                },
                indent=2,
            ),
            "utf-8",
        )
    finally:
        adapter.close()
        observer.close()


@pytest.mark.parametrize(
    ("cancel", "applied_restore", "verdict", "restoration"),
    [
        (False, True, "failed", "restored"),
        (True, True, "cancelled", "restored"),
        (False, False, "failed", "failed"),
    ],
)
def test_workbench_recovers_or_latches_warning_after_lost_replies(
    peer, tmp_path, cancel, applied_restore, verdict, restoration
):
    peer.ignore_restore = not applied_restore
    peer.suppress_restore_reply = True
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "runs.sqlite3"),
            "LAB_WORKER": False,
            "LAB_AUTH_ENABLED": False,
            "LAB_ALLOW_HARDWARE": True,
        },
    )
    lab = app.extensions["lab"]
    observer = peer.adapter()
    try:
        device_id = lab.add(
            {
                "name": "Loopback relay",
                "kind": "relay",
                "adapter": "mqtt",
                "endpoint": peer.endpoint,
            }
        )
        lab.connect(device_id, True)
        observer.connect()
        client = app.test_client()
        started = client.post(
            "/api/lab/system-runs",
            json={
                "plan": {
                    "name": "Lost replies",
                    "roles": {"relay": "commandRelay"},
                    "steps": [
                        {
                            "name": "Enable",
                            "role": "relay",
                            "action": "command",
                            "active": True,
                        },
                        {
                            "name": "Disable",
                            "role": "relay",
                            "action": "command",
                            "active": False,
                        },
                    ],
                },
                "bench": {
                    "mode": "connected",
                    "devices": {
                        "relay": {"deviceId": device_id, "approvedCommandRelay": True}
                    },
                },
            },
        )
        assert started.status_code == 202
        assert peer.lost.wait(1)
        if cancel:
            assert client.post("/api/lab/runs/cancel", json={}).status_code == 200
        run = completed(lab, started.json["runId"])
        assert run["status"] == verdict and run["restoration"] == restoration
        assert run["steps"][0]["status"] == "failed"
        assert run["steps"][1]["status"] == "pending"
        writes = [
            event for event in run["audit"]["requests"] if event["operation"] == "set"
        ]
        assert [(event["phase"], event["requested"]) for event in writes] == [
            ("step", 1),
            ("restoration", 0),
        ]
        for event in writes:
            assert (
                event["outcome"] == "failed"
                and "delivery is uncertain" in event["error"]
            )
            assert (
                peer.received.count((event["requestId"], "set", event["requested"]))
                == 1
            )
        readback = run["audit"]["requests"][-1]
        assert readback["phase"] == "restoration" and readback["operation"] == "read"
        expected = 0 if applied_restore else 1
        assert readback["observed"] == expected == observer.read()
        assert bool(lab.device(device_id).get("safetyWarning")) != applied_restore
        (tmp_path / "report.json").write_text(json.dumps(run, indent=2), "utf-8")
    finally:
        observer.close()
        lab.close()


def test_device_run_sends_one_restore_and_checks_state_after_lost_ack(peer, tmp_path):
    peer.suppress_restore_reply = True
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "device.sqlite3"),
            "LAB_WORKER": False,
            "LAB_AUTH_ENABLED": False,
            "LAB_ALLOW_HARDWARE": True,
        },
    )
    lab = app.extensions["lab"]
    observer = peer.adapter()
    try:
        device_id = lab.add(
            {
                "name": "Loopback valve",
                "kind": "valve",
                "adapter": "mqtt",
                "endpoint": peer.endpoint,
            }
        )
        lab.connect(device_id, True)
        observer.connect()
        lab.start(device_id, "control")
        for _ in range(4):
            lab.advance()
        run = lab.snapshot()["runs"][0]
        assert run["status"] == "passed" and run["restoration"] == "restored"
        assert [value for _, value in peer.applied] == [75, 0]
        restore = [
            event
            for event in run["audit"]["requests"]
            if event["phase"] == "restoration"
        ]
        assert [event["operation"] for event in restore] == ["set", "read"]
        assert "delivery is uncertain" in restore[0]["error"]
        assert restore[1]["observed"] == observer.read() == 0
        (tmp_path / "report.json").write_text(json.dumps(run, indent=2), "utf-8")
    finally:
        observer.close()
        lab.close()
