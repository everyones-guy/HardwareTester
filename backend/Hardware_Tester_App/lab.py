"""Persistent, single-owner lab engine. One process owns transports and the runner."""

import copy
import json
import math
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from .transports import TransportError, create_transport, numeric

PROFILES = {
    "temperature": ("MQTT", "sim://mqtt/lab/temperature"),
    "valve": ("Serial", "sim://serial/COM-DEMO"),
    "relay": ("USB", "sim://usb/relay-01"),
}
PLANS = {
    "smoke": (
        "Connection & health",
        ["Connection handshake", "Read telemetry", "Validate operating range"],
    ),
    "control": (
        "Control response",
        [
            "Connection handshake",
            "Send control command",
            "Verify response",
            "Restore initial state",
        ],
    ),
}


def now():
    return datetime.now(timezone.utc).isoformat()


class LabError(Exception):
    def __init__(self, message, status=400):
        self.status = status
        super().__init__(message)


def new_device(kind, name, adapter="simulation", endpoint=None, baudrate=115200):
    if (
        not isinstance(kind, str)
        or not isinstance(adapter, str)
        or kind not in PROFILES
        or adapter not in ("simulation", "serial", "mqtt")
    ):
        raise LabError("Unknown device profile or adapter.")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise LabError("Device name must contain 1–100 characters.")
    if adapter != "simulation":
        if not isinstance(endpoint, str) or not endpoint.strip() or len(endpoint) > 250:
            raise LabError("A real transport endpoint is required.")
        if adapter == "serial" and (
            not isinstance(baudrate, int)
            or isinstance(baudrate, bool)
            or not 1200 <= baudrate <= 1000000
        ):
            raise LabError("Baud rate must be an integer between 1200 and 1000000.")
        if adapter == "serial" and "://" in endpoint:
            raise LabError(
                "Use a local serial port such as COM3 or /dev/ttyUSB0, not a URL."
            )
        if adapter == "mqtt":
            try:
                uri = urlparse(endpoint)
                valid = (
                    uri.scheme == "mqtt"
                    and uri.hostname
                    and uri.path.strip("/")
                    and not uri.username
                    and not uri.password
                    and not uri.query
                    and not uri.fragment
                    and (uri.port is None or 1 <= uri.port <= 65535)
                    and not any(x in uri.path for x in ("+", "#"))
                )
            except ValueError:
                valid = False
            if not valid:
                raise LabError(
                    "Use mqtt://broker:1883/device/topic without credentials or wildcards."
                )
    return {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "kind": kind,
        "adapter": adapter,
        "protocol": (
            PROFILES[kind][0]
            if adapter == "simulation"
            else "Serial" if adapter == "serial" else "MQTT"
        ),
        "endpoint": PROFILES[kind][1] if adapter == "simulation" else endpoint.strip(),
        "baudrate": baudrate,
        "connected": False,
        "fault": "none",
        "value": 24 if kind == "temperature" else 0,
        "enabled": False,
        "lastError": None,
    }


def initial_state():
    return {
        "version": 1,
        "devices": [
            new_device(k, n)
            for k, n in [
                ("temperature", "Ambient temperature"),
                ("valve", "Intake valve"),
                ("relay", "Pump relay"),
            ]
        ],
        "runs": [],
        "logs": [],
    }


class Lab:
    def __init__(
        self,
        path,
        allow_hardware=False,
        autostart=True,
        step_seconds=0.75,
        transport_factory=create_transport,
    ):
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.adapters = {}
        self.transport_factory = transport_factory
        self.allow_hardware = allow_hardware
        self.step_seconds = step_seconds
        self.active = None
        self.next_step = 0
        self.last_tick = time.monotonic()
        self.tick = 0
        self.closed = False
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path), check_same_thread=False)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS lab_state (id INTEGER PRIMARY KEY CHECK(id = 1), payload TEXT NOT NULL)"
        )
        row = self.connection.execute(
            "SELECT payload FROM lab_state WHERE id=1"
        ).fetchone()
        self.state = json.loads(row[0]) if row else initial_state()
        self.state.setdefault("peripherals", [])
        self.state.setdefault("blueprints", [])
        self.state.setdefault("testPlans", [])
        for d in self.state["devices"]:
            d["connected"] = False
        for run in self.state["runs"]:
            if run["status"] == "running":
                run["status"] = "cancelled"
                run["finishedAt"] = now()
                d = next(
                    (d for d in self.state["devices"] if d["id"] == run["deviceId"]),
                    None,
                )
                if d and d["adapter"] == "simulation":
                    d["value"] = run["originalValue"]
                    d["enabled"] = run["originalEnabled"]
                    if d.get("scenario"):
                        d["scenarioOutput"] = run["originalValue"]
                elif d:
                    d["lastError"] = (
                        "Server restarted during a run. Physical output state is unknown; inspect hardware before reconnecting."
                    )
                    d["safetyWarning"] = d["lastError"]
                self.log(
                    "Interrupted test cancelled on server restart; transports are disconnected."
                )
        self.save()
        self.worker = None
        if autostart:
            self.worker = threading.Thread(
                target=self.work, name="hardware-lab", daemon=True
            )
            self.worker.start()

    def log(self, message, level="info", device_id=None, run_id=None):
        self.state["logs"].insert(
            0,
            {
                "id": str(uuid.uuid4()),
                "time": now(),
                "level": level,
                "message": message,
                "deviceId": device_id
                or (self.active["device"]["id"] if self.active else None),
                "runId": run_id or (self.active["run"]["id"] if self.active else None),
            },
        )
        del self.state["logs"][250:]

    def save(self):
        self.state["revision"] = self.state.get("revision", 0) + 1
        self.connection.execute(
            "INSERT INTO lab_state VALUES(1, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
            (json.dumps(self.state, allow_nan=False),),
        )
        self.connection.commit()

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def in_range(self, device, value):
        limits = []
        for p in self.state["peripherals"]:
            if (
                p["device_id"] == device["id"]
                and p["properties"].get("threshold") is not None
            ):
                t = p["properties"]["threshold"]
                limits.append(t if isinstance(t, dict) else {"max": t})
        if not limits:
            return (
                0
                <= value
                <= {"temperature": 50, "valve": 100, "relay": 1}[device["kind"]]
            )
        return all(
            t.get("min", -math.inf) <= value <= t.get("max", math.inf) for t in limits
        )

    def device(self, device_id):
        d = next((d for d in self.state["devices"] if d["id"] == device_id), None)
        if not d:
            raise LabError("Device not found.", 404)
        return d

    def add(self, payload):
        with self.lock:
            if len(self.state["devices"]) >= 100:
                raise LabError("The bench supports up to 100 devices.", 409)
            d = new_device(
                payload.get("kind"),
                payload.get("name"),
                payload.get("adapter", "simulation"),
                payload.get("endpoint"),
                payload.get("baudrate", 115200),
            )
            if d["adapter"] != "simulation" and not self.allow_hardware:
                raise LabError(
                    "Real hardware is disabled. Set LAB_ALLOW_HARDWARE=true before adding a real transport.",
                    403,
                )
            self.state["devices"].append(d)
            self.log(f"Added {d['name']} ({d['adapter']}).", device_id=d["id"])
            self.save()
            return d["id"]

    def remove(self, device_id):
        with self.lock:
            if self.active:
                raise LabError("Stop the active test before removing a device.", 409)
            d = self.device(device_id)
            self.disconnect(d)
            self.state["devices"].remove(d)
            self.state["peripherals"] = [
                p for p in self.state["peripherals"] if p["device_id"] != device_id
            ]
            self.log(f"Removed {d['name']}.", device_id=d["id"])
            self.save()

    def disconnect(self, d):
        adapter = self.adapters.pop(d["id"], None)
        if adapter:
            adapter.close()
        d["connected"] = False

    def connect(self, device_id, connected):
        with self.lock:
            if not isinstance(connected, bool):
                raise LabError("connected must be a boolean.")
            d = self.device(device_id)
            if connected and not d["connected"]:
                if d["adapter"] != "simulation" and not self.allow_hardware:
                    raise LabError("Real hardware is disabled.", 403)
                adapter = self.transport_factory(d)
                try:
                    adapter.connect()
                    if d["adapter"] != "simulation":
                        d["value"] = numeric(adapter.read())
                    self.adapters[d["id"]] = adapter
                    d["connected"] = True
                    d["lastContactAt"] = (
                        now()
                        if d["adapter"] != "simulation"
                        else d.get("lastContactAt")
                    )
                    d["lastError"] = None
                except Exception as error:
                    adapter.close()
                    d["lastError"] = str(error)[:300]
                    self.log(
                        f"{d['name']}: connection failed: {d['lastError']}",
                        "error",
                        device_id=d["id"],
                    )
                    self.save()
                    raise LabError(d["lastError"], 502) from error
            elif not connected:
                self.disconnect(d)
            self.log(
                f"{d['name']} {'connected' if connected else 'disconnected'} ({d['adapter']}).",
                "success" if connected else "info",
                device_id=d["id"],
            )
            self.save()

    def connect_bench(self):
        # A bulk action must never open an unreviewed physical connection.
        for d in self.snapshot()["devices"]:
            if d["adapter"] == "simulation" and not d["connected"]:
                self.connect(d["id"], True)

    def fault(self, device_id, fault):
        with self.lock:
            d = self.device(device_id)
            if d.get("scenario"):
                raise LabError(
                    "Clear the emulator scenario before injecting a manual fault.", 409
                )
            if fault not in ("none", "timeout", "out-of-range"):
                raise LabError("Unknown fault profile.")
            if d["adapter"] != "simulation":
                raise LabError(
                    "Fault injection is only available for simulated devices."
                )
            d["fault"] = fault
            d["value"] = (
                (95 if d["kind"] == "temperature" else 150)
                if fault == "out-of-range"
                else (
                    (24 if d["kind"] == "temperature" else 0)
                    if fault == "none"
                    else d["value"]
                )
            )
            self.log(
                f"{d['name']}: {fault} fault profile.",
                "error" if fault != "none" else "info",
                device_id=d["id"],
            )
            self.save()

    def read(self, d):
        if not d["connected"] or d["id"] not in self.adapters:
            raise TransportError("Device disconnected. Connect the device and retry.")
        d["value"] = numeric(self.adapters[d["id"]].read())
        d["lastError"] = None
        d["lastContactAt"] = now()
        return d["value"]

    def diagnose(self, device_id):
        with self.lock:
            if self.active:
                raise LabError("Connection checks are disabled during a test.", 409)
            d = self.device(device_id)
            started = time.monotonic()
            checked_at = now()
            value = None
            try:
                value = self.read(d)
                maximum = {"temperature": 50, "valve": 100, "relay": 1}[d["kind"]]
                healthy = 0 <= value <= maximum
                status = "passed" if healthy else "warning"
                detail = (
                    f"Received {value}; within expected range 0–{maximum}."
                    if healthy
                    else f"Transport responded, but reading {value} is outside expected range 0–{maximum}."
                )
            except Exception as error:
                status = "failed"
                detail = str(error)[:300]
                d["lastError"] = detail
            check = {
                "checkedAt": checked_at,
                "status": status,
                "detail": detail,
                "durationMs": round((time.monotonic() - started) * 1000),
                "value": value,
            }
            d["diagnostics"] = [check, *d.get("diagnostics", [])][:5]
            self.log(
                f"{d['name']}: connection check {status}: {detail}",
                "success" if status == "passed" else "error",
                device_id=d["id"],
            )
            self.save()

    def write(self, d, value):
        if not d["connected"] or d["id"] not in self.adapters:
            raise TransportError("Device disconnected. Connect the device and retry.")
        d["value"] = numeric(self.adapters[d["id"]].write(value))
        d["enabled"] = d["value"] > 0

    def command(self, device_id, value):
        with self.lock:
            if self.active:
                raise LabError("Manual commands are disabled during a test.", 409)
            d = self.device(device_id)
            maximum = {"temperature": 50, "valve": 100, "relay": 1}[d["kind"]]
            try:
                numeric(value)
            except TransportError as error:
                raise LabError(str(error)) from error
            if not 0 <= value <= maximum or (
                d["kind"] == "relay" and value not in (0, 1)
            ):
                raise LabError(f"Command value must be in range 0–{maximum}.")
            try:
                self.write(d, value)
            except Exception as error:
                d["lastError"] = str(error)[:300]
                self.log(
                    f"{d['name']}: command failed: {error}", "error", device_id=d["id"]
                )
                self.save()
                raise LabError(str(error), 502) from error
            self.log(
                f"{d['name']}: sent {value}; observed {d['value']}.",
                "success",
                device_id=d["id"],
            )
            d["safetyWarning"] = None
            self.save()

    def start(self, device_id, plan, actor=None):
        with self.lock:
            if self.active:
                raise LabError("A test is already running.", 409)
            if not isinstance(plan, str):
                raise LabError("Unknown test plan.")
            d = self.device(device_id)
            if not d["connected"]:
                raise LabError("Connect the device before running a test.", 409)
            definition = None
            if plan not in PLANS:
                from .test_plans import PlanRepository, normalize_plan

                saved = PlanRepository(self).find(plan)
                definition = dict(
                    normalize_plan(saved), id=saved["id"], version=saved["version"]
                )
                if definition["kind"] != d["kind"]:
                    raise LabError(
                        "The test plan profile does not match this device.", 409
                    )
            title = definition["name"] if definition else PLANS[plan][0]
            names = (
                ["Connection handshake"]
                + [s["name"] for s in definition["steps"]]
                + (
                    ["Restore initial state"]
                    if any(s["action"] == "set" for s in definition["steps"])
                    else []
                )
                if definition
                else PLANS[plan][1]
            )
            run = {
                "id": str(uuid.uuid4()),
                "deviceId": d["id"],
                "deviceName": d["name"],
                "plan": title,
                "startedAt": now(),
                "status": "running",
                "originalValue": (
                    d.get("scenarioOutput", d["value"])
                    if d.get("scenario")
                    else d["value"]
                ),
                "originalEnabled": d["enabled"],
                "steps": [
                    {"name": name, "status": "pending", "detail": "Waiting to execute"}
                    for name in names
                ],
            }
            if actor:
                run["startedBy"] = {
                    key: actor[key] for key in ("id", "username", "role")
                }
            run["configuration"] = {
                "device": copy.deepcopy(d),
                "peripherals": copy.deepcopy(
                    [p for p in self.state["peripherals"] if p["device_id"] == d["id"]]
                ),
                "plan": (
                    copy.deepcopy(definition)
                    if definition
                    else {"id": plan, "version": 1, "name": title, "steps": list(names)}
                ),
                "workspaceRevision": self.state.get("revision", 0),
            }
            if not definition:
                run["configuration"]["plan"]["parameters"] = {
                    "defaultMin": 0,
                    "defaultMax": {"temperature": 50, "valve": 100, "relay": 1}[
                        d["kind"]
                    ],
                    "controlValue": {"temperature": 30, "valve": 75, "relay": 1}[
                        d["kind"]
                    ],
                }
            self.state["runs"].insert(0, run)
            del self.state["runs"][100:]
            self.active = {
                "run": run,
                "device": d,
                "plan": plan,
                "definition": definition,
                "index": 0,
                "changed": False,
            }
            self.next_step = time.monotonic() + self.step_seconds
            self.log(
                f"Started {run['plan']} on {d['name']} ({d['adapter']}).",
                device_id=d["id"],
            )
            self.save()
            return run["id"]

    def cleanup(self, active):
        if not active["changed"]:
            active["run"]["restoration"] = "not-needed"
            return
        d, run = active["device"], active["run"]
        if d["adapter"] == "simulation":
            d["value"], d["enabled"] = run["originalValue"], run["originalEnabled"]
            if d.get("scenario"):
                d["scenarioOutput"] = run["originalValue"]
            run["restoration"] = "restored"
            return
        try:
            self.write(d, run["originalValue"])
            if self.read(d) != run["originalValue"]:
                raise TransportError(
                    "Restore acknowledgement did not match the original output."
                )
            run["restoration"] = "restored"
        except Exception as error:
            run["restoration"] = "failed"
            d["lastError"] = f"Output restoration failed; inspect hardware: {error}"[
                :300
            ]
            d["safetyWarning"] = d["lastError"]
            self.log(d["lastError"], "error")
            run["steps"].append(
                {
                    "name": "Cleanup original output",
                    "status": "failed",
                    "detail": d["lastError"],
                }
            )

    def cancel(self):
        with self.lock:
            if not self.active:
                raise LabError("No test is running.", 409)
            active = self.active
            self.cleanup(active)
            active["run"].update(status="cancelled", finishedAt=now())
            self.active = None
            self.log(
                "Test cancelled. Inspect cleanup results for output restoration.",
                device_id=active["device"]["id"],
                run_id=active["run"]["id"],
            )
            self.save()

    def advance(self):
        with self.lock:
            if not self.active:
                return
            active = self.active
            d, run = active["device"], active["run"]
            step = run["steps"][active["index"]]
            name = step["name"]
            if active.get("definition"):
                self.advance_custom(active, step)
                return
            started = time.monotonic()
            step["startedAt"] = now()
            maximum = {"temperature": 50, "valve": 100, "relay": 1}[d["kind"]]
            if name == "Validate operating range":
                step["expected"] = {"min": 0, "max": maximum}
            if name == "Verify response":
                step["expected"] = {
                    "value": {"temperature": 30, "valve": 75, "relay": 1}[d["kind"]],
                    "tolerance": 0,
                }
            if name == "Restore initial state":
                step["expected"] = {"value": run["originalValue"], "tolerance": 0}
            try:
                if name == "Send control command":
                    if any(
                        previous["status"] == "failed"
                        for previous in run["steps"][: active["index"]]
                    ):
                        raise TransportError(
                            "Control command skipped because the connection check failed."
                        )
                    active["changed"] = (
                        True  # A missing ACK does not prove an output stayed unchanged.
                    )
                    self.write(
                        d, {"temperature": 30, "valve": 75, "relay": 1}[d["kind"]]
                    )
                elif name == "Restore initial state" and active["changed"]:
                    self.write(d, run["originalValue"])
                value = self.read(d)
                step["observed"] = value
                if name in (
                    "Validate operating range",
                    "Verify response",
                ) and not self.in_range(d, value):
                    raise TransportError(
                        f"Reading {value} is outside expected operating range."
                    )
                if (
                    name == "Verify response"
                    and value != {"temperature": 30, "valve": 75, "relay": 1}[d["kind"]]
                ):
                    raise TransportError(
                        f"Command response mismatch: received {value}."
                    )
                if name == "Restore initial state" and value != run["originalValue"]:
                    raise TransportError(
                        f'Restoration mismatch: expected {run["originalValue"]}, received {value}.'
                    )
                step.update(
                    status="passed",
                    detail=f'{name}: observed {value} via {d["adapter"]}.',
                )
            except Exception as error:
                step.update(status="failed", detail=str(error)[:300])
                d["lastError"] = step["detail"]
            step["durationMs"] = round((time.monotonic() - started) * 1000)
            step["finishedAt"] = now()
            self.log(
                f"{d['name']} · {step['detail']}",
                "success" if step["status"] == "passed" else "error",
                device_id=d["id"],
            )
            active["index"] += 1
            if active["index"] == len(run["steps"]):
                self.cleanup(active)
                run.update(
                    status=(
                        "passed"
                        if all(s["status"] == "passed" for s in run["steps"])
                        else "failed"
                    ),
                    finishedAt=now(),
                )
                self.active = None
                self.log(
                    f"{d['name']}: test {run['status']}.",
                    "success" if run["status"] == "passed" else "error",
                    d["id"],
                    run["id"],
                )
            self.save()

    def advance_custom(self, active, step):
        """Execute one typed step; waits yield to the worker rather than blocking it."""
        d, run = active["device"], active["run"]
        definitions = active["definition"]["steps"]
        index = active["index"]
        operation = (
            {"action": "read", "timeout": 2}
            if index == 0
            else (
                definitions[index - 1]
                if index <= len(definitions)
                else {"action": "restore", "timeout": 2}
            )
        )
        action = operation["action"]
        adapter = self.adapters.get(d["id"])
        previous_timeout = getattr(adapter, "timeout", 2)
        started = time.monotonic()
        step.setdefault("startedAt", now())
        step_started = active.setdefault("step_started", started)
        if action == "assert_range":
            step["expected"] = {"min": operation["min"], "max": operation["max"]}
        if action in ("assert_equal", "set"):
            step["expected"] = {
                "value": operation["value"],
                "tolerance": operation.get("tolerance", 0),
            }
        if action == "restore":
            step["expected"] = {"value": run["originalValue"], "tolerance": 0}
        try:
            if action == "wait":
                deadline = active.setdefault(
                    "wait_until", started + operation["seconds"]
                )
                if started < deadline:
                    self.next_step = min(deadline, started + 0.1)
                    return
                active.pop("wait_until", None)
                detail = f"Waited {operation['seconds']} seconds."
            else:
                # After any failed check, do not issue further control commands.
                if action == "set" and any(
                    s["status"] == "failed" for s in run["steps"][:index]
                ):
                    raise TransportError(
                        "Control command skipped because a previous check failed."
                    )
                if adapter:
                    adapter.timeout = operation["timeout"]
                if action == "set":
                    active["changed"] = True
                    self.write(d, operation["value"])
                elif action == "restore":
                    if active["changed"]:
                        self.write(d, run["originalValue"])
                remaining = operation["timeout"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise TransportError("Step response exceeded its timeout.")
                if adapter:
                    adapter.timeout = remaining
                value = self.read(d)
                step["observed"] = value
                if time.monotonic() - started > operation["timeout"]:
                    raise TransportError("Step response exceeded its timeout.")
                if (
                    action == "assert_range"
                    and not operation["min"] <= value <= operation["max"]
                ):
                    raise TransportError(
                        f"Reading {value} is outside expected range {operation['min']}–{operation['max']}."
                    )
                if (
                    action == "assert_equal"
                    and abs(value - operation["value"]) > operation["tolerance"]
                ):
                    raise TransportError(
                        f"Expected {operation['value']} ± {operation['tolerance']}; received {value}."
                    )
                if action == "restore" and value != run["originalValue"]:
                    raise TransportError(
                        f"Restoration mismatch: expected {run['originalValue']}, received {value}."
                    )
                detail = f'{action}: observed {value} via {d["adapter"]}.'
                step["observed"] = value
            step.update(status="passed", detail=detail)
        except Exception as error:
            step.update(status="failed", detail=str(error)[:300])
            d["lastError"] = step["detail"]
        finally:
            if adapter:
                adapter.timeout = previous_timeout
        step["durationMs"] = round((time.monotonic() - step_started) * 1000)
        active.pop("step_started", None)
        step["finishedAt"] = now()
        self.log(
            f"{d['name']} · {step['detail']}",
            "success" if step["status"] == "passed" else "error",
            device_id=d["id"],
        )
        active["index"] += 1
        if active["index"] == len(run["steps"]):
            self.cleanup(active)
            run.update(
                status=(
                    "passed"
                    if all(s["status"] == "passed" for s in run["steps"])
                    else "failed"
                ),
                finishedAt=now(),
            )
            self.active = None
            self.log(
                f"{d['name']}: test {run['status']}.",
                "success" if run["status"] == "passed" else "error",
                d["id"],
                run["id"],
            )
        self.save()

    def work(self):
        while not self.stop_event.wait(0.1):
            try:
                with self.lock:
                    if time.monotonic() - self.last_tick >= 1:
                        self.tick += 1
                        self.last_tick = time.monotonic()
                        for d in self.state["devices"]:
                            if (
                                d.get("scenario")
                                or not d["connected"]
                                or self.active
                                and self.active["device"]["id"] == d["id"]
                            ):
                                continue
                            if (
                                d["adapter"] == "simulation"
                                and d["kind"] == "temperature"
                                and d["fault"] == "none"
                            ):
                                d["value"] = round(
                                    24 + math.sin(self.tick / 4) * 1.4, 1
                                )
                            try:
                                self.read(d)
                            except Exception as error:
                                message = str(error)[:300]
                                if d.get("lastError") != message:
                                    self.log(
                                        f"{d['name']}: {message}",
                                        "error",
                                        device_id=d["id"],
                                    )
                                d["lastError"] = message
                        self.save()
                    if self.active and time.monotonic() >= self.next_step:
                        self.next_step = time.monotonic() + self.step_seconds
                        self.advance()
                    if hasattr(self, "suites"):
                        self.suites.tick()
            except Exception:
                import logging

                logging.getLogger(__name__).exception("Lab worker failed")

    def reset(self):
        with self.lock:
            if self.active:
                raise LabError("Stop the active test before resetting.", 409)
            for d in self.state["devices"]:
                self.disconnect(d)
            revision = self.state.get("revision", 0)
            blueprints = self.state["blueprints"]
            scenarios = self.state.get("scenarios", [])
            test_plans = self.state["testPlans"]
            suites = self.state.get("validationSuites", [])
            self.state = initial_state()
            self.state.update(peripherals=[], blueprints=blueprints)
            self.state["testPlans"] = test_plans
            self.state["validationSuites"] = suites
            self.state["suiteRuns"] = []
            self.state["scenarios"] = scenarios
            self.state["revision"] = revision
            self.save()

    def close(self):
        if self.closed:
            return
        self.stop_event.set()
        if self.worker:
            self.worker.join(timeout=10)
        with self.lock:
            if getattr(self, "suites", None) and self.suites.active:
                self.suites.cancel()
            elif self.active:
                self.cancel()
            for d in self.state["devices"]:
                self.disconnect(d)
            self.save()
            self.connection.close()
            self.closed = True
