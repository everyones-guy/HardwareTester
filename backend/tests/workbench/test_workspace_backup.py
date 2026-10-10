import copy
import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.workspace_backup import validate_archive, remap


@pytest.fixture
def app(tmp_path):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "backup.sqlite3"),
            "LAB_WORKER": False,
            "LAB_STEP_SECONDS": 0,
        },
    )
    yield app
    app.extensions["lab"].close()


def archive(app):
    response = app.test_client().get("/api/lab/workspace/backup")
    assert response.status_code == 200, response.json
    return response.json


def preview(client, data, policy="copy", history=True):
    payload = dict(archive=data, policy=policy, includeHistory=history)
    response = client.post("/api/lab/workspace/preview", json=payload)
    assert response.status_code == 200, response.json
    return (
        dict(
            payload, **{k: response.json["preview"][k] for k in ("revision", "digest")}
        ),
        response.json["preview"],
    )


def seed(app):
    client, lab = app.test_client(), app.extensions["lab"]
    plan = client.post(
        "/api/lab/test-plans",
        json=dict(
            name="Portable plan",
            kind="temperature",
            steps=[dict(name="Read", action="read")],
        ),
    ).json["planId"]
    scenario = client.post(
        "/api/lab/scenarios",
        json=dict(name="Portable scenario", frames=[dict(behavior="healthy", count=1)]),
    ).json["scenarioId"]
    suite = client.post(
        "/api/lab/validation-suites",
        json=dict(
            name="Portable suite",
            kind="temperature",
            planId=plan,
            cases=[dict(name="Read", scenarioId=scenario, expected=["passed"])],
        ),
    ).json["suiteId"]
    d = lab.state["devices"][0]
    lab.connect(d["id"], True)
    client.post(f"/api/lab/devices/{d['id']}/scenario", json=dict(scenarioId=scenario))
    client.post(f"/api/lab/validation-suites/{suite}/run", json=dict(deviceId=d["id"]))
    for _ in range(30):
        lab.advance()
        lab.suites.tick()
        if not lab.suites.active:
            break
    assert lab.state["suiteRuns"][0]["status"] == "passed"
    return plan, scenario, suite


def test_copy_import_remaps_definitions_and_preserves_archived_measurements(app):
    plan, scenario, suite = seed(app)
    client, lab = app.test_client(), app.extensions["lab"]
    data = archive(app)
    original = copy.deepcopy(lab.state)
    payload, report = preview(client, data)
    assert (
        report["added"] == 6
    )  # three devices, plan, scenario, suite; history IDs deduplicated
    assert lab.state == original  # preview does not write or disconnect
    response = client.post("/api/lab/workspace/import", json=payload)
    assert response.status_code == 200, response.json
    state = response.json["state"]
    new_suite = next(s for s in state["validationSuites"] if s["id"] != suite)
    assert new_suite["planId"] != plan
    assert new_suite["cases"][0]["scenarioId"] != scenario
    assert any(p["id"] == new_suite["planId"] for p in state["testPlans"])
    copies = [
        d
        for d in state["devices"]
        if d["id"] not in {x["id"] for x in original["devices"]}
    ]
    assert len(copies) == 3 and all(not d["connected"] for d in copies)
    assert lab.state["devices"][0][
        "connected"
    ]  # additive import leaves kept transports alone
    assert state["suiteRuns"][0] == original["suiteRuns"][0]
    assert state["runs"][0]["steps"] == original["runs"][0]["steps"]


def test_keep_matches_names_and_rebinds_suite_references(app):
    plan, _, _ = seed(app)
    data = archive(app)
    source_plan = data["workspace"]["testPlans"][0]
    source_plan["id"] = "other-installation-plan"
    data["workspace"]["validationSuites"][0]["id"] = "new-suite"
    data["workspace"]["validationSuites"][0]["name"] = "Imported dependency check"
    data["workspace"]["validationSuites"][0]["planId"] = source_plan["id"]
    payload, report = preview(app.test_client(), data, "keep", False)
    assert report["added"] == 1
    response = app.test_client().post("/api/lab/workspace/import", json=payload)
    assert response.status_code == 200
    added = next(
        s for s in response.json["state"]["validationSuites"] if s["id"] == "new-suite"
    )
    assert added["planId"] == plan


def test_roundtrip_into_empty_workspace_and_restart(app, tmp_path):
    seed(app)
    data = archive(app)
    other = create_app(
        "testing", {"LAB_DB_PATH": str(tmp_path / "other.sqlite3"), "LAB_WORKER": False}
    )
    lab = other.extensions["lab"]
    for key in data["workspace"]:
        lab.state[key] = []
    lab.save()
    payload, _ = preview(other.test_client(), data, "keep")
    result = other.test_client().post("/api/lab/workspace/import", json=payload)
    assert result.status_code == 200, result.json
    assert all(not d["connected"] for d in lab.state["devices"])
    assert (
        lab.state["suiteRuns"][0]["cases"][0]["attempts"][0]["run"]["status"]
        == "passed"
    )
    lab.close()
    restarted = create_app(
        "testing", {"LAB_DB_PATH": str(tmp_path / "other.sqlite3"), "LAB_WORKER": False}
    )
    assert (
        restarted.extensions["lab"].state["validationSuites"][0]["name"]
        == "Portable suite"
    )
    restarted.extensions["lab"].close()


def test_stale_preview_and_changed_choices_do_not_apply(app):
    client, lab = app.test_client(), app.extensions["lab"]
    payload, _ = preview(client, archive(app))
    changed = dict(payload, includeHistory=False)
    assert client.post("/api/lab/workspace/import", json=changed).status_code == 409
    lab.log("Concurrent edit")
    lab.save()
    before = copy.deepcopy(lab.state)
    assert client.post("/api/lab/workspace/import", json=payload).status_code == 409
    assert lab.state == before


@pytest.mark.parametrize(
    "change",
    [
        lambda b: b.update(version=2),
        lambda b: b["workspace"]["devices"][0].update(value="invalid"),
        lambda b: b["workspace"]["devices"][0].update(connected="true"),
        lambda b: b["workspace"]["devices"].append(b["workspace"]["devices"][0]),
        lambda b: b["workspace"]["scenarios"][0]["frames"][0].update(count=999),
        lambda b: b["workspace"].update(
            runs=[dict(id="bad", status="passed", steps=[])]
        ),
        lambda b: b["workspace"].update(
            peripherals=[
                dict(
                    id="p",
                    name="Orphan",
                    type="Sensor",
                    device_id="absent",
                    properties={},
                )
            ]
        ),
    ],
)
def test_invalid_archives_are_rejected_without_mutation(app, change):
    client, lab = app.test_client(), app.extensions["lab"]
    data = archive(app)
    change(data)
    before = copy.deepcopy(lab.state)
    result = client.post(
        "/api/lab/workspace/preview",
        json=dict(archive=data, policy="copy", includeHistory=True),
    )
    assert result.status_code == 400, result.json
    assert lab.state == before


def test_active_bench_rejects_export_and_import(app):
    client, lab = app.test_client(), app.extensions["lab"]
    data = archive(app)
    d = lab.state["devices"][0]
    lab.connect(d["id"], True)
    lab.start(d["id"], "smoke")
    assert client.get("/api/lab/workspace/backup").status_code == 409
    assert (
        client.post(
            "/api/lab/workspace/preview",
            json=dict(archive=data, policy="keep", includeHistory=True),
        ).status_code
        == 409
    )


def test_secrets_are_excluded_and_accounts_are_untouched(app):
    lab = app.extensions["lab"]
    lab.state["peripherals"] = [
        dict(
            id="p",
            name="Probe",
            type="Sensor",
            device_id=lab.state["devices"][0]["id"],
            version=1,
            properties=dict(
                password="secret", nested=dict(api_key="secret", threshold=5)
            ),
        )
    ]
    lab.save()
    data = archive(app)
    properties = data["workspace"]["peripherals"][0]["properties"]
    assert properties == dict(nested=dict(threshold=5))
    assert "accounts" not in data["workspace"]
    assert validate_archive(data)["peripherals"][0]["properties"] == properties


def test_capacity_and_transaction_failure_leave_definitions_intact(app, monkeypatch):
    client, lab = app.test_client(), app.extensions["lab"]
    data = archive(app)
    lab.state["devices"] = [
        dict(lab.state["devices"][0], id=f"d-{i}", name=f"Device {i}")
        for i in range(100)
    ]
    lab.save()
    assert (
        client.post(
            "/api/lab/workspace/preview",
            json=dict(archive=data, policy="copy", includeHistory=True),
        ).status_code
        == 409
    )
    lab.state["devices"] = lab.state["devices"][:1]
    lab.save()
    payload, _ = preview(client, data)
    before = copy.deepcopy(lab.state)

    def fail():
        raise RuntimeError("Disk unavailable")

    monkeypatch.setattr(lab, "save", fail)
    with pytest.raises(RuntimeError, match="Disk unavailable"):
        client.post("/api/lab/workspace/import", json=payload)
    assert lab.state == before
    monkeypatch.undo()


def test_portable_peripherals_blueprints_diagnostics_and_history_limits(app):
    client, lab = app.test_client(), app.extensions["lab"]
    d = lab.state["devices"][0]
    lab.connect(d["id"], True)
    lab.diagnose(d["id"])
    p = client.post(
        "/api/lab/peripherals",
        json=dict(
            name="Probe",
            type="Sensor",
            device_id=d["id"],
            properties=dict(threshold=dict(min=0, max=40)),
        ),
    ).json["peripheralId"]
    bp = client.post(
        "/api/lab/blueprints/capture", json=dict(name="Portable blueprint")
    ).json["blueprintId"]
    data = archive(app)
    payload, _ = preview(client, data)
    result = client.post("/api/lab/workspace/import", json=payload)
    assert result.status_code == 200, result.json
    state = result.json["state"]
    copied_probe = next(x for x in state["peripherals"] if x["id"] != p)
    copied_device = next(
        x for x in state["devices"] if x["id"] == copied_probe["device_id"]
    )
    assert copied_device["name"].endswith("(imported)")
    assert copied_device["diagnostics"][0]["status"] == "passed"
    copied_blueprint = next(x for x in state["blueprints"] if x["id"] != bp)
    assert (
        copied_blueprint["configuration"]
        == data["workspace"]["blueprints"][0]["configuration"]
    )
    assert (
        validate_archive(archive(app))["blueprints"][-1]["name"]
        == copied_blueprint["name"]
    )
    data = archive(app)
    original_log = copy.deepcopy(lab.state["logs"][0])
    lab.state["logs"] = [dict(original_log, id=f"log-{i}") for i in range(250)]
    lab.save()
    _, report = preview(client, data, "keep")
    row = next(r for r in report["rows"] if r["collection"] == "logs")
    assert row["trimmed"] > 0


def test_large_archive_uses_dedicated_limit_and_invalid_nested_reports_reject(app):
    client = app.test_client()
    data = archive(app)
    data["workspace"]["logs"] = [
        dict(id=f"large-{i}", time=data["exportedAt"], level="info", message="x" * 7000)
        for i in range(25)
    ]
    payload, report = preview(client, data, "keep")
    assert report["added"] == 25
    assert client.post("/api/lab/workspace/import", json=payload).status_code == 200
    assert (
        client.post("/api/lab/devices", json=dict(name="x" * 140000)).status_code == 413
    )
    data = archive(app)
    data["workspace"]["suiteRuns"] = [dict(id="bad", suite={}, device={}, plan={})]
    assert (
        client.post(
            "/api/lab/workspace/preview",
            json=dict(archive=data, policy="keep", includeHistory=True),
        ).status_code
        == 400
    )

    nested = {}
    for _ in range(45):
        nested = dict(child=nested)
    data = archive(app)
    data["workspace"]["devices"][0]["extra"] = nested
    assert (
        client.post(
            "/api/lab/workspace/preview",
            json=dict(archive=data, policy="keep", includeHistory=True),
        ).status_code
        == 400
    )


def test_cross_installation_history_references_follow_kept_definitions(app):
    plan, scenario, suite = seed(app)
    lab, client = app.extensions["lab"], app.test_client()
    data = archive(app)
    maps = {
        k: {
            item["id"]: "foreign-" + item["id"]
            for item in items
            if not item["id"].startswith("preset-")
        }
        for k, items in data["workspace"].items()
    }
    data["workspace"] = {
        k: [remap(item, maps, k) for item in items]
        for k, items in data["workspace"].items()
    }
    payload, _ = preview(client, data, "keep")
    result = client.post("/api/lab/workspace/import", json=payload)
    assert result.status_code == 200, result.json
    run = next(r for r in lab.state["runs"] if r["id"].startswith("foreign-"))
    assert run["configuration"]["plan"]["id"] == plan
    assert run["deviceId"] == lab.state["devices"][0]["id"]
    report = next(r for r in lab.state["suiteRuns"] if r["id"].startswith("foreign-"))
    assert report["suite"]["id"] == suite
    assert report["cases"][0]["scenario"]["id"] == scenario
    assert report["cases"][0]["attempts"][0]["run"]["deviceId"] == run["deviceId"]


def test_importing_physical_configuration_never_opens_hardware(app, monkeypatch):
    client, lab = app.test_client(), app.extensions["lab"]
    data = archive(app)
    data["workspace"]["devices"] = [
        dict(
            data["workspace"]["devices"][0],
            id="pi-serial",
            name="Pi responder",
            adapter="serial",
            endpoint="COM6",
            connected=True,
        )
    ]

    def unexpected_open(*args):
        pytest.fail("Import must not open any transport")

    monkeypatch.setattr(lab, "transport_factory", unexpected_open)
    payload, _ = preview(client, data, "keep")
    result = client.post("/api/lab/workspace/import", json=payload)
    assert result.status_code == 200
    restored = next(d for d in lab.state["devices"] if d["id"] == "pi-serial")
    assert not restored["connected"] and restored["endpoint"] == "COM6"
    assert (
        client.post(
            "/api/lab/devices/pi-serial/connection", json=dict(connected=True)
        ).status_code
        == 403
    )
