"""Run the same role-based system sequence on a modeled or connected bench."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from Hardware_Tester_App.transports import TransportError, create_transport
from Hardware_Tester_App.run_audit import append_request, audit_record, json_digest
from Hardware_Tester_App.system_plan import (
    AdapterBench,
    ModelBench,
    StateMachineBench,
    object_file,
    run_steps,
    validate_plan,
)


class ConnectedBench(AdapterBench):
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
            if (
                roles[role] == "commandRelay"
                and spec.get("approvedCommandRelay") is not True
            ):
                raise ValueError(
                    f"Bind an explicitly approved command relay for {role}."
                )
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
                reference, _ = object_file(args.reference, limit=512 * 1024)
                if reference.get("planSha256") != report[
                    "planSha256"
                ] or not isinstance(reference.get("steps"), list):
                    raise ValueError(
                        "Compare with a completed report for the same plan file."
                    )
            if binding.get("mode") == "modeled":
                bench = (
                    StateMachineBench(roles, binding)
                    if "states" in binding
                    else ModelBench(roles, binding)
                )
            elif binding.get("mode") == "connected" and args.allow_connected:
                connected = bench = ConnectedBench(roles, binding)
                connected.connect()
            else:
                raise ValueError(
                    "Use a modeled bench or explicitly authorize a connected bench."
                )
            providers = [
                {
                    "role": role,
                    "roleKind": kind,
                    "name": role,
                    "adapter": (
                        binding["devices"][role]["adapter"]
                        if connected
                        else "simulation"
                    ),
                }
                for role, kind in roles.items()
            ]
            audit = report["audit"] = audit_record("system", None, providers)
            audit.update(
                planSha256=json_digest(plan),
                bindingSha256=json_digest(binding),
                benchMode=binding["mode"],
            )
            run_steps(
                bench,
                steps,
                report,
                request_sink=lambda event: append_request(audit, event),
            )
            audit["restorationByRole"] = report["restoration"]
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
