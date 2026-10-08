from Hardware_Tester_App import create_app


def test_report_measurements_timing_restoration_and_event_links(tmp_path):
    app = create_app(
        "testing",
        {"LAB_DB_PATH": str(tmp_path / "report.sqlite3"), "LAB_WORKER": False},
    )
    lab = app.extensions["lab"]
    device = lab.state["devices"][1]
    lab.connect(device["id"], True)
    lab.command(device["id"], 20)
    lab.start(device["id"], "control")
    while lab.active:
        lab.advance()
    run = lab.state["runs"][0]
    verify = next(s for s in run["steps"] if s["name"] == "Verify response")
    assert verify["expected"] == {"value": 75, "tolerance": 0}
    assert verify["observed"] == 75
    assert all(
        s["durationMs"] >= 0 and s["startedAt"] and s["finishedAt"]
        for s in run["steps"]
    )
    assert run["restoration"] == "restored"
    assert device["value"] == 20
    events = [l for l in lab.state["logs"] if l.get("runId") == run["id"]]
    assert len(events) == 6
    assert all(l["deviceId"] == device["id"] for l in events)
    lab.close()


def test_wait_timing_and_failed_custom_assertion_keep_actual_and_expected(
    tmp_path, monkeypatch
):
    app = create_app(
        "testing",
        {"LAB_DB_PATH": str(tmp_path / "custom.sqlite3"), "LAB_WORKER": False},
    )
    lab = app.extensions["lab"]
    clock = [100.0]
    monkeypatch.setattr("Hardware_Tester_App.lab.time.monotonic", lambda: clock[0])
    response = app.test_client().post(
        "/api/lab/test-plans",
        json={
            "name": "Wait and compare",
            "kind": "valve",
            "steps": [
                {"action": "wait", "seconds": 0.2},
                {"action": "assert_equal", "value": 50, "tolerance": 1},
            ],
        },
    )
    device = lab.state["devices"][1]
    lab.connect(device["id"], True)
    lab.start(device["id"], response.json["planId"])
    lab.advance()
    lab.advance()
    clock[0] += 0.3
    lab.advance()
    lab.advance()
    run = lab.state["runs"][0]
    assert run["steps"][1]["durationMs"] == 300
    assert run["steps"][2]["expected"] == {"value": 50, "tolerance": 1}
    assert run["steps"][2]["observed"] == 0
    assert run["steps"][2]["status"] == "failed"
    assert run["restoration"] == "not-needed"
    lab.close()
