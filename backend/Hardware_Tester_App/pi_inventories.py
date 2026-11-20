"""Store Pi inventory snapshots and evaluate declarations against their recorded fields."""

import json
import re
import uuid
from datetime import datetime

from flask import jsonify, request

from tools.capture_pi_inventory import (
    CONFIG_FILES,
    FIRMWARE_FIELDS,
    SERVICE_PROPERTIES,
    SERVICE_UNITS,
    STATE_TOKEN,
)
from tools.pi_provisioning import PI3B_MODEL, SHA256, make_plan

from .lab import LabError

INTERFACES = frozenset(
    {"gpio", "i2c", "spi", "serial", "usb", "ethernet", "wifi", "bluetooth"}
)
CUSTOM_FIELDS = {
    "osId": "OS ID",
    "osVersion": "OS version",
    "architecture": "Kernel architecture",
    "kernel": "Kernel release",
    "interface": "Interface observed",
}
INVENTORY_TEXT_FIELDS = ("model", "architecture", "kernel", "osId", "osVersion")
RECOMMENDED = {
    "arm-kernel": "ARM kernel architecture",
    "known-os-version": "OS version identified",
}
SPECIALIZED = {"pi3b-64bit": "64-bit Pi 3 Model B boot candidate"}
VIDEOCORE_REVISION = re.compile(r"[a-f0-9]{7,64}")
UTC_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)"
)
API = "/api/lab/pi-inventories"


def text_value(value, label, maximum=160):
    if isinstance(value, str):
        value = value.strip()
        if 1 <= len(value) <= maximum and value.isprintable():
            return value
    raise LabError(f"{label} must be 1 to {maximum} printable characters.")


def normalize_inventory(inventory):
    fields = {
        "schemaVersion",
        "capturedAt",
        "memoryMiB",
        "interfaces",
        *INVENTORY_TEXT_FIELDS,
    }
    version = inventory.get("schemaVersion") if isinstance(inventory, dict) else None
    if type(version) is not int or version not in (1, 2):
        raise LabError("Use a Raspberry Pi inventory with schemaVersion 1 or 2.")
    if inventory.keys() != (fields | {"observations"} if version == 2 else fields):
        raise LabError("The inventory fields do not match its schema version.")

    values = {
        field: text_value(inventory[field], field) for field in INVENTORY_TEXT_FIELDS
    }
    if not values["model"].startswith("Raspberry Pi "):
        raise LabError("The inventory model must identify a Raspberry Pi.")

    captured_at = inventory["capturedAt"]
    if not isinstance(captured_at, str) or not UTC_TIMESTAMP.fullmatch(captured_at):
        raise LabError("capturedAt must be an ISO 8601 UTC timestamp.")
    try:
        timestamp = datetime.fromisoformat(captured_at)
    except ValueError as exc:
        raise LabError("capturedAt must be a valid date and time.") from exc

    memory = inventory["memoryMiB"]
    if type(memory) is not int or not 1 <= memory <= 1_048_576:
        raise LabError("memoryMiB must be a positive integer in MiB.")
    interfaces = inventory["interfaces"]
    if (
        not isinstance(interfaces, list)
        or len(interfaces) > len(INTERFACES)
        or any(
            not isinstance(value, str) or value not in INTERFACES
            for value in interfaces
        )
        or len(set(interfaces)) != len(interfaces)
    ):
        raise LabError("interfaces must list unique, supported interface categories.")

    normalized = dict(
        values,
        schemaVersion=version,
        capturedAt=timestamp.isoformat().replace("+00:00", "Z"),
        memoryMiB=memory,
        interfaces=sorted(interfaces),
    )
    if version == 2:
        normalized["observations"] = normalize_observations(inventory["observations"])
    return normalized


def normalize_observations(observations):
    allowed = {
        "firmware": set(FIRMWARE_FIELDS),
        "configuration": set(CONFIG_FILES),
        "services": set(SERVICE_UNITS),
    }
    if not isinstance(observations, dict) or observations.keys() != allowed.keys():
        raise LabError(
            "Use the collector's firmware, configuration, and service observations."
        )
    for group, fields in allowed.items():
        values = observations[group]
        if not isinstance(values, dict) or values.keys() != fields:
            raise LabError(f"Unexpected {group} observations.")
        for key, value in values.items():
            if value is None:
                continue
            if group == "services":
                if (
                    not isinstance(value, dict)
                    or value.keys() != set(SERVICE_PROPERTIES.values())
                    or any(
                        not (token is None and property_name == "unitFileState")
                        and (
                            not isinstance(token, str)
                            or not STATE_TOKEN.fullmatch(token)
                        )
                        for property_name, token in value.items()
                    )
                ):
                    raise LabError(f"Invalid systemd state in {key}.")
            else:
                pattern = VIDEOCORE_REVISION if key == "videoCoreRevision" else SHA256
                if not isinstance(value, str) or not pattern.fullmatch(value):
                    raise LabError(f"Invalid revision or SHA-256 in {key}.")
    return observations


def inventory_drift(baseline, current):
    if any(baseline[key] != current[key] for key in ("model", "architecture")):
        raise LabError("Compare captures of the same board model and architecture.")
    if datetime.fromisoformat(baseline["capturedAt"]) > datetime.fromisoformat(
        current["capturedAt"]
    ):
        raise LabError("Select a baseline captured before the current inventory.")
    items = []

    def compare(group, name, before, after):
        state = (
            "unavailable"
            if before is None or after is None
            else "unchanged" if before == after else "changed"
        )
        items.append(
            dict(group=group, name=name, before=before, after=after, status=state)
        )

    for key in ("osId", "osVersion", "kernel"):
        compare("platform", key, baseline[key], current[key])
    for group, keys in (
        ("firmware", FIRMWARE_FIELDS),
        ("configuration", CONFIG_FILES),
        ("services", SERVICE_UNITS),
    ):
        before = baseline.get("observations", {}).get(group, {})
        after = current.get("observations", {}).get(group, {})
        for key in keys:
            compare(group, key, before.get(key), after.get(key))
    return items


def check_result(name, expected, actual, passed):
    return dict(name=name, expected=expected, actual=actual, passed=passed)


def evaluate_checks(inventory, payload):
    check_ids = payload.get("checkIds", [])
    custom = payload.get("customChecks", [])
    definitions = RECOMMENDED | SPECIALIZED
    if (
        not isinstance(check_ids, list)
        or len(check_ids) > len(definitions)
        or any(
            not isinstance(item, str) or item not in definitions for item in check_ids
        )
        or len(set(check_ids)) != len(check_ids)
    ):
        raise LabError("Choose unique check IDs from the Raspberry Pi inventory.")
    if not isinstance(custom, list) or len(custom) > 10:
        raise LabError("Use up to 10 custom checks.")
    if not check_ids and not custom:
        raise LabError("Choose at least one inventory check.")

    arch = inventory["architecture"]
    os_version = inventory["osVersion"]
    model = inventory["model"]
    results = {
        "arm-kernel": check_result(
            RECOMMENDED["arm-kernel"],
            "aarch64, armv6l, armv7l or armv8l",
            arch,
            arch in {"aarch64", "armv6l", "armv7l", "armv8l"},
        ),
        "known-os-version": check_result(
            RECOMMENDED["known-os-version"],
            "A recorded OS version",
            os_version,
            os_version.casefold() != "unknown",
        ),
        "pi3b-64bit": check_result(
            SPECIALIZED["pi3b-64bit"],
            "Raspberry Pi 3 Model B with an aarch64 kernel",
            f"{model} with a {arch} kernel",
            PI3B_MODEL.fullmatch(model) is not None and arch == "aarch64",
        ),
    }
    checks = [results[identity] for identity in check_ids]
    for item in custom:
        if not isinstance(item, dict) or item.keys() != {"field", "value"}:
            raise LabError("Each custom check needs a field and an expected value.")
        field = item["field"]
        if not isinstance(field, str) or field not in CUSTOM_FIELDS:
            raise LabError("Choose a supported custom inventory field.")
        value = text_value(item["value"], "Custom check expected value")
        if field == "interface":
            if value not in INTERFACES:
                raise LabError("Choose a supported interface category.")
            interfaces = inventory["interfaces"]
            actual = ", ".join(interfaces) or "No interfaces observed"
            passed = value in interfaces
        else:
            actual = inventory[field]
            passed = value == actual
        checks.append(check_result(CUSTOM_FIELDS[field], value, actual, passed))
    return checks


def register_pi_inventories(app, lab):
    with lab.lock, lab.connection:
        lab.connection.execute(
            "CREATE TABLE IF NOT EXISTS pi_inventories ("
            "id TEXT PRIMARY KEY, name TEXT NOT NULL, inventory TEXT NOT NULL)"
        )

    def response():
        with lab.lock:
            rows = lab.connection.execute(
                "SELECT id, name, inventory FROM pi_inventories ORDER BY rowid DESC"
            ).fetchall()
        return jsonify(
            inventories=[
                dict(
                    id=identity,
                    name=name,
                    inventory=json.loads(inventory),
                    recommendedChecks=[
                        dict(id=k, name=v) for k, v in RECOMMENDED.items()
                    ],
                    specializedChecks=[
                        dict(id=k, name=v) for k, v in SPECIALIZED.items()
                    ],
                )
                for identity, name, inventory in rows
            ]
        )

    def body():
        payload = request.get_json()
        if not isinstance(payload, dict):
            raise LabError("Request body must be a JSON object.")
        return payload

    def load_inventory(identity):
        with lab.lock:
            row = lab.connection.execute(
                "SELECT inventory FROM pi_inventories WHERE id = ?", (identity,)
            ).fetchone()
        if row is None:
            raise LabError("Raspberry Pi inventory not found.", 404)
        return json.loads(row[0])

    @app.get(API)
    def list_pi_inventories():
        return response()

    @app.post(API)
    def import_pi_inventory():
        payload = body()
        if payload.keys() != {"name", "inventory"}:
            raise LabError("An inventory import needs a name and an inventory.")
        name = text_value(payload["name"], "Inventory name", maximum=80)
        inventory = normalize_inventory(payload["inventory"])
        with lab.connection:
            count = lab.connection.execute(
                "SELECT COUNT(*) FROM pi_inventories"
            ).fetchone()[0]
            if count >= 100:
                raise LabError(
                    "The library supports 100 Raspberry Pi inventories.", 409
                )
            lab.connection.execute(
                "INSERT INTO pi_inventories (id, name, inventory) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), name, json.dumps(inventory)),
            )
        return response(), 201

    @app.delete(API + "/<identity>")
    def delete_pi_inventory(identity):
        with lab.connection:
            deleted = lab.connection.execute(
                "DELETE FROM pi_inventories WHERE id = ?", (identity,)
            ).rowcount
            if not deleted:
                raise LabError("Raspberry Pi inventory not found.", 404)
        return response()

    @app.post(API + "/<identity>/checks")
    def run_pi_inventory_checks(identity):
        payload = body()
        if payload.keys() - {"checkIds", "customChecks"}:
            raise LabError("Request body may only contain inventory checks.")
        return jsonify(checks=evaluate_checks(load_inventory(identity), payload))

    @app.get(API + "/<identity>/drift")
    def compare_pi_inventory(identity):
        baseline = request.args.get("baselineId")
        if not baseline or baseline == identity:
            raise LabError("Select a different saved baseline inventory.")
        with lab.lock:
            previous, current = load_inventory(baseline), load_inventory(identity)
        return jsonify(items=inventory_drift(previous, current))

    @app.post(API + "/<identity>/provisioning-plan")
    def plan_pi_provisioning(identity):
        payload = body()
        if payload.keys() != {"manifest"}:
            raise LabError("Provide the approved provisioning manifest.")
        try:
            plan = make_plan(load_inventory(identity), payload["manifest"])
        except ValueError as exc:
            raise LabError(str(exc)) from exc
        return jsonify(plan=plan)
