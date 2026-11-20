from pathlib import Path

import pytest

from Hardware_Tester_App import create_app
from Hardware_Tester_App.ui_discovery import UiDiscoveryError, discover_ui

from test_auth import setup, user

UI = "/api/lab/ui-catalogs"
FIXTURE = (
    Path(__file__).resolve().parents[3] / "deployment/ui-fixtures/uisee-controller"
)


@pytest.fixture
def inputs():
    return {
        file.name: file.read_text(encoding="utf-8") for file in FIXTURE.glob("*.sql")
    }


def test_source_discovery_rejects_paths_and_only_records_supported_rows(inputs):
    with pytest.raises(UiDiscoveryError):
        discover_ui({"../control.sql": next(iter(inputs.values()))})
    baseline = discover_ui(inputs)
    assert baseline == discover_ui(dict(reversed(list(inputs.items()))))
    assert len(baseline["pages"]) == 2
    assert any(
        control["handler"] == "setValveTarget" for control in baseline["controls"]
    )
    appended = inputs | {"Ignored.sql": "DROP TABLE WidgetsInstalled;"}
    changed = discover_ui(appended)
    assert changed["controls"] == baseline["controls"]
    assert changed["catalogSha256"] != baseline["catalogSha256"]


def test_catalog_binding_generated_plan_replay_and_negative_check(tmp_path, inputs):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "ui.sqlite3"),
            "LAB_WORKER": False,
            "LAB_AUTH_ENABLED": False,
            "LAB_STEP_SECONDS": 0,
        },
    )
    lab = app.extensions["lab"]
    client = app.test_client()
    try:
        imported = client.post(UI, json={"name": "Fixture", "files": inputs})
        assert imported.status_code == 201
        entry = imported.json["catalog"]
        base = f"{UI}/{entry['id']}"
        control = next(
            item
            for item in entry["catalog"]["controls"]
            if item["handler"] == "setValveTarget"
        )
        assert control["source"]["table"] == "WidgetsInstalled"
        assert control["source"]["path"].endswith("Valve.sql")
        revised_files = inputs | {
            "Valve.sql": inputs["Valve.sql"].replace('"ValveTarget"', '"ValveSetpoint"')
        }
        revision = client.post(
            UI, json={"name": "Fixture revision", "files": revised_files}
        ).json["catalog"]
        diff = client.get(f"{UI}/{revision['id']}/compare?baseline={entry['id']}").json[
            "comparison"
        ]["controls"]
        assert diff["changed"][0]["before"] == "ValveTarget"
        assert diff["changed"][0]["after"] == "ValveSetpoint"
        assert diff["added"] == diff["removed"] == []
        payload = {
            "controlId": control["id"],
            "name": "Readback",
            "value": 54,
            "expected": 54,
            "tolerance": 0,
            "timeout": 2,
        }
        assert client.post(f"{base}/plans", json=payload).status_code == 409
        binding = {
            "controlId": control["id"],
            "handler": "setValveTarget",
            "kind": "valve",
            "reference": "Reviewed lab C++ fixture controller.cpp",
        }
        assert (
            client.post(
                f"{base}/bindings", json=binding | {"handler": "other"}
            ).status_code
            == 400
        )
        assert client.post(f"{base}/bindings", json=binding).status_code == 200
        assert (
            client.post(f"{base}/plans", json=payload | {"value": 54.5}).status_code
            == 400
        )
        generated = client.post(f"{base}/plans", json=payload)
        assert generated.status_code == 201
        identity = generated.json["planId"]
        saved = client.get(f"/api/lab/test-plans/{identity}").json["plan"]
        assert saved["uiSource"]["catalogSha256"] == entry["id"]
        assert [step["action"] for step in saved["steps"]] == [
            "read",
            "set",
            "assert_equal",
        ]
        replay = client.post("/api/lab/test-plans", json=saved)
        assert replay.status_code == 200
        target = next(
            device["id"] for device in lab.state["devices"] if device["kind"] == "valve"
        )
        lab.connect(target, True)

        def run(plan):
            assert (
                client.post(
                    "/api/lab/runs", json={"deviceId": target, "plan": plan}
                ).status_code
                == 202
            )
            for _ in range(12):
                if lab.active is None:
                    break
                lab.advance()
            return lab.state["runs"][0]

        good = run(replay.json["planId"])
        assert good["status"] == "passed"
        assert good["configuration"]["plan"]["uiSource"] == saved["uiSource"]
        assert good["restoration"] == "restored"
        bad_plan = client.post(f"{base}/plans", json=payload | {"expected": 55})
        bad = run(bad_plan.json["planId"])
        assert bad["status"] == "failed"
        assert bad["steps"][3]["observed"] == 54
        assert bad["restoration"] == "restored"
        saved["steps"][2]["value"] = 43
        assert client.post("/api/lab/test-plans", json=saved).status_code == 400
        assert (
            client.put(
                f"/api/lab/test-plans/{identity}",
                json={k: v for k, v in saved.items() if k != "uiSource"},
            ).status_code
            == 200
        )
        assert (
            "uiSource" not in client.get(f"/api/lab/test-plans/{identity}").json["plan"]
        )
    finally:
        lab.close()


def test_catalog_writes_require_admin(tmp_path, inputs):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "roles.sqlite3"),
            "LAB_WORKER": False,
            "LAB_AUTH_ENABLED": True,
        },
    )
    try:
        admin = app.test_client()
        auth = setup(admin)
        operator, csrf = user(app, admin, auth["csrf"], "operator")
        headers = {"X-CSRF-Token": csrf}
        assert operator.get(UI).status_code == 200
        assert (
            operator.post(
                UI, json={"name": "Fixture", "files": inputs}, headers=headers
            ).status_code
            == 403
        )
    finally:
        app.extensions["lab"].close()
