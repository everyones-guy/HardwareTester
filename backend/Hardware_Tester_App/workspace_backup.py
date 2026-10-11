"""Portable workspace archives and atomic, previewed additive imports."""

import copy
import hashlib
import json
import math
import uuid
from datetime import datetime
from flask import jsonify, request
from .lab import LabError, PLANS, new_device, now
from .blueprints import normalize_configuration, peripheral
from .results import eligible, series
from .test_plans import normalize_plan
from .scenarios import normalize as normalize_scenario, presets
from .validation_suites import normalize as normalize_suite

FORMAT = "hardware-tester-workspace"
MAX_BYTES = 20 * 1024 * 1024
LIMITS = dict(
    devices=100,
    peripherals=500,
    blueprints=100,
    testPlans=100,
    scenarios=100,
    validationSuites=100,
    runs=100,
    suiteRuns=10,
    logs=250,
)
HISTORY = {"runs", "suiteRuns", "logs"}
PRESETS = {p["id"]: p for p in presets()}


def text(value, label, maximum=10000, empty=False):
    if (
        not isinstance(value, str)
        or len(value) > maximum
        or (not empty and not value.strip())
    ):
        raise LabError(f"{label} must be text up to {maximum} characters.")
    return value


def integer(value, label, minimum=0, maximum=1000000000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise LabError(f"{label} must be an integer between {minimum} and {maximum}.")
    return value


def finite(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise LabError("Recorded numeric values must be finite numbers.")
    return value


def timestamp(value):
    text(value, "Timestamp", 80)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise LabError("Invalid recorded timestamp.") from error
    return value


def scrub(value, depth=0):
    if depth > 40:
        raise LabError("Archive nesting exceeds 40 levels.")
    if isinstance(value, dict):
        return {
            k: scrub(v, depth + 1)
            for k, v in value.items()
            if k.lower()
            not in {
                "password",
                "token",
                "access_token",
                "secret",
                "api_key",
                "auth",
                "cookie",
                "sessions",
            }
        }
    if isinstance(value, list):
        return [scrub(v, depth + 1) for v in value]
    if isinstance(value, float):
        finite(value)
    return value


def metadata(item, result):
    result["id"] = text(item.get("id"), "Item ID", 150)
    if "version" in item and not isinstance(item["version"], str):
        result["version"] = integer(item["version"], "Version", 1)
    for field in ("updatedAt", "createdAt"):
        if field in item:
            result[field] = timestamp(item[field])
    return result


def scenario(item):
    result = metadata(item, normalize_scenario(item))
    result.setdefault("version", 1)
    result["builtin"] = False
    return result


def device(item, snapshot=False):
    if not isinstance(item, dict):
        raise LabError("A device must be an object.")
    result = new_device(
        item.get("kind"),
        item.get("name"),
        item.get("adapter", "simulation"),
        item.get("endpoint"),
        item.get("baudrate", 115200),
    )
    result["id"] = text(item.get("id"), "Device ID", 150)
    result["value"] = finite(item.get("value"))
    if type(item.get("enabled")) is not bool or type(item.get("connected")) is not bool:
        raise LabError("Device connection and output flags must be boolean.")
    if item.get("fault") not in ("none", "timeout", "out-of-range"):
        raise LabError("Unknown device fault.")
    result.update(
        enabled=item["enabled"],
        connected=item["connected"] if snapshot else False,
        fault=item["fault"],
    )
    for field in ("lastError", "safetyWarning"):
        if item.get(field) is not None:
            result[field] = text(item[field], field, empty=True)
    if item.get("lastContactAt"):
        result["lastContactAt"] = timestamp(item["lastContactAt"])
    diagnostics = item.get("diagnostics", [])
    if not isinstance(diagnostics, list) or len(diagnostics) > 5:
        raise LabError("A device retains at most five connection checks.")
    for check in diagnostics:
        if not isinstance(check, dict) or check.get("status") not in (
            "passed",
            "warning",
            "failed",
        ):
            raise LabError("Invalid connection check.")
        timestamp(check.get("checkedAt"))
        text(check.get("detail"), "Connection detail", empty=True)
        finite(check.get("durationMs"))
        if check.get("value") is not None:
            finite(check["value"])
    if diagnostics:
        result["diagnostics"] = copy.deepcopy(diagnostics)
    if item.get("scenario"):
        if result["adapter"] != "simulation":
            raise LabError("Physical devices cannot contain simulation scenarios.")
        result["scenario"] = scenario(item["scenario"])
        result["scenarioCursor"] = integer(
            item.get("scenarioCursor", 0), "Scenario cursor", 0, 200
        )
        result["scenarioOutput"] = finite(item.get("scenarioOutput", result["value"]))
    return result


def attached(item):
    result = metadata(item, peripheral(item))
    result["device_id"] = text(item.get("device_id"), "Peripheral device ID", 150)
    result.setdefault("version", 1)
    return result


def recorded_plan(item, kind):
    if not isinstance(item, dict):
        raise LabError("Recorded plan must be an object.")
    text(item.get("id"), "Recorded plan ID", 150)
    text(item.get("name"), "Recorded plan name", 100)
    integer(item.get("version"), "Recorded plan version", 1)
    steps = item.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
        raise LabError("Recorded plans require 1–32 steps.")
    if all(isinstance(s, str) for s in steps):
        for s in steps:
            text(s, "Recorded step", 100)
    else:
        normalize_plan(dict(item, kind=kind))


def recorded_run(item):
    if not isinstance(item, dict):
        raise LabError("Recorded test must be an object.")
    for field in ("id", "deviceId", "deviceName", "plan"):
        text(item.get(field), field, 150)
    if item.get("status") not in ("passed", "failed", "cancelled"):
        raise LabError("Only completed or cancelled tests can be imported.")
    if "baseline" in item and (
        type(item["baseline"]) is not bool or (item["baseline"] and not eligible(item))
    ):
        raise LabError("Only a completed passing run can be a baseline.")
    timestamp(item.get("startedAt"))
    if item.get("finishedAt"):
        timestamp(item["finishedAt"])
    steps = item.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 32:
        raise LabError("Recorded tests require 1–32 checks.")
    for s in steps:
        if not isinstance(s, dict) or s.get("status") not in (
            "passed",
            "failed",
            "pending",
        ):
            raise LabError("Invalid recorded check.")
        text(s.get("name"), "Check name", 100)
        text(s.get("detail"), "Check detail", empty=True)
        for field in ("observed", "durationMs"):
            if field in s:
                finite(s[field])
        if "expected" in s:
            if not isinstance(s["expected"], dict) or set(s["expected"]) - {
                "min",
                "max",
                "value",
                "tolerance",
            }:
                raise LabError("Invalid recorded expectations.")
            for v in s["expected"].values():
                finite(v)
    for field in ("planId", "restoration"):
        if field in item:
            text(item[field], field, 150)
    config = item.get("configuration")
    if config is not None:
        if not isinstance(config, dict):
            raise LabError("Recorded configuration must be an object.")
        d = device(config.get("device"), snapshot=True)
        recorded_plan(config.get("plan"), d["kind"])
        if (
            not isinstance(config.get("peripherals"), list)
            or len(config["peripherals"]) > 500
        ):
            raise LabError("Invalid recorded peripherals.")
        for p in config["peripherals"]:
            attached(p)
    return copy.deepcopy(item)


def recorded_suite(item):
    if not isinstance(item, dict):
        raise LabError("Suite report must be an object.")
    text(item.get("id"), "Report ID", 150)
    normalize_suite(item.get("suite"))
    integer(item["suite"].get("version"), "Suite version", 1)
    d = device(item.get("device"), snapshot=True)
    plan = item.get("plan")
    if not isinstance(plan, dict):
        raise LabError("Suite report plan must be an object.")
    text(plan.get("id"), "Suite plan ID", 150)
    if isinstance(plan, dict) and plan.get("id") in PLANS and "steps" not in plan:
        text(plan.get("name"), "Suite plan name", 100)
        integer(plan.get("version"), "Suite plan version", 1)
    else:
        recorded_plan(plan, d["kind"])
    if item.get("status") not in ("passed", "failed", "cancelled", "error"):
        raise LabError("Only completed suite reports can be imported.")
    timestamp(item.get("startedAt"))
    for field in ("detail", "restoration"):
        if field in item:
            text(item[field], field, empty=True)
    cases = item.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 10:
        raise LabError("Invalid suite report cases.")
    for c in cases:
        normalize_suite(dict(item["suite"], cases=[c]))
        scenario(c.get("scenario"))
        if (
            c.get("status") not in ("passed", "failed", "cancelled", "error", "pending")
            or not isinstance(c.get("attempts"), list)
            or len(c["attempts"]) > 3
        ):
            raise LabError("Invalid suite report attempts.")
        for a in c["attempts"]:
            if (
                not isinstance(a, dict)
                or type(a.get("matched")) is not bool
                or a.get("expected") not in ("passed", "failed")
            ):
                raise LabError("Invalid suite attempt verdict.")
            recorded_run(a.get("run"))
    return copy.deepcopy(item)


def validate_archive(bundle):
    if (
        not isinstance(bundle, dict)
        or bundle.get("format") != FORMAT
        or type(bundle.get("version")) is not int
        or bundle["version"] != 1
    ):
        raise LabError("Choose a Hardware Tester workspace archive (version 1).")
    source = bundle.get("workspace")
    if not isinstance(source, dict) or set(source) != set(LIMITS):
        raise LabError("Archive must include every workspace collection.")
    source = scrub(source)
    result = {}
    for collection, limit in LIMITS.items():
        entries = source[collection]
        if not isinstance(entries, list) or len(entries) > limit:
            raise LabError(f"{collection} exceeds its archive capacity of {limit}.")
        result[collection] = []
        seen = set()
        for item in entries:
            if not isinstance(item, dict):
                raise LabError(f"Every {collection} entry must be an object.")
            identity = text(item.get("id"), "Item ID", 150)
            if identity in seen:
                raise LabError(f"Duplicate ID in {collection}.")
            seen.add(identity)
            if collection == "devices":
                normalized = device(item)
            elif collection == "peripherals":
                normalized = attached(item)
            elif collection == "blueprints":
                normalized = metadata(
                    item, normalize_configuration(item.get("configuration"))
                )
                normalized["name"] = text(item.get("name"), "Blueprint name", 100)
                normalized["description"] = text(
                    item.get("description", ""),
                    "Blueprint description",
                    2000,
                    empty=True,
                )
            elif collection == "testPlans":
                normalized = metadata(item, normalize_plan(item))
                normalized.setdefault("version", 1)
                if identity in PLANS:
                    raise LabError("Saved plans cannot use built-in plan IDs.")
            elif collection == "scenarios":
                normalized = scenario(item)
                if identity in PRESETS:
                    if normalize_scenario(item) != normalize_scenario(
                        PRESETS[identity]
                    ):
                        raise LabError(
                            "Built-in scenario definitions cannot be replaced."
                        )
                    normalized = copy.deepcopy(PRESETS[identity])
                elif item.get("builtin"):
                    raise LabError("Unknown built-in scenario.")
            elif collection == "validationSuites":
                normalized = metadata(item, normalize_suite(item))
                normalized.setdefault("version", 1)
            elif collection == "runs":
                normalized = recorded_run(item)
            elif collection == "suiteRuns":
                normalized = recorded_suite(item)
            else:
                timestamp(item.get("time"))
                text(item.get("message"), "Log message", empty=True)
                if item.get("level") not in ("info", "error", "success"):
                    raise LabError("Unknown log level.")
                for field in ("deviceId", "runId"):
                    if item.get(field) is not None:
                        text(item[field], field, 150)
                normalized = copy.deepcopy(item)
            result[collection].append(normalized)
    return result


def remap(value, maps, collection=""):
    """Rebind only reference fields; archived measurement snapshots remain intact."""
    if isinstance(value, list):
        return [remap(v, maps, collection) for v in value]
    if not isinstance(value, dict):
        return value
    result = {}
    references = {
        "deviceId": "devices",
        "device_id": "devices",
        "planId": "testPlans",
        "scenarioId": "scenarios",
        "runId": "runs",
    }
    nested = {
        "device": "devices",
        "plan": "testPlans",
        "scenario": "scenarios",
        "suite": "validationSuites",
        "run": "runs",
        "peripherals": "peripherals",
    }
    for k, v in value.items():
        if k == "id" and isinstance(v, str):
            result[k] = maps.get(collection, {}).get(v, v)
        elif k in references and isinstance(v, str):
            result[k] = maps[references[k]].get(v, v)
        elif k in nested or k in ("configuration", "cases", "attempts"):
            result[k] = (
                copy.deepcopy(v)
                if collection == "blueprints"
                else remap(v, maps, nested.get(k, ""))
            )
        else:
            result[k] = copy.deepcopy(v)
    return result


def prepare(lab, payload):
    if (
        not isinstance(payload, dict)
        or payload.get("policy") not in ("keep", "copy")
        or type(payload.get("includeHistory")) is not bool
    ):
        raise LabError("Choose keep/copy conflicts and whether to include history.")
    incoming = validate_archive(payload.get("archive"))
    digest = hashlib.sha256(
        json.dumps(
            dict(
                workspace=incoming,
                policy=payload["policy"],
                includeHistory=payload["includeHistory"],
            ),
            sort_keys=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()
    candidate = copy.deepcopy(lab.state)
    maps, imports, rows = {}, {}, []
    revision = lab.state.get("revision", 0)
    for collection, entries in incoming.items():
        current = candidate.get(collection, [])
        by_id = {i["id"]: i for i in current}
        by_name = {i.get("name", "").casefold(): i for i in current}
        maps[collection], imports[collection] = {}, []
        row = dict(
            collection=collection,
            incoming=len(entries),
            added=0,
            copied=0,
            skipped=0,
            conflicts=[],
            trimmed=0,
        )
        for item in entries:
            conflict = by_id.get(item["id"])
            if (
                not conflict
                and collection not in HISTORY
                and collection != "peripherals"
            ):
                conflict = by_name.get(item.get("name", "").casefold())
            builtin = collection == "scenarios" and item["id"] in PRESETS
            if collection in HISTORY and not payload["includeHistory"]:
                row["skipped"] += 1
                continue
            if conflict and not builtin:
                row["conflicts"].append(
                    dict(
                        name=item.get("name", item["id"]),
                        existingName=conflict.get("name", conflict["id"]),
                    )
                )
            if conflict and (
                payload["policy"] == "keep" or builtin or collection in HISTORY
            ):
                maps[collection][item["id"]] = conflict["id"]
                row["skipped"] += 1
                continue
            imported = copy.deepcopy(item)
            if conflict:
                imported["id"] = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"{digest}:{revision}:{collection}:{item['id']}",
                    )
                )
                imported["name"] = f"{item['name'][:89]} (imported)"
                if "version" in imported and collection != "blueprints":
                    imported["version"] = 1
                row["copied"] += 1
            maps[collection][item["id"]] = imported["id"]
            imports[collection].append(imported)
            row["added"] += 1
        rows.append(row)
    for row in rows:
        collection = row["collection"]
        added = [remap(item, maps, collection) for item in imports[collection]]
        # IDs were assigned above; remap references without remapping the new ID again.
        combined = (
            added + candidate.get(collection, [])
            if collection in HISTORY
            else candidate.get(collection, []) + added
        )
        if collection in HISTORY:
            key = "time" if collection == "logs" else "startedAt"
            combined.sort(
                key=lambda item: datetime.fromisoformat(
                    item[key].replace("Z", "+00:00")
                ).timestamp(),
                reverse=True,
            )
            retained = LIMITS[collection] - (
                1 if collection == "logs" and any(r["added"] for r in rows) else 0
            )
            row["trimmed"] = max(0, len(combined) - retained)
            combined = combined[:retained]
            retained_ids = {item["id"] for item in combined}
            row["added"] = sum(item["id"] in retained_ids for item in added)
        elif len(combined) > LIMITS[collection]:
            raise LabError(
                f"Import exceeds {collection} capacity ({LIMITS[collection]}). Choose keep existing or a smaller archive.",
                409,
            )
        candidate[collection] = combined
    # Retained existing baselines win collisions; otherwise prefer the newest import.
    existing_baselines = {r["id"] for r in lab.state["runs"] if r.get("baseline")}
    chosen = set()
    for run in sorted(
        candidate["runs"], key=lambda r: r["id"] not in existing_baselines
    ):
        if run.get("baseline"):
            if series(run) in chosen:
                run.pop("baseline", None)
            else:
                chosen.add(series(run))
    devices = {d["id"]: d for d in candidate["devices"]}
    plans = {p["id"]: p for p in candidate["testPlans"]}
    scenarios = {s["id"] for s in candidate["scenarios"]}
    for p in candidate["peripherals"]:
        if p["device_id"] not in devices:
            raise LabError("A peripheral references a missing device.")
    warnings = []
    for s in candidate["validationSuites"]:
        plan = plans.get(s["planId"])
        if (
            s["planId"] not in PLANS and (not plan or plan["kind"] != s["kind"])
        ) or any(c["scenarioId"] not in scenarios for c in s["cases"]):
            warnings.append(
                f"{s['name']}: replace a missing or incompatible plan/scenario before running."
            )
    preview = dict(
        revision=revision,
        digest=digest,
        rows=rows,
        warnings=warnings,
        added=sum(r["added"] for r in rows),
        policy=payload["policy"],
        includeHistory=payload["includeHistory"],
    )
    return candidate, preview


def register_backup(app, lab):
    def payload():
        try:
            return request.get_json()
        except RecursionError as error:
            raise LabError("Archive nesting is too deep.") from error

    def idle():
        if lab.active or lab.suites.active:
            raise LabError(
                "Stop the active test or suite before backing up or importing.", 409
            )

    @app.get("/api/lab/workspace/backup")
    def export_workspace():
        with lab.lock:
            idle()
            archive = dict(
                format=FORMAT,
                version=1,
                exportedAt=now(),
                workspace=scrub(
                    {k: copy.deepcopy(lab.state.get(k, [])) for k in LIMITS}
                ),
            )
            if len(json.dumps(archive, allow_nan=False).encode()) > MAX_BYTES - 4096:
                raise LabError(
                    "Workspace archive exceeds the 20 MB portable archive limit.", 413
                )
            return jsonify(archive)

    @app.post("/api/lab/workspace/preview")
    def preview_workspace():
        with lab.lock:
            idle()
            _, preview = prepare(lab, payload())
            return jsonify(preview=preview)

    @app.post("/api/lab/workspace/import")
    def import_workspace():
        with lab.lock:
            idle()
            data = payload()
            candidate, preview = prepare(lab, data)
            if (
                type(data.get("revision")) is not int
                or data["revision"] != preview["revision"]
                or data.get("digest") != preview["digest"]
            ):
                raise LabError(
                    "The workspace or import choices changed. Preview the archive again.",
                    409,
                )
            previous = lab.state
            try:
                lab.state = candidate
                lab.log(
                    f"Imported workspace archive: {preview['added']} entries added."
                )
                lab.save()
            except Exception:
                lab.connection.rollback()
                lab.state = previous
                raise
            return jsonify(state=lab.snapshot(), preview=preview)
