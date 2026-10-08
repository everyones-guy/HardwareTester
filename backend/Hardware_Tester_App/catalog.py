"""Workbench persistence adapter for the original blueprint/peripheral services."""

import copy
import uuid
from flask import request, jsonify
from .lab import LabError, new_device, now
from .blueprints import peripheral, properties_valid
from .services.blueprint_service import BlueprintService
from .services.peripheral_service import PeripheralService


class Catalog:
    def __init__(self, lab):
        self.lab = lab
        lab.state.setdefault("blueprints", [])
        lab.state.setdefault("peripherals", [])

    def editable(self):
        if self.lab.active:
            raise LabError("Stop the active test before changing configurations.", 409)

    def find(self, collection, identity):
        item = next(
            (p for p in self.lab.state[collection] if p["id"] == identity), None
        )
        if item is None:
            raise LabError("Configuration not found.", 404)
        return item

    def list_peripherals(self):
        return {
            "success": True,
            "peripherals": copy.deepcopy(self.lab.state["peripherals"]),
        }

    def add_peripheral(self, name, type, properties, device_id):
        self.editable()
        self.lab.device(device_id)
        if len(self.lab.state["peripherals"]) >= 500:
            raise LabError("The workspace supports 500 peripherals.", 409)
        item = peripheral({"name": name, "type": type, "properties": properties})
        item.update(id=str(uuid.uuid4()), device_id=device_id, version=1)
        self.lab.state["peripherals"].append(item)
        self.lab.log(f"Added peripheral {item['name']}.")
        self.lab.save()
        return {"success": True, "peripheralId": item["id"]}

    def update_peripheral(self, identity, properties):
        self.editable()
        item = self.find("peripherals", identity)
        item["properties"] = properties_valid(properties)
        item["version"] += 1
        self.lab.log(f"Updated peripheral {item['name']}.")
        self.lab.save()
        return {"success": True}

    def delete_peripheral(self, identity):
        self.editable()
        item = self.find("peripherals", identity)
        self.lab.state["peripherals"].remove(item)
        self.lab.log(f"Removed peripheral {item['name']}.")
        self.lab.save()
        return {"success": True}

    def capture(self, payload):
        return {
            "name": payload.get("name"),
            "description": payload.get("description", ""),
            "devices": [
                {
                    "name": d["name"],
                    "kind": d["kind"],
                    "peripherals": [
                        {k: p[k] for k in ("name", "type", "properties")}
                        for p in self.lab.state["peripherals"]
                        if p["device_id"] == d["id"]
                    ],
                }
                for d in self.lab.state["devices"]
            ],
        }

    def save_blueprint(self, source):
        self.editable()
        if len(self.lab.state["blueprints"]) >= 100:
            raise LabError("The library supports 100 blueprints.", 409)
        item = BlueprintService.normalize_configuration(source)
        item.update(id=str(uuid.uuid4()), createdAt=now())
        self.lab.state["blueprints"].append(item)
        self.lab.log(f"Saved blueprint {item['name']}.")
        self.lab.save()
        return item["id"]

    def apply(self, identity):
        self.editable()
        item = self.find("blueprints", identity)
        # Revalidate persisted source before constructing any new state.
        normalized = BlueprintService.normalize_configuration(item["configuration"])
        devices, peripherals = [], []
        for definition in normalized["devices"]:
            d = new_device(definition["kind"], definition["name"])
            devices.append(d)
            for p in definition["peripherals"]:
                peripherals.append(
                    dict(
                        copy.deepcopy(p),
                        id=str(uuid.uuid4()),
                        device_id=d["id"],
                        version=1,
                    )
                )
        if (
            len(self.lab.state["devices"]) + len(devices) > 100
            or len(self.lab.state["peripherals"]) + len(peripherals) > 500
        ):
            raise LabError(
                "This blueprint exceeds bench capacity (100 devices / 500 peripherals).",
                409,
            )
        self.lab.state["devices"].extend(devices)
        self.lab.state["peripherals"].extend(peripherals)
        self.lab.log(
            f"Applied blueprint {item['name']}: added {len(devices)} simulated devices."
        )
        self.lab.save()


def register_catalog(app, lab):
    catalog = Catalog(lab)

    @app.route("/api/lab/blueprints", methods=["GET", "POST"])
    @app.route("/api/lab/blueprints/preview", methods=["POST"])
    @app.route("/api/lab/blueprints/capture", methods=["POST"])
    @app.route("/api/lab/blueprints/<identity>/apply", methods=["POST"])
    @app.route("/api/lab/blueprints/<identity>", methods=["DELETE"])
    @app.route("/api/lab/peripherals", methods=["GET", "POST"])
    @app.route("/api/lab/peripherals/<identity>", methods=["PATCH", "DELETE"])
    def configurations(identity=None):
        with lab.lock:
            data = {} if request.method == "GET" else request.get_json()
            if not isinstance(data, dict):
                raise LabError("Request body must be a JSON object.")
            extra = {}
            path = request.path
            if "/peripherals" in path:
                if request.method == "GET":
                    extra = PeripheralService.list_peripherals(repository=catalog)
                elif identity:
                    item = catalog.find("peripherals", identity)
                    if data.get("version") != item["version"]:
                        raise LabError(
                            "This peripheral changed. Reload it before saving or deleting.",
                            409,
                        )
                    if request.method == "DELETE":
                        extra = PeripheralService.delete_peripheral(
                            identity, repository=catalog
                        )
                    else:
                        extra = PeripheralService.update_peripheral(
                            identity, data.get("properties"), repository=catalog
                        )
                else:
                    extra = PeripheralService.add_peripheral(
                        data.get("name"),
                        data.get("type"),
                        data.get("properties", {}),
                        data.get("device_id"),
                        repository=catalog,
                    )
            elif path.endswith("/preview"):
                extra["preview"] = BlueprintService.normalize_configuration(
                    data.get("configuration")
                )
            elif path.endswith("/capture"):
                extra["blueprintId"] = catalog.save_blueprint(catalog.capture(data))
            elif path.endswith("/apply"):
                catalog.apply(identity)
            elif request.method == "DELETE":
                catalog.editable()
                lab.state["blueprints"].remove(catalog.find("blueprints", identity))
                lab.save()
            elif request.method == "POST":
                extra["blueprintId"] = catalog.save_blueprint(data.get("configuration"))
            return jsonify(state=lab.snapshot(), **extra)
