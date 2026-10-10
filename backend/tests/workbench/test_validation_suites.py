import copy
import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.validation_suites import normalize
from Hardware_Tester_App.lab import LabError


@pytest.fixture
def app(tmp_path):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "suites.sqlite3"),
            "LAB_WORKER": False,
            "LAB_STEP_SECONDS": 0,
        },
    )
    yield app
    app.extensions["lab"].close()


def create(app, cases=None, plan="smoke"):
    response = app.test_client().post(
        "/api/lab/validation-suites",
        json=dict(
            name="Regression suite",
            kind="temperature",
            planId=plan,
            cases=cases
            or [
                dict(name="Healthy", scenarioId="preset-healthy", expected=["passed"]),
                dict(
                    name="Bad reading",
                    scenarioId="preset-sustained-bad-reading",
                    expected=["failed"],
                ),
                dict(
                    name="Recovery",
                    scenarioId="preset-recovery",
                    expected=["failed", "passed"],
                ),
            ],
        ),
    )
    assert response.status_code == 200, response.json
    return response.json["suiteId"]


def start(app, identity):
    lab = app.extensions["lab"]
    device = lab.state["devices"][0]
    lab.connect(device["id"], True)
    response = app.test_client().post(
        f"/api/lab/validation-suites/{identity}/run", json={"deviceId": device["id"]}
    )
    assert response.status_code == 200, response.json
    return lab, device, lab.state["suiteRuns"][0]


def finish(lab):
    for _ in range(300):
        if not lab.suites.active:
            return
        if lab.active:
            lab.advance()
        lab.suites.tick()
    pytest.fail("Suite did not finish")


def test_suite_matches_expected_failures_recovers_and_restores(app):
    identity = create(app)
    lab = app.extensions["lab"]
    d = lab.state["devices"][0]
    d.update(fault="timeout", scenario=None, value=26, enabled=True)
    original = copy.deepcopy(d)
    lab, d, report = start(app, identity)
    finish(lab)
    assert report["status"] == "passed"
    assert [[a["run"]["status"] for a in c["attempts"]] for c in report["cases"]] == [
        ["passed"],
        ["failed"],
        ["failed", "passed"],
    ]
    for key in ("fault", "scenario", "value", "enabled"):
        assert d[key] == original[key]
    assert "scenarioOutput" not in d and report["restoration"] == "restored"
    assert (
        report["cases"][2]["attempts"][0]["run"]["configuration"]["device"][
            "scenarioCursor"
        ]
        == 0
    )
    assert (
        report["cases"][2]["attempts"][1]["run"]["configuration"]["device"][
            "scenarioCursor"
        ]
        > 0
    )
    for c in report["cases"]:
        assert all(a["matched"] for a in c["attempts"])
    snapshot = copy.deepcopy(report)
    app.test_client().delete(
        f"/api/lab/validation-suites/{identity}", json={"version": 1}
    )
    assert lab.state["suiteRuns"][0] == snapshot


def test_mismatch_is_suite_failure_even_when_test_passes(app):
    identity = create(
        app,
        [
            dict(
                name="Wrong expectation",
                scenarioId="preset-healthy",
                expected=["failed"],
            )
        ],
    )
    lab, d, r = start(app, identity)
    finish(lab)
    assert r["status"] == "failed" and not r["cases"][0]["attempts"][0]["matched"]


def test_cancel_blocks_writes_and_restores_applied_snapshot(app):
    lab = app.extensions["lab"]
    d = lab.state["devices"][0]
    app.test_client().post(
        f"/api/lab/devices/{d['id']}/scenario", json={"scenarioId": "preset-delayed"}
    )
    d["scenarioCursor"] = 3
    original = copy.deepcopy(d)
    identity = create(app)
    lab, d, r = start(app, identity)
    client = app.test_client()
    for path, data in [
        ("/api/lab/reset", {}),
        ("/api/lab/scenarios", {}),
        ("/api/lab/runs", {"deviceId": d["id"], "plan": "smoke"}),
        (f"/api/lab/devices/{d['id']}/command", {"value": 20}),
    ]:
        assert client.post(path, json=data).status_code == 409
    assert client.get("/api/lab").status_code == 200
    assert client.post("/api/lab/suite-runs/cancel", json={}).status_code == 200
    assert r["status"] == "cancelled" and not lab.active
    assert d["scenario"] == original["scenario"] and d["scenarioCursor"] == 3
    assert client.post("/api/lab/scenarios", json={}).status_code == 400


def test_versions_deleted_dependencies_and_profile_mismatch(app):
    identity = create(app)
    client = app.test_client()
    lab = app.extensions["lab"]
    assert (
        client.delete(
            f"/api/lab/validation-suites/{identity}", json={"version": True}
        ).status_code
        == 409
    )
    d = lab.state["devices"][1]
    lab.connect(d["id"], True)
    assert (
        client.post(
            f"/api/lab/validation-suites/{identity}/run", json={"deviceId": d["id"]}
        ).status_code
        == 409
    )
    d = lab.state["devices"][0]
    d["adapter"] = "serial"
    d["connected"] = True
    assert (
        client.post(
            f"/api/lab/validation-suites/{identity}/run", json={"deviceId": d["id"]}
        ).status_code
        == 403
    )
    d["adapter"] = "simulation"
    d["connected"] = False
    lab.state["scenarios"] = [
        s for s in lab.state["scenarios"] if s["id"] != "preset-healthy"
    ]
    lab.connect(d["id"], True)
    assert (
        client.post(
            f"/api/lab/validation-suites/{identity}/run", json={"deviceId": d["id"]}
        ).status_code
        == 404
    )
    assert not lab.suites.active and not lab.state["suiteRuns"]


@pytest.mark.parametrize(
    "cases",
    [
        [],
        [{}],
        [dict(name="x", scenarioId="preset-healthy", expected=["cancelled"])],
        [dict(name="x", scenarioId="preset-healthy", expected=["passed"] * 4)],
    ],
)
def test_invalid_cases(cases):
    with pytest.raises(LabError):
        normalize(dict(name="Suite", kind="relay", planId="smoke", cases=cases))


def test_restart_cancels_and_preserves_suite_library(app):
    identity = create(app)
    lab, d, r = start(app, identity)
    original = r["device"]
    path = lab.connection.execute("PRAGMA database_list").fetchone()[2]
    lab.save()
    lab.connection.close()
    lab.closed = True
    restarted = create_app("testing", {"LAB_DB_PATH": path, "LAB_WORKER": False})
    try:
        other = restarted.extensions["lab"]
        report = other.state["suiteRuns"][0]
        assert report["status"] == "cancelled" and report["restoration"] == "restored"
        assert other.state["validationSuites"][0]["id"] == identity
        assert other.state["devices"][0]["value"] == original["value"]
        assert not other.state["devices"][0]["connected"] and not other.suites.active
        other.reset()
        assert other.state["validationSuites"] and not other.state["suiteRuns"]
    finally:
        restarted.extensions["lab"].close()


def test_roles_for_suite_commands():
    from Hardware_Tester_App.auth import required_role

    assert required_role("/api/lab/validation-suites", "POST") == "admin"
    assert required_role("/api/lab/validation-suites/id/run", "POST") == "operator"
    assert required_role("/api/lab/suite-runs/cancel", "POST") == "operator"
    assert required_role("/api/lab", "GET") == "viewer"


def test_updates_snapshots_and_limits(app):
    identity = create(app)
    client = app.test_client()
    suite = copy.deepcopy(app.extensions["lab"].state["validationSuites"][0])
    suite["name"] = "Edited suite"
    assert (
        client.put(f"/api/lab/validation-suites/{identity}", json=suite).status_code
        == 200
    )
    assert (
        client.put(f"/api/lab/validation-suites/{identity}", json=suite).status_code
        == 409
    )
    lab, device, report = start(app, identity)
    finish(lab)
    assert report["suite"]["version"] == 2
    suite["version"] = 2
    suite["name"] = "Changed after validation"
    assert (
        client.put(f"/api/lab/validation-suites/{identity}", json=suite).status_code
        == 200
    )
    assert report["suite"]["name"] == "Edited suite"
    excessive = [
        dict(name="x", scenarioId="preset-healthy", expected=["passed"] * 3)
    ] * 7
    with pytest.raises(LabError, match="at most 20"):
        normalize(dict(name="Too long", kind="relay", planId="smoke", cases=excessive))


def test_short_bad_reading_sequence_exposes_unexpected_pass(app):
    identity = create(
        app,
        [dict(name="Too brief", scenarioId="preset-bad-reading", expected=["failed"])],
    )
    lab, device, report = start(app, identity)
    finish(lab)
    assert report["status"] == "failed"
    assert report["cases"][0]["attempts"][0]["run"]["status"] == "passed"
