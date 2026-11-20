"""Validated executable plans and persistent adapter for the original plan service."""

import copy
import hashlib
import json
import math
import re
import uuid
from pathlib import PurePosixPath
from flask import jsonify, request, g, has_request_context
from .lab import LabError, now
from .utils.validators import validate_json

UI_ACTIONS = ("ui_navigate", "ui_input", "ui_confirm")
UI_WIDGET_ID = re.compile(r"page:[0-9]{1,16}/widget:[0-9]{1,16}/config:[0-9]{1,16}")


def number(value, label, minimum=-1e9, maximum=1e9):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not minimum <= value <= maximum
        or not math.isfinite(value)
    ):
        raise LabError(
            f"{label} must be a finite number between {minimum} and {maximum}."
        )
    return value


def ui_plan_steps_digest(plan):
    steps = [
        {
            key: (
                int(value) if isinstance(value, float) and value.is_integer() else value
            )
            for key, value in step.items()
        }
        for step in plan["steps"]
    ]
    encoded = json.dumps(
        {"kind": plan["kind"], "steps": steps},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def normalize_ui_source(origin, plan):
    fields = {
        "catalogSha256",
        "controlId",
        "handler",
        "bindingReference",
        "source",
        "stepsSha256",
    }
    if not isinstance(origin, dict) or origin.keys() != fields:
        raise LabError("Invalid UI source provenance.")
    limits = {"controlId": 220, "handler": 100, "bindingReference": 240}
    for field, limit in limits.items():
        value = origin[field]
        if (
            not isinstance(value, str)
            or not 1 <= len(value) <= limit
            or not value.isprintable()
        ):
            raise LabError("Invalid UI source provenance.")
    if not isinstance(origin["catalogSha256"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", origin["catalogSha256"]
    ):
        raise LabError("UI source provenance needs a SHA-256 catalog digest.")
    if origin["stepsSha256"] != ui_plan_steps_digest(plan):
        raise LabError("The plan steps differ from the recorded UI source plan.")
    normalize_source_location(origin["source"], "WidgetsInstalled")
    return copy.deepcopy(origin)


def normalize_source_location(source, table):
    if not isinstance(source, dict) or source.keys() != {"path", "line", "table"}:
        raise LabError("Invalid UI source location.")
    path = source["path"]
    if (
        not isinstance(path, str)
        or not 1 <= len(path) <= 180
        or not path.isprintable()
        or any(char in path for char in "\\:")
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or not path.lower().endswith(".sql")
        or type(source["line"]) is not int
        or not 1 <= source["line"] <= 524288
        or source["table"] != table
    ):
        raise LabError("Invalid UI source location.")
    return source.copy()


def normalize_ui_step(data, action):
    fields = {"controlId", "source"}
    if action == "ui_navigate":
        fields |= {"pageId", "pageSource"}
    if not isinstance(data, dict) or data.keys() != fields:
        raise LabError("Invalid source action metadata.")
    if not isinstance(data["controlId"], str) or not UI_WIDGET_ID.fullmatch(
        data["controlId"]
    ):
        raise LabError("A source action needs an exact widget configuration ID.")
    step = {
        "controlId": data["controlId"],
        "source": normalize_source_location(data["source"], "WidgetsInstalled"),
    }
    if action == "ui_navigate":
        if not isinstance(data["pageId"], str) or not re.fullmatch(
            r"page:[0-9]{1,16}", data["pageId"]
        ):
            raise LabError("Navigation needs a source page ID.")
        step.update(
            pageId=data["pageId"],
            pageSource=normalize_source_location(data["pageSource"], "PagesInstalled"),
        )
    return step


def validate_ui_sequence(plan):
    steps = plan["steps"]
    if [step["action"] for step in steps] != [
        "read",
        *UI_ACTIONS,
        "assert_equal",
    ] or "uiSource" not in plan:
        raise LabError(
            "A source workflow requires navigation, input, confirmation and readback in order with source provenance."
        )
    navigation, draft, confirmation = (step["uiAction"] for step in steps[1:4])
    origin = plan["uiSource"]
    page_id = navigation["pageId"]
    if (
        draft["controlId"] != origin["controlId"]
        or draft["source"] != origin["source"]
        or draft["controlId"] == confirmation["controlId"]
        or navigation["controlId"].split("/", 1)[0] == page_id
        or any(
            node["controlId"].split("/", 1)[0] != page_id
            for node in (draft, confirmation)
        )
    ):
        raise LabError(
            "Source actions do not match the declared page and numeric control."
        )


def normalize_plan(data):
    ok, message = validate_json(data, ["name", "kind", "steps"])
    if not ok:
        raise LabError(message)
    if not isinstance(data["name"], str) or not 1 <= len(data["name"].strip()) <= 100:
        raise LabError("Plan name must contain 1–100 characters.")
    if data["kind"] not in ("temperature", "valve", "relay"):
        raise LabError("Choose a temperature, valve, or relay plan profile.")
    description = data.get("description", "")
    if not isinstance(description, str) or len(description) > 2000:
        raise LabError("Description must be text up to 2000 characters.")
    if not isinstance(data["steps"], list) or not 1 <= len(data["steps"]) <= 30:
        raise LabError("A plan requires 1–30 steps.")
    steps = []
    for item in data["steps"]:
        if not isinstance(item, dict):
            raise LabError("Every step must be a JSON object.")
        action = item.get("action")
        if action not in (
            "read",
            "set",
            "assert_range",
            "assert_equal",
            "wait",
            *UI_ACTIONS,
        ):
            raise LabError(
                "Supported actions: read, set, assert_range, assert_equal, wait."
            )
        label = item.get("name", action.replace("_", " ").title())
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
            raise LabError("Step name must contain 1–100 characters.")
        step = {"name": label.strip(), "action": action}
        if action in UI_ACTIONS:
            step["uiAction"] = normalize_ui_step(item.get("uiAction"), action)
        if action == "wait":
            step["seconds"] = number(item.get("seconds"), "Wait duration", 0, 30)
        elif action not in ("ui_navigate", "ui_input"):
            step["timeout"] = number(
                item.get("timeout", 2), "Response timeout", 0.1, 10
            )
        if action in ("set", "assert_equal", "ui_input"):
            step["value"] = number(item.get("value"), "Value")
            if (
                action in ("set", "ui_input")
                and not 0
                <= step["value"]
                <= {"temperature": 50, "valve": 100, "relay": 1}[data["kind"]]
            ):
                raise LabError(
                    "Set value is outside the device profile command limits."
                )
            if (
                action in ("set", "ui_input")
                and data["kind"] == "relay"
                and step["value"] not in (0, 1)
            ):
                raise LabError("Relay set commands must be 0 or 1.")
            if action == "assert_equal":
                step["tolerance"] = number(
                    item.get("tolerance", 0), "Tolerance", 0, 1e6
                )
        if action == "assert_range":
            step["min"] = number(item.get("min"), "Minimum")
            step["max"] = number(item.get("max"), "Maximum")
            if step["min"] > step["max"]:
                raise LabError("Range minimum cannot exceed maximum.")
        steps.append(step)
    plan = {
        "name": data["name"].strip(),
        "kind": data["kind"],
        "description": description,
        "steps": steps,
    }
    if "uiSource" in data:
        plan["uiSource"] = normalize_ui_source(data["uiSource"], plan)
    if any(step["action"] in UI_ACTIONS for step in steps):
        validate_ui_sequence(plan)
    return plan


class PlanRepository:
    def __init__(self, lab):
        self.lab = lab
        lab.state.setdefault("testPlans", [])

    def editable(self):
        if self.lab.active:
            raise LabError("Stop the active test before editing plans.", 409)

    def find(self, identity):
        plan = next(
            (p for p in self.lab.state["testPlans"] if p["id"] == identity), None
        )
        if plan is None:
            raise LabError("Test plan not found.", 404)
        return plan

    def list_test_plans(self, search=None, page=1, per_page=10):
        plans = [
            p
            for p in self.lab.state["testPlans"]
            if not search or search.lower() in p["name"].lower()
        ]
        return {"success": True, "testPlans": copy.deepcopy(plans), "total": len(plans)}

    def create_test_plan(self, data, created_by=None):
        self.editable()
        if len(self.lab.state["testPlans"]) >= 100:
            raise LabError("The library supports 100 test plans.", 409)
        plan = normalize_plan(data)
        plan.update(id=str(uuid.uuid4()), version=1, updatedAt=now())
        self.lab.state["testPlans"].append(plan)
        self.lab.log(f"Created test plan {plan['name']}.")
        self.lab.save()
        return {"success": True, "planId": plan["id"]}

    def preview_test_plan(self, identity):
        return {"success": True, "plan": copy.deepcopy(self.find(identity))}

    def run_test_plan(self, identity, device_id, release_sha256=None):
        return {
            "success": True,
            "runId": self.lab.start(
                device_id,
                identity,
                actor=(
                    getattr(g, "workbench_user", None)
                    if has_request_context()
                    else None
                ),
                release_sha256=release_sha256,
            ),
        }

    def update(self, identity, data):
        self.editable()
        previous = self.find(identity)
        if data.get("version") != previous["version"]:
            raise LabError("This plan changed. Reload it before saving.", 409)
        normalized = normalize_plan(data)
        if "uiSource" not in normalized and "uiSource" in previous:
            if previous["uiSource"]["stepsSha256"] != ui_plan_steps_digest(normalized):
                previous.pop("uiSource")
        previous.update(normalized, version=previous["version"] + 1, updatedAt=now())
        self.lab.log(f"Updated test plan {previous['name']}.")
        self.lab.save()

    def delete(self, identity, version):
        self.editable()
        plan = self.find(identity)
        if version != plan["version"]:
            raise LabError("This plan changed. Reload it before deleting.", 409)
        self.lab.state["testPlans"].remove(plan)
        self.lab.log(f"Deleted test plan {plan['name']}.")
        self.lab.save()


def register_plans(app, lab):
    from .services.test_plan_service import TestPlanService

    repository = PlanRepository(lab)
    app.extensions["plan_repository"] = repository

    @app.route("/api/lab/test-plans", methods=["GET", "POST"])
    @app.route("/api/lab/test-plans/<identity>", methods=["GET", "PUT", "DELETE"])
    @app.route("/api/lab/test-plans/<identity>/run", methods=["POST"])
    def plans(identity=None):
        with lab.lock:
            data = {} if request.method == "GET" else request.get_json()
            if not isinstance(data, dict):
                raise LabError("Request body must be a JSON object.")
            extra = {}
            if request.path.endswith("/run"):
                extra = TestPlanService.run_test_plan(
                    identity,
                    device_id=data.get("deviceId"),
                    repository=repository,
                    release_sha256=data.get("releaseSha256"),
                )
            elif request.method == "GET":
                extra = (
                    TestPlanService.preview_test_plan(identity, repository=repository)
                    if identity
                    else TestPlanService.list_test_plans(repository=repository)
                )
            elif request.method == "POST":
                extra = TestPlanService.create_test_plan(
                    data, None, repository=repository
                )
            elif request.method == "PUT":
                repository.update(identity, data)
            else:
                repository.delete(identity, data.get("version"))
            return jsonify(state=lab.snapshot(), **extra)
