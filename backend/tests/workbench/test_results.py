import copy
import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.workspace_backup import validate_archive
from Hardware_Tester_App.lab import LabError


@pytest.fixture
def app(tmp_path):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "results.sqlite3"),
            "LAB_WORKER": False,
            "LAB_STEP_SECONDS": 0,
        },
    )
    yield app
    app.extensions["lab"].close()


def completed(app, plan="smoke", fault="none"):
    lab = app.extensions["lab"]
    device = lab.state["devices"][0]
    lab.connect(device["id"], True)
    lab.fault(device["id"], fault)
    identity = lab.start(device["id"], plan)
    while lab.active:
        lab.advance()
    return next(r for r in lab.state["runs"] if r["id"] == identity)


def mark(client, run, enabled=True, **kwargs):
    return client.post(
        f'/api/lab/runs/{run["id"]}/baseline', json={"enabled": enabled}, **kwargs
    )


def test_baseline_replacement_preserves_measurements_and_other_plan(app):
    client = app.test_client()
    first = completed(app)
    control = completed(app, "control")
    newest = completed(app)
    before = copy.deepcopy(first)
    assert mark(client, first).status_code == 200
    assert mark(client, control).status_code == 200
    assert mark(client, newest).status_code == 200
    assert "baseline" not in first and newest["baseline"] and control["baseline"]
    assert first == before
    assert mark(client, newest, False).status_code == 200
    assert "baseline" not in newest and control["baseline"]


def test_baseline_rejects_bad_missing_failed_and_running_runs(app):
    client = app.test_client()
    failed = completed(app, fault="timeout")
    assert mark(client, failed).status_code == 409
    assert mark(client, failed, "true").status_code == 400
    assert mark(client, {"id": "missing"}).status_code == 404
    good = completed(app)
    good["restoration"] = "failed"
    assert mark(client, good).status_code == 409
    lab = app.extensions["lab"]
    lab.start(good["deviceId"], "smoke")
    assert mark(client, good, False).status_code == 409


def test_baseline_survives_restart_and_archive_import(app, tmp_path):
    client = app.test_client()
    run = completed(app)
    assert mark(client, run).status_code == 200
    archive = client.get("/api/lab/workspace/backup").json
    # Import a second marked run for the same series: existing baseline wins.
    imported = copy.deepcopy(archive)
    imported["workspace"]["runs"][0]["id"] = "imported-run"
    payload = dict(archive=imported, policy="keep", includeHistory=True)
    preview = client.post("/api/lab/workspace/preview", json=payload).json["preview"]
    payload.update({k: preview[k] for k in ("revision", "digest")})
    result = client.post("/api/lab/workspace/import", json=payload)
    assert result.status_code == 200
    assert [r["id"] for r in result.json["state"]["runs"] if r.get("baseline")] == [
        run["id"]
    ]
    other = create_app(
        "testing",
        {"LAB_DB_PATH": str(tmp_path / "restored.sqlite3"), "LAB_WORKER": False},
    )
    try:
        target = other.test_client()
        payload = dict(archive=archive, policy="copy", includeHistory=True)
        preview = target.post("/api/lab/workspace/preview", json=payload).json[
            "preview"
        ]
        payload.update({k: preview[k] for k in ("revision", "digest")})
        assert target.post("/api/lab/workspace/import", json=payload).status_code == 200
    finally:
        other.extensions["lab"].close()
    restarted = create_app(
        "testing",
        {"LAB_DB_PATH": str(tmp_path / "restored.sqlite3"), "LAB_WORKER": False},
    )
    try:
        restored = restarted.extensions["lab"].state["runs"][0]
        assert restored["baseline"] and restored["steps"] == run["steps"]
    finally:
        restarted.extensions["lab"].close()
    archive["workspace"]["runs"][0]["baseline"] = "true"
    with pytest.raises(LabError, match="baseline"):
        validate_archive(archive)


@pytest.mark.parametrize("role,status", [("viewer", 403), ("operator", 200)])
def test_baseline_requires_operator_access_and_csrf(app, role, status):
    app.config["LAB_AUTH_ENABLED"] = True
    client = app.test_client()
    password = "Release-test-passphrase-123"
    csrf = client.post(
        "/api/auth/setup",
        json=dict(username="admin", email="admin@example.com", password=password),
    ).json["csrf"]
    client.post(
        "/api/auth/users",
        json=dict(
            username=role, email=role + "@example.com", password=password, role=role
        ),
        headers={"X-CSRF-Token": csrf},
    )
    run = completed(app)
    login = client.post(
        "/api/auth/login", json=dict(username=role, password=password)
    ).json
    assert mark(client, run).status_code == 403
    assert (
        mark(client, run, headers={"X-CSRF-Token": login["csrf"]}).status_code == status
    )
