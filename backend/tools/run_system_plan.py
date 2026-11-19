"""Run the same role-based system sequence on a modeled or connected bench."""

import argparse
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from Hardware_Tester_App.transports import TransportError, create_transport


def object_file(path):
    with path.open("rb") as source:
        raw = source.read(65537)
    if len(raw) > 65536:
        raise ValueError(f"{path.name} exceeds 64 KiB.")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return value, hashlib.sha256(raw).hexdigest()


def number(value):
    return type(value) in (int, float) and -1_000_000 <= value <= 1_000_000


def validate_plan(plan):
    if plan.keys() != {"name", "roles", "steps"}:
        raise ValueError("A system plan contains name, roles, and steps.")
    roles, steps = plan.get("roles"), plan.get("steps")
    name = plan.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise ValueError("Give the system plan a name up to 120 characters.")
    if not isinstance(roles, dict) or not 1 <= len(roles) <= 16:
        raise ValueError("Define 1 to 16 bench roles.")
    if any(
        not 1 <= len(role) <= 40 or kind not in ("telemetry", "faultRelay")
        for role, kind in roles.items()
    ):
        raise ValueError("Roles must be named telemetry or faultRelay bindings.")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 30:
        raise ValueError("Define 1 to 30 system steps.")
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("Each system step must be an object.")
        title, role, action = (step.get(key) for key in ("name", "role", "action"))
        if not isinstance(title, str) or not title.strip() or len(title) > 120:
            raise ValueError("Name each system step (up to 120 characters).")
        if not isinstance(role, str) or role not in roles:
            raise ValueError(f"Choose a valid role for {title}.")
        if action == "expect" and roles[role] == "telemetry":
            if step.keys() != {
                "name",
                "role",
                "action",
                "value",
                "tolerance",
                "withinSeconds",
            }:
                raise ValueError(f"Check the expectation fields for {title}.")
            expected, tolerance, seconds = (
                step.get(key) for key in ("value", "tolerance", "withinSeconds")
            )
            if not all(
                number(value) for value in (expected, tolerance, seconds)
            ) or not (tolerance >= 0 and 0.1 <= seconds <= 30):
                raise ValueError(
                    f"Use a finite value and tolerance and 0.1–30 seconds for {title}."
                )
        elif (
            action != "fault"
            or roles[role] != "faultRelay"
            or type(step.get("active")) is not bool
            or step.keys() != {"name", "role", "action", "active"}
        ):
            raise ValueError(
                f"Use expect for telemetry and fault with active true/false for a fault relay ({title})."
            )
    return roles, steps


class ModelBench:
    def __init__(self, roles, binding):
        telemetry = {role for role, kind in roles.items() if kind == "telemetry"}
        fault_relays = [role for role, kind in roles.items() if kind == "faultRelay"]
        if len(fault_relays) != 1:
            raise ValueError("A modeled bench needs exactly one sensor fault relay.")
        self.states = {False: binding.get("normal"), True: binding.get("sensorFailed")}
        for state in self.states.values():
            if (
                not isinstance(state, dict)
                or state.keys() != telemetry
                or not all(map(number, state.values()))
            ):
                raise ValueError(
                    "Each model state must include a numeric reading for every telemetry role."
                )
        self.active = False

    def read(self, role, timeout=2):
        return self.states[self.active][role]

    def write_fault(self, role, value):
        self.active = value

    def fault_read(self, role):
        return self.active


class ConnectedBench:
    def __init__(self, roles, binding):
        devices = binding.get("devices")
        if not isinstance(devices, dict) or devices.keys() != roles.keys():
            raise ValueError(
                "Bind every required role, including the approved fault relay."
            )
        self.transports = {}
        endpoints = set()
        for role, spec in devices.items():
            if not isinstance(spec, dict) or not isinstance(spec.get("endpoint"), str):
                raise ValueError(f"Set an endpoint for {role}.")
            adapter, endpoint = spec.get("adapter"), spec["endpoint"]
            if not endpoint or endpoint in endpoints:
                raise ValueError("Each connected role needs its own endpoint.")
            endpoints.add(endpoint)
            if adapter == "mqtt":
                uri = urlsplit(endpoint)
                if (
                    uri.scheme != "mqtt"
                    or not uri.hostname
                    or not uri.path.strip("/")
                    or (
                        uri.username is not None
                        or uri.password is not None
                        or uri.query
                        or uri.fragment
                        or any(character in uri.path for character in "#+\0")
                    )
                ):
                    raise ValueError(
                        f"Use a concrete private-bench MQTT topic for {role}."
                    )
                _ = (
                    uri.port
                )  # Reject malformed or out-of-range ports before connecting.
            elif adapter != "serial":
                raise ValueError(f"Choose mqtt or serial for {role}.")
            baudrate = spec.get("baudrate", 115200)
            if type(baudrate) is not int or not 1200 <= baudrate <= 4_000_000:
                raise ValueError(f"Set a valid baud rate for {role}.")
            if (
                roles[role] == "faultRelay"
                and spec.get("approvedFaultRelay") is not True
            ):
                raise ValueError(f"Bind an explicitly approved fault relay for {role}.")
            self.transports[role] = create_transport(
                dict(adapter=adapter, endpoint=endpoint, baudrate=baudrate)
            )
        self.opened = []

    def connect(self):
        for transport in self.transports.values():
            self.opened.append(transport)
            transport.connect()

    def close(self):
        errors = []
        for transport in reversed(self.opened):
            try:
                transport.close()
            except (OSError, TransportError) as exc:
                errors.append(str(exc))
        return errors

    def read(self, role, timeout=2):
        transport = self.transports[role]
        transport.timeout = timeout
        return transport.read()

    def fault_read(self, role):
        value = self.read(role)
        if value not in (0, 1):
            raise TransportError(f"{role} did not report its fault relay state.")
        return bool(value)

    def write_fault(self, role, value):
        transport = self.transports[role]
        transport.timeout = 2
        if transport.write(int(value)) != int(value) or self.fault_read(role) != value:
            raise TransportError(
                f"{role} did not verify the requested fault relay state."
            )


def run_steps(bench, steps, report):
    touched = {}
    try:
        for step in steps:
            started = time.monotonic()
            role = step["role"]
            record = {"name": step["name"], "role": role, "action": step["action"]}
            report["steps"].append(record)
            try:
                if step["action"] == "fault":
                    if role not in touched:
                        if bench.fault_read(role):
                            raise TransportError(
                                f"{role} is already injecting a fault. Check the bench before running."
                            )
                        touched[role] = False
                    record["expected"] = step["active"]
                    bench.write_fault(role, step["active"])
                    record["actual"] = bench.fault_read(role)
                    record["passed"] = record["actual"] == step["active"]
                else:
                    record.update(expected=step["value"], tolerance=step["tolerance"])
                    deadline = started + step["withinSeconds"]
                    while (remaining := deadline - time.monotonic()) > 0:
                        actual = bench.read(role, min(2, remaining))
                        record["actual"] = actual
                        if math.isclose(
                            actual, step["value"], rel_tol=0, abs_tol=step["tolerance"]
                        ):
                            break
                        time.sleep(min(0.05, max(0, deadline - time.monotonic())))
                    record["passed"] = (
                        "actual" in record
                        and math.isclose(
                            record["actual"],
                            step["value"],
                            rel_tol=0,
                            abs_tol=step["tolerance"],
                        )
                        and time.monotonic() <= deadline
                    )
            except (OSError, TransportError) as error:
                record.update(passed=False, error=str(error))
            finally:
                record["elapsedMs"] = round((time.monotonic() - started) * 1000)
            if not record["passed"]:
                break
    finally:
        for role, value in reversed(list(touched.items())):
            try:
                bench.write_fault(role, value)
                report["restoration"][role] = (
                    "verified" if bench.fault_read(role) == value else "failed"
                )
            except (OSError, TransportError) as error:
                report["restoration"][role] = f"failed: {error}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("plan", "bench", "report"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument(
        "--reference",
        type=Path,
        help="Compare against a report from the same plan file",
    )
    parser.add_argument("--allow-connected", action="store_true")
    args = parser.parse_args()
    report = {
        "schemaVersion": 1,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "steps": [],
        "restoration": {},
        "status": "started",
    }
    with args.report.open("x", encoding="utf-8") as output:
        output.write(json.dumps(report, indent=2) + "\n")
        output.flush()
        connected = None
        reference = None
        try:
            plan, report["planSha256"] = object_file(args.plan)
            binding, report["benchSha256"] = object_file(args.bench)
            roles, steps = validate_plan(plan)
            report["plan"] = plan
            report["benchMode"] = binding.get("mode")
            if args.reference:
                reference, _ = object_file(args.reference)
                if reference.get("planSha256") != report[
                    "planSha256"
                ] or not isinstance(reference.get("steps"), list):
                    raise ValueError(
                        "Compare with a completed report for the same plan file."
                    )
            if binding.get("mode") == "modeled":
                bench = ModelBench(roles, binding)
            elif binding.get("mode") == "connected" and args.allow_connected:
                connected = bench = ConnectedBench(roles, binding)
                connected.connect()
            else:
                raise ValueError(
                    "Use a modeled bench or explicitly authorize a connected bench."
                )
            run_steps(bench, steps, report)
            report["status"] = (
                "recoveryRequired"
                if any(value != "verified" for value in report["restoration"].values())
                else (
                    "passed"
                    if len(report["steps"]) == len(steps)
                    and all(step["passed"] for step in report["steps"])
                    else "failed"
                )
            )
            if reference is not None:
                report["comparison"] = {
                    "referenceMode": reference.get("benchMode"),
                    "referenceStatus": reference.get("status"),
                    "steps": [
                        {
                            "name": current["name"],
                            "referenceActual": previous.get("actual"),
                            "actual": current.get("actual"),
                            "referencePassed": previous.get("passed"),
                            "passed": current["passed"],
                        }
                        for current, previous in zip(
                            report["steps"], reference["steps"]
                        )
                        if isinstance(previous, dict)
                        and previous.get("name") == current["name"]
                    ],
                }
        except (OSError, ValueError, TransportError) as error:
            report.update(status="blocked", error=str(error))
        except KeyboardInterrupt:
            report["status"] = "interrupted"
        finally:
            if connected:
                close_errors = connected.close()
                if close_errors:
                    report["closeErrors"] = close_errors
            report["finishedAt"] = datetime.now(timezone.utc).isoformat()
            output.seek(0)
            output.truncate()
            output.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['status']}: {args.report}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
