import json
from pathlib import Path

from tools import run_system_plan as runner

ROOT = Path(__file__).resolve().parents[3]


def test_unchanged_plan_model_and_connected_report(monkeypatch, tmp_path):
    plan = ROOT / "deployment" / "plans" / "controller-sensor-fault.json"
    model = ROOT / "deployment" / "fixtures" / "controller-sensor-fault.json"
    first, second = (tmp_path / name for name in ("modeled.json", "connected.json"))
    binding = tmp_path / "binding.json"
    normal = json.loads(model.read_text())["normal"]
    failed = json.loads(model.read_text())["sensorFailed"]
    faulted = False
    commands = []
    connected = []

    class FakeTransport:
        def __init__(self, spec):
            self.role = spec["endpoint"].rsplit("/", 1)[-1]

        def connect(self):
            connected.append(self.role)

        def close(self):
            connected.remove(self.role)

        def read(self):
            if self.role == "temperatureFaultRelay":
                return int(faulted)
            return (failed if faulted else normal)[self.role]

        def write(self, value):
            nonlocal faulted
            commands.append((self.role, value))
            faulted = bool(value)
            return value

    def run(bench, report, *extra):
        monkeypatch.setattr(
            "sys.argv",
            [
                "run_system_plan",
                "--plan",
                str(plan),
                "--bench",
                str(bench),
                "--report",
                str(report),
                *extra,
            ],
        )
        return runner.main()

    assert run(model, first) == 0
    roles = json.loads(plan.read_text())["roles"]
    devices = {
        role: {"adapter": "mqtt", "endpoint": f"mqtt://test-bench/lab/{role}"}
        for role in roles
    }
    binding.write_text(json.dumps({"mode": "connected", "devices": devices}))
    monkeypatch.setattr(runner, "create_transport", FakeTransport)
    blocked = tmp_path / "blocked.json"
    assert run(binding, blocked, "--allow-connected") == 1
    assert json.loads(blocked.read_text())["status"] == "blocked"
    assert not connected and not commands

    devices["temperatureFaultRelay"]["approvedFaultRelay"] = True
    binding.write_text(json.dumps({"mode": "connected", "devices": devices}))
    assert run(binding, second, "--allow-connected", "--reference", str(first)) == 0
    report = json.loads(second.read_text())
    assert report["planSha256"] == json.loads(first.read_text())["planSha256"]
    assert len(report["comparison"]["steps"]) == 10
    assert all(role == "temperatureFaultRelay" for role, _ in commands)
    assert commands[0][1] == 1 and commands[-1][1] == 0
    assert report["restoration"] == {"temperatureFaultRelay": "verified"}
    assert not connected and not faulted


def test_multi_state_model_start_stop_faults_and_recovery():
    source = ROOT / "deployment"
    plan, _ = runner.object_file(source / "plans/controller-start-stop.json")
    model, _ = runner.object_file(source / "fixtures/controller-start-stop.json")
    roles, steps = runner.validate_plan(plan)
    good = {"steps": [], "restoration": {}}
    bench = runner.StateMachineBench(roles, model)
    runner.run_steps(bench, steps, good)
    assert len(good["steps"]) == 22
    assert all(step["passed"] for step in good["steps"])
    assert set(good["restoration"].values()) == {"verified"}
    assert bench.current == "stopped"

    model["states"]["sensorFault"]["readings"]["temperatureSensor"] = None
    bench = runner.StateMachineBench(roles, model)
    failure = {"steps": [], "restoration": {}}
    runner.run_steps(bench, steps, failure)
    assert failure["steps"][-1]["passed"] is False
    assert "No modeled response" in failure["steps"][-1]["error"]
    assert bench.current == "stopped"
    assert set(failure["restoration"].values()) == {"verified"}
