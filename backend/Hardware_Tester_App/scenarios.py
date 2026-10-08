"""Reusable, deterministic response sequences for simulation transports only."""

import copy
import math
import uuid
from flask import jsonify, request
from .lab import LabError


def presets():
    definitions = [
        (
            "healthy",
            "Healthy device",
            "Every request responds normally.",
            [{"behavior": "healthy", "count": 1}],
        ),
        (
            "intermittent",
            "Intermittent timeout",
            "Two responses, a timeout, two responses, another timeout, then recovery.",
            [
                {"behavior": "healthy", "count": 2},
                {"behavior": "timeout", "count": 1},
                {"behavior": "healthy", "count": 2},
                {"behavior": "timeout", "count": 1},
                {"behavior": "healthy", "count": 1},
            ],
        ),
        (
            "delayed",
            "Delayed responses",
            "Ten responses delayed by 200 ms, then normal responses.",
            [
                {"behavior": "delay", "count": 10, "delayMs": 200},
                {"behavior": "healthy", "count": 1},
            ],
        ),
        (
            "bad-reading",
            "Bad telemetry",
            "Two readings outside the device profile range, then healthy readings.",
            [
                {"behavior": "out-of-range", "count": 2},
                {"behavior": "healthy", "count": 1},
            ],
        ),
        (
            "recovery",
            "Timeout and recovery",
            "Two timeouts followed by normal responses.",
            [{"behavior": "timeout", "count": 2}, {"behavior": "healthy", "count": 1}],
        ),
    ]
    return [
        {
            "id": f"preset-{key}",
            "name": name,
            "description": description,
            "frames": frames,
            "version": 1,
            "builtin": True,
        }
        for key, name, description, frames in definitions
    ]


def normalize(data):
    if not isinstance(data, dict):
        raise LabError("A scenario must be a JSON object.")
    name, description, frames = (
        data.get("name"),
        data.get("description", ""),
        data.get("frames"),
    )
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise LabError("Scenario name must contain 1–100 characters.")
    if not isinstance(description, str) or len(description) > 2000:
        raise LabError("Description must be text up to 2000 characters.")
    if not isinstance(frames, list) or not 1 <= len(frames) <= 20:
        raise LabError("A scenario requires 1–20 response stages.")
    result = []
    for frame in frames:
        if not isinstance(frame, dict) or frame.get("behavior") not in (
            "healthy",
            "timeout",
            "out-of-range",
            "delay",
        ):
            raise LabError("Choose healthy, timeout, out-of-range, or delay responses.")
        count = frame.get("count")
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or not 1 <= count <= 100
        ):
            raise LabError("Each stage requires 1–100 read attempts.")
        normalized = {"behavior": frame["behavior"], "count": count}
        if frame["behavior"] == "delay":
            delay = frame.get("delayMs")
            if (
                isinstance(delay, bool)
                or not isinstance(delay, (int, float))
                or not math.isfinite(delay)
                or not 0 <= delay <= 2000
            ):
                raise LabError("Response delay must be 0–2000 milliseconds.")
            normalized["delayMs"] = delay
        result.append(normalized)
    if sum(f["count"] for f in result) > 200:
        raise LabError("A scenario supports at most 200 staged read attempts.")
    return {"name": name.strip(), "description": description, "frames": result}


def register_scenarios(app, lab):
    lab.state.setdefault("scenarios", presets())
    lab.save()

    def find(identity):
        item = next((s for s in lab.state["scenarios"] if s["id"] == identity), None)
        if item is None:
            raise LabError("Scenario not found.", 404)
        return item

    def editable():
        if lab.active:
            raise LabError("Stop the active test before changing scenarios.", 409)

    @app.post("/api/lab/scenarios")
    def create_scenario():
        with lab.lock:
            editable()
            if len(lab.state["scenarios"]) >= 100:
                raise LabError("The library supports 100 scenarios.", 409)
            item = dict(
                normalize(request.get_json()),
                id=str(uuid.uuid4()),
                version=1,
                builtin=False,
            )
            lab.state["scenarios"].append(item)
            lab.log(f"Saved emulator scenario {item['name']}.")
            lab.save()
            return jsonify(state=lab.snapshot(), scenarioId=item["id"])

    @app.route("/api/lab/scenarios/<identity>", methods=["PUT", "DELETE"])
    def change_scenario(identity):
        with lab.lock:
            editable()
            item = find(identity)
            data = request.get_json()
            if not isinstance(data, dict):
                raise LabError("Use a JSON object.")
            if item["builtin"]:
                raise LabError("Duplicate a preset to customize it.", 409)
            if (
                type(data.get("version")) is not int
                or data["version"] != item["version"]
            ):
                raise LabError("Scenario changed. Reload before saving.", 409)
            if request.method == "DELETE":
                lab.state["scenarios"].remove(item)
            else:
                item.update(normalize(data), version=item["version"] + 1)
            lab.log(
                f"Emulator scenario {item['name']} {'deleted' if request.method == 'DELETE' else 'updated'}."
            )
            lab.save()
            return jsonify(state=lab.snapshot())

    @app.post("/api/lab/devices/<identity>/scenario")
    def apply_scenario(identity):
        with lab.lock:
            editable()
            device = lab.device(identity)
            if device["adapter"] != "simulation":
                raise LabError(
                    "Scenarios are only available for simulated devices.", 403
                )
            data = request.get_json()
            if not isinstance(data, dict) or (
                "scenarioId" not in data and data.get("restart") is not True
            ):
                raise LabError("Provide scenarioId, null to clear, or restart: true.")
            if data.get("restart") is True:
                source = device.get("scenario")
                if not source:
                    raise LabError("No applied scenario to restart.", 409)
            else:
                source = (
                    find(data["scenarioId"]) if data["scenarioId"] is not None else None
                )
            output = device.get("scenarioOutput", device["value"])
            maximum = {"temperature": 50, "valve": 100, "relay": 1}[device["kind"]]
            if not 0 <= output <= maximum:
                output = 24 if device["kind"] == "temperature" else 0
            device.update(
                scenario=copy.deepcopy(source),
                scenarioCursor=0,
                scenarioOutput=output,
                value=output,
                fault="none",
                lastError=None,
            )
            if source is None:
                device.pop("scenarioOutput", None)
            lab.log(
                f"{device['name']}: scenario {source['name'] + ' restarted at response 1' if source else 'cleared'}.",
                device_id=device["id"],
            )
            lab.save()
            return jsonify(state=lab.snapshot())
