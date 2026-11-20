import importlib.util
import json
from pathlib import Path
import threading
import time
from types import SimpleNamespace
import pytest
import paho.mqtt.client as mqtt
from Hardware_Tester_App import transports


def fixture_module():
    spec = importlib.util.spec_from_file_location(
        "fixture", Path(__file__).parents[2] / "tools/mqtt_fixture.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("failure", [False, True])
def test_health_probe_is_read_only_and_closes_on_failure(monkeypatch, failure):
    fixture = fixture_module()
    calls = []

    class Peer:
        def __init__(self, device):
            assert device["endpoint"] == "mqtt://broker:1883/lab/demo-valve"

        def connect(self):
            calls.append("connect")
            if failure:
                raise RuntimeError("unavailable")

        def close(self):
            calls.append("close")

    monkeypatch.setattr(transports, "MQTTTransport", Peer)
    monkeypatch.setattr(
        "sys.argv", ["mqtt_fixture.py", "--broker", "broker", "--check"]
    )
    if failure:
        with pytest.raises(RuntimeError):
            fixture.main()
    else:
        fixture.main()
    assert calls == ["connect", "close"]


def test_mock_valve_correlates_replies_and_rejects_invalid_outputs(monkeypatch):
    fixture = fixture_module()
    replies = []

    class Client:
        def __init__(self, *args):
            pass

        def connect(self, *args):
            pass

        def disconnect(self):
            pass

        def loop_stop(self):
            pass

        def publish(self, topic, payload, **options):
            assert topic == "lab/demo-valve/reply"
            assert options == {"qos": 1, "retain": False}
            replies.append(json.loads(payload))

        def loop_start(self):
            for request in [
                {"id": "a", "command": "read"},
                {"id": "b", "command": "set", "value": 75},
                {"id": "c", "command": "set", "value": True},
                {"id": "d", "command": "set", "value": 200},
                {"id": "e", "command": "read"},
                [],
            ]:
                self.on_message(
                    self, None, SimpleNamespace(payload=json.dumps(request).encode())
                )

    monkeypatch.setattr(mqtt, "Client", Client)
    monkeypatch.setattr(fixture.signal, "signal", lambda *args: None)
    monkeypatch.setattr(fixture.threading.Event, "wait", lambda *args: None)
    monkeypatch.setattr("sys.argv", ["mqtt_fixture.py"])
    fixture.main()
    assert replies[0] == {"id": "a", "value": 0}
    assert replies[1] == {"id": "b", "value": 75}
    assert all("error" in r for r in replies[2:4])
    assert replies[4] == {"id": "e", "value": 75}


def example_model_path():
    return Path(__file__).parents[3] / "deployment/fixtures/valve-state-machine.json"


def test_model_command_transitions_faults_recovery_and_restart():
    fixture = fixture_module()
    model = fixture.load_model(example_model_path())
    replies = fixture.RequestReplies()

    def request(identity, command, value=0):
        return replies.resolve((identity, command, value), model.execute)

    assert request("read", "read") == ({"id": "read", "value": 0}, 35)
    assert request("move", "set", 89.9) == ({"id": "move", "value": 89.9}, 120)
    error, delay = request("overload", "set", 90)
    assert "overload" in error["error"]
    assert delay == 150
    assert model.output == 89.9
    assert request("lost", "read") == (None, 0)
    assert request("reset", "set", 0) == ({"id": "reset", "value": 0}, 120)
    assert model.state == "recovering"
    assert request("reset", "set", 100) == (
        {"id": "reset", "error": fixture.REQUEST_CONFLICT},
        0,
    )
    assert request("lost", "read") == (None, 0)
    assert request("reset", "set", 0) == ({"id": "reset", "value": 0}, 0)
    assert request("move", "set", 89.9) == ({"id": "move", "value": 89.9}, 0)
    assert model.state == "recovering"
    assert model.output == 0
    assert request("recover", "read") == ({"id": "recover", "value": 0}, 450)
    assert model.state == "ready"
    assert request("next", "read") == ({"id": "next", "value": 0}, 35)
    assert fixture.load_model(example_model_path()).execute("read") == (
        {"value": 0},
        35,
    )


def test_fixture_limits_remembered_outcomes(monkeypatch):
    fixture = fixture_module()
    monkeypatch.setattr(fixture, "MAX_REMEMBERED_REQUESTS", 2)
    replies = fixture.RequestReplies()
    applied = []

    def execute(command, value):
        applied.append(value)
        return {"value": value}, 0

    for identity, value in [("a", 1), ("b", 2), ("a", 1), ("c", 3), ("a", 1)]:
        assert replies.resolve((identity, "set", value), execute) == (
            {"id": identity, "value": value},
            0,
        )
    assert applied == [1, 2, 3, 1]


@pytest.mark.parametrize(
    ("transition", "error"),
    [
        ({"command": "read", "reply": {"type": "value"}}, "Overlapping read"),
        (
            {"command": "set", "when": {"exactly": 90}, "reply": {"type": "value"}},
            "Overlapping set",
        ),
        ({"command": "set", "reply": {"type": "shell"}}, "Reply must be"),
        (
            {"command": "set", "reply": {"type": "value", "delayMs": 5001}},
            "delayMs",
        ),
        (
            {"command": "read", "reply": {"type": "value"}, "script": "anything"},
            "Unknown fields",
        ),
    ],
)
def test_model_rejects_ambiguous_or_invalid_transitions(tmp_path, transition, error):
    fixture = fixture_module()
    model = json.loads(example_model_path().read_text(encoding="utf-8"))
    model["states"]["ready"].append({"target": "ready", **transition})
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(model), encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        fixture.load_model(path)


def test_signal_measurement_can_be_out_of_range_without_changing_output(tmp_path):
    fixture = fixture_module()
    model = json.loads(example_model_path().read_text(encoding="utf-8"))
    model["states"]["ready"][0]["reply"] = {"type": "value", "value": -8}
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(model), encoding="utf-8")
    model = fixture.load_model(path)
    assert model.execute("set", 20) == ({"value": 20}, 120)
    assert model.execute("read") == ({"value": -8}, 0)
    assert model.output == 20


def test_model_fixture_publishes_delayed_correlated_replies(monkeypatch, tmp_path):
    fixture = fixture_module()
    model = json.loads(example_model_path().read_text(encoding="utf-8"))
    model["states"]["ready"][0]["reply"]["delayMs"] = 0
    model["states"]["ready"][1]["reply"]["delayMs"] = 300
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(model), encoding="utf-8")
    handlers = {}
    published = []
    replied = threading.Event()

    class Client:
        def __init__(self, *args):
            pass

        def max_queued_messages_set(self, limit):
            assert limit == 2 * fixture.MAX_PENDING_REPLIES

        def connect(self, *args):
            pass

        def disconnect(self):
            pass

        def loop_stop(self):
            pass

        def publish(self, topic, payload, **options):
            assert topic == "lab/model/reply"
            assert options == {"qos": 1, "retain": False}
            published.append((time.monotonic(), json.loads(payload)))
            if len(published) == 3:
                replied.set()

        def send(self, request, retain=False):
            self.on_message(
                self,
                None,
                SimpleNamespace(payload=json.dumps(request).encode(), retain=retain),
            )

        def loop_start(self):
            self.send({"id": "stale", "command": "set", "value": 90}, retain=True)
            started = time.monotonic()
            self.send({"id": "move", "command": "set", "value": 75})
            self.send({"id": "move", "command": "set", "value": 90})
            self.send({"id": "read", "command": "read"})
            assert replied.wait(3)
            assert published[2][0] - started >= 0.28
            handlers[fixture.signal.SIGINT]()

    monkeypatch.setattr(mqtt, "Client", Client)
    monkeypatch.setattr(fixture.signal, "signal", handlers.__setitem__)
    monkeypatch.setattr(
        "sys.argv", ["mqtt_fixture.py", "--topic", "lab/model", "--model", str(path)]
    )
    fixture.main()
    assert [payload for _, payload in published] == [
        {"id": "move", "error": fixture.REQUEST_CONFLICT},
        {"id": "read", "value": 75},
        {"id": "move", "value": 75},
    ]
