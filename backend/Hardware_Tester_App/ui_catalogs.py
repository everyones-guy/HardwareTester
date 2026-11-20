"""Read-only UISee discovery with reviewed bindings to existing lab plans."""

import json
import re
from fractions import Fraction

from flask import g, jsonify, request

from .lab import LabError, now
from .pi_inventories import text_value
from .test_plans import normalize_plan, number, ui_plan_steps_digest
from .ui_discovery import UiDiscoveryError, discover_ui

UI_CATALOG_API = "/api/lab/ui-catalogs"
UI_CATALOG_REQUEST_LIMIT = 2 * 1024 * 1024
MAX_CATALOGS = 25
HANDLER_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*")


def body(*fields):
    data = request.get_json()
    if not isinstance(data, dict) or set(data) != set(fields):
        raise LabError("This request has missing or unsupported fields.")
    return data


def control_for(entry, identity):
    control = next(
        (item for item in entry["catalog"]["controls"] if item["id"] == identity), None
    )
    if not control:
        raise LabError("UI control not found.", 404)
    if control.get("input", None) is None:
        raise LabError("This control needs source-declared numeric input limits.")
    return control


def source_actions(entry, control):
    if control.get("workflowError"):
        raise LabError(control["workflowError"])
    workflow = control.get("workflow")
    if workflow is None:
        return None, None
    controls = {item["id"]: item for item in entry["catalog"]["controls"]}
    return controls[workflow["navigationId"]], controls[workflow["confirmationId"]]


def source_action(control):
    return {"controlId": control["id"], "source": control["source"]}


def make_plan(entry, data):
    control = control_for(entry, data["controlId"])
    binding = entry["bindings"].get(control["id"])
    if binding is None:
        raise LabError("Review and save a handler binding before building a plan.", 409)
    limits = control["input"]
    if limits["kind"] != "number":
        raise LabError("Only source-declared numeric input is supported.")
    command = number(data["value"], "Input value", limits["min"], limits["max"])
    offset = Fraction(str(command)) - Fraction(str(limits["min"]))
    if (offset / Fraction(str(limits["step"]))).denominator != 1:
        raise LabError("The input value must align with the source-declared step size.")
    expected = number(data["expected"], "Expected device reading")
    tolerance = number(data["tolerance"], "Tolerance", 0, 1e6)
    timeout = number(data["timeout"], "Response timeout", 0.1, 10)
    navigation, confirmation = source_actions(entry, control)
    command_steps = [
        {
            "name": "Apply bound input",
            "action": "set",
            "value": command,
            "timeout": timeout,
        }
    ]
    if navigation:
        if confirmation["handler"] and binding["handler"] != confirmation["handler"]:
            raise LabError(
                "Review the handler declared by the confirmation button before building a plan.",
                409,
            )
        page = next(
            item
            for item in entry["catalog"]["pages"]
            if item["pageId"] == control["pageId"]
        )
        command_steps = [
            {
                "name": navigation["name"][:100].strip(),
                "action": "ui_navigate",
                "uiAction": {
                    **source_action(navigation),
                    "pageId": page["id"],
                    "pageSource": page["source"],
                },
            },
            {
                "name": f"Enter {control['name']}"[:100].strip(),
                "action": "ui_input",
                "value": command,
                "uiAction": source_action(control),
            },
            {
                "name": confirmation["name"][:100].strip(),
                "action": "ui_confirm",
                "timeout": timeout,
                "uiAction": source_action(confirmation),
            },
        ]
    plan = {
        "name": data["name"],
        "kind": binding["kind"],
        "description": f"Built from the UISee control {control['name']}.",
        "steps": [
            {
                "name": "Read output before command",
                "action": "read",
                "timeout": timeout,
            },
            *command_steps,
            {
                "name": "Check device readback",
                "action": "assert_equal",
                "value": expected,
                "tolerance": tolerance,
                "timeout": timeout,
            },
        ],
    }
    plan["uiSource"] = {
        "catalogSha256": entry["id"],
        "controlId": control["id"],
        "handler": binding["handler"],
        "bindingReference": binding["reference"],
        "source": control["source"],
        "stepsSha256": ui_plan_steps_digest(plan),
    }
    return normalize_plan(plan)


def compare_catalogs(before, after):
    result = {}
    for collection, fields in (
        ("pages", ("name", "attributes")),
        (
            "controls",
            (
                "name",
                "buttonType",
                "widgetIndex",
                "handler",
                "input",
                "attributes",
                "workflow",
                "workflowError",
            ),
        ),
    ):
        left = {item["id"]: item for item in before[collection]}
        right = {item["id"]: item for item in after[collection]}
        added = [right[key] for key in sorted(right.keys() - left.keys())]
        removed = [left[key] for key in sorted(left.keys() - right.keys())]
        changed = []
        for key in sorted(left.keys() & right.keys()):
            differences = [
                field
                for field in fields
                if left[key].get(field) != right[key].get(field)
            ]
            if differences:
                changed.append(
                    {
                        "id": key,
                        "before": left[key]["name"],
                        "after": right[key]["name"],
                        "fields": differences,
                    }
                )
        removed_names = {item["name"].casefold() for item in removed if item["name"]}
        review = sorted(
            {
                item["name"]
                for item in added
                if item["name"] and item["name"].casefold() in removed_names
            }
        )
        result[collection] = {
            "added": [{"id": item["id"], "name": item["name"]} for item in added],
            "removed": [{"id": item["id"], "name": item["name"]} for item in removed],
            "changed": changed,
            "reviewNames": review,
        }
    return result


def register_ui_catalogs(app, lab):
    with lab.lock, lab.connection:
        lab.connection.execute(
            "CREATE TABLE IF NOT EXISTS ui_catalogs (id TEXT PRIMARY KEY, entry TEXT NOT NULL)"
        )

    def get_entry(identity):
        with lab.lock:
            row = lab.connection.execute(
                "SELECT entry FROM ui_catalogs WHERE id = ?", (identity,)
            ).fetchone()
        if row is None:
            raise LabError("UI catalog not found.", 404)
        return json.loads(row[0])

    @app.get(UI_CATALOG_API)
    def list_ui_catalogs():
        with lab.lock:
            rows = lab.connection.execute(
                "SELECT entry FROM ui_catalogs ORDER BY rowid DESC"
            ).fetchall()
        entries = (json.loads(encoded) for (encoded,) in rows)
        return jsonify(
            catalogs=[
                {
                    "id": entry["id"],
                    "name": entry["name"],
                    "createdAt": entry["createdAt"],
                    "pageCount": len(entry["catalog"]["pages"]),
                    "controlCount": len(entry["catalog"]["controls"]),
                }
                for entry in entries
            ]
        )

    @app.post(UI_CATALOG_API)
    def import_ui_catalog():
        data = body("name", "files")
        name = text_value(data["name"], "Catalog name", 100)
        try:
            catalog = discover_ui(data["files"])
        except UiDiscoveryError as exc:
            raise LabError(str(exc)) from exc
        if not catalog["pages"] and not catalog["controls"]:
            raise LabError("The files contain no recognized UISee pages or controls.")
        identity = catalog["catalogSha256"]
        entry = {
            "id": identity,
            "name": name,
            "createdAt": now(),
            "catalog": catalog,
            "bindings": {},
        }
        with lab.connection:
            existing = lab.connection.execute(
                "SELECT 1 FROM ui_catalogs WHERE id = ?", (identity,)
            ).fetchone()
            if existing:
                existing_entry = get_entry(identity)
                if existing_entry["catalog"] != catalog:
                    existing_entry["catalog"] = catalog
                    lab.connection.execute(
                        "UPDATE ui_catalogs SET entry = ? WHERE id = ?",
                        (json.dumps(existing_entry, allow_nan=False), identity),
                    )
                return jsonify(catalog=existing_entry)
            count = lab.connection.execute(
                "SELECT COUNT(*) FROM ui_catalogs"
            ).fetchone()[0]
            if count >= MAX_CATALOGS:
                raise LabError(f"The library supports {MAX_CATALOGS} UI catalogs.", 409)
            lab.connection.execute(
                "INSERT INTO ui_catalogs VALUES (?, ?)",
                (identity, json.dumps(entry, allow_nan=False)),
            )
        return jsonify(catalog=entry), 201

    @app.get(UI_CATALOG_API + "/<identity>")
    def get_ui_catalog(identity):
        return jsonify(catalog=get_entry(identity))

    @app.get(UI_CATALOG_API + "/<identity>/compare")
    def diff_ui_catalog(identity):
        current = get_entry(identity)
        baseline = get_entry(request.args.get("baseline"))
        return jsonify(
            comparison=compare_catalogs(baseline["catalog"], current["catalog"])
        )

    @app.post(UI_CATALOG_API + "/<identity>/bindings")
    def bind_ui_control(identity):
        data = body("controlId", "handler", "kind", "reference")
        entry = get_entry(identity)
        control = control_for(entry, data["controlId"])
        _, confirmation = source_actions(entry, control)
        declared_handler = control["handler"] or (
            confirmation and confirmation["handler"]
        )
        handler = text_value(data["handler"], "Handler", 100)
        if not HANDLER_NAME.fullmatch(handler):
            raise LabError("Use a plain handler name or C++ qualified identifier.")
        if declared_handler and declared_handler != handler:
            raise LabError("The reviewed handler must match the source declaration.")
        if data["kind"] not in ("valve", "relay"):
            raise LabError("Choose the valve or relay output profile.")
        actor = getattr(g, "workbench_user", None)
        entry["bindings"][control["id"]] = {
            "handler": handler,
            "kind": data["kind"],
            "reference": text_value(data["reference"], "Binding reference", 240),
            "reviewedBy": actor["username"] if actor else None,
            "reviewedAt": now(),
        }
        with lab.connection:
            lab.connection.execute(
                "UPDATE ui_catalogs SET entry = ? WHERE id = ?",
                (json.dumps(entry, allow_nan=False), identity),
            )
        return jsonify(catalog=entry)

    @app.post(UI_CATALOG_API + "/<identity>/plans")
    def create_ui_plan(identity):
        data = body("controlId", "name", "value", "expected", "tolerance", "timeout")
        plan = make_plan(get_entry(identity), data)
        result = app.extensions["plan_repository"].create_test_plan(plan)
        return jsonify(state=lab.snapshot(), **result), 201
