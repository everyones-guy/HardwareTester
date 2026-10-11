"""Baseline annotations on retained run history; measurements stay immutable."""

from flask import jsonify, request
from .lab import LabError


def series(run):
    plan = (run.get("configuration") or {}).get("plan", {}).get("id") or run.get("planId")
    if not plan:
        plan = {"Connection & health": "smoke", "Control response": "control"}.get(
            run["plan"], run["plan"]
        )
    return run["deviceId"], plan


def eligible(run):
    return (
        run["status"] == "passed"
        and bool(run.get("finishedAt"))
        and run.get("restoration") != "failed"
    )


def register_results(app, lab):
    @app.post("/api/lab/runs/<identity>/baseline")
    def baseline(identity):
        data = request.get_json()
        if not isinstance(data, dict) or type(data.get("enabled")) is not bool:
            raise LabError("Choose whether to enable the baseline.")
        if lab.active:
            raise LabError("Stop the active test before changing a baseline.", 409)
        run = next((r for r in lab.state["runs"] if r["id"] == identity), None)
        if run is None:
            raise LabError("Run no longer exists in retained history.", 404)
        if data["enabled"] and not eligible(run):
            raise LabError(
                "A baseline requires a completed passing run with no restoration failure.",
                409,
            )
        if data["enabled"]:
            for other in lab.state["runs"]:
                if series(other) == series(run):
                    other.pop("baseline", None)
            run["baseline"] = True
        else:
            run.pop("baseline", None)
        lab.log(
            f'{"Marked" if data["enabled"] else "Cleared"} baseline for {run["deviceName"]}: {run["plan"]}.',
            device_id=run["deviceId"], run_id=run["id"],
        )
        lab.save()
        return jsonify(state=lab.snapshot())
