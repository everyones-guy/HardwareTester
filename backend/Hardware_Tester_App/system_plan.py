"""Execution and validation shared by Workbench and the local system-plan command."""

import hashlib
import json
import math
import time

from contextlib import contextmanager, nullcontext

from .run_audit import exchange, now, request_scope
from .transports import TransportError

RELAY_ACTIONS = {"fault": "faultRelay", "command": "commandRelay"}


def object_file(path, limit=65536):
    with path.open("rb") as source:
        raw = source.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f"{path.name} exceeds {limit // 1024} KiB.")
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
    if (
        not isinstance(name, str)
        or not name.strip()
        or not name.isprintable()
        or len(name) > 120
    ):
        raise ValueError("Give the system plan a name up to 120 characters.")
    if not isinstance(roles, dict) or not 1 <= len(roles) <= 16:
        raise ValueError("Define 1 to 16 bench roles.")
    if any(
        not isinstance(role, str)
        or not 1 <= len(role) <= 40
        or not role.isprintable()
        or kind not in ("telemetry", "faultRelay", "commandRelay")
        for role, kind in roles.items()
    ):
        raise ValueError(
            "Roles must be telemetry, faultRelay or commandRelay bindings."
        )
    if not isinstance(steps, list) or not 1 <= len(steps) <= 30:
        raise ValueError("Define 1 to 30 system steps.")
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("Each system step must be an object.")
        title, role, action = (step.get(key) for key in ("name", "role", "action"))
        if (
            not isinstance(title, str)
            or not title.strip()
            or not title.isprintable()
            or len(title) > 120
        ):
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
            action not in ("fault", "command")
            or roles[role] != RELAY_ACTIONS[action]
            or type(step.get("active")) is not bool
            or step.keys() != {"name", "role", "action", "active"}
        ):
            raise ValueError(
                f"Use expect for telemetry, or the corresponding relay action with active true/false ({title})."
            )
    return roles, steps


class ModeledBench:
    def read(self, role, timeout=2):
        return exchange("simulation", "read", lambda _: self._read(role))

    def relay_read(self, role):
        return exchange("simulation", "read", lambda _: self._relay_read(role))

    def write_relay(self, role, value):
        return exchange(
            "simulation", "set", lambda _: self._write_relay(role, value), value
        )


class ModelBench(ModeledBench):
    def __init__(self, roles, binding):
        telemetry = {role for role, kind in roles.items() if kind == "telemetry"}
        fault_relays = [role for role, kind in roles.items() if kind == "faultRelay"]
        if len(fault_relays) != 1 or "commandRelay" in roles.values():
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

    def _read(self, role):
        return self.states[self.active][role]

    def _write_relay(self, role, value):
        self.active = value

    def _relay_read(self, role):
        return self.active


class StateMachineBench(ModeledBench):
    """A finite-state machine keyed by verified command and fault relay positions."""

    def __init__(self, roles, binding):
        telemetry = {role for role, kind in roles.items() if kind == "telemetry"}
        relays = set(roles) - telemetry
        self.states = binding.get("states")
        self.current = binding.get("initialState")
        if (
            not isinstance(self.states, dict)
            or not 1 <= len(self.states) <= 32
            or not isinstance(self.current, str)
            or self.current not in self.states
        ):
            raise ValueError(
                "Choose an initial state and define up to 32 model states."
            )
        for name, state in self.states.items():
            if not isinstance(state, dict) or state.keys() != {
                "readings",
                "relays",
                "transitions",
            }:
                raise ValueError(
                    f"State {name} requires readings, relays and transitions."
                )
            readings, outputs, transitions = (
                state[key] for key in ("readings", "relays", "transitions")
            )
            if (
                not isinstance(readings, dict)
                or readings.keys() != telemetry
                or not all(
                    value is None or number(value) for value in readings.values()
                )
            ):
                raise ValueError(
                    f"Use a numeric value or null for each telemetry role in {name}."
                )
            if (
                not isinstance(outputs, dict)
                or outputs.keys() != relays
                or not all(type(value) is bool for value in outputs.values())
            ):
                raise ValueError(f"Use a boolean state for each relay in {name}.")
            if not isinstance(transitions, dict) or transitions.keys() - relays:
                raise ValueError(f"Transitions in {name} must name a relay role.")
            for role, changes in transitions.items():
                if (
                    not isinstance(changes, dict)
                    or changes.keys() - {"on", "off"}
                    or not all(
                        isinstance(target, str) and target in self.states
                        for target in changes.values()
                    )
                ):
                    raise ValueError(
                        f"Transitions for {role} must point to known states."
                    )
        for state in self.states.values():
            for role, changes in state["transitions"].items():
                for position, target in changes.items():
                    outputs = self.states[target]["relays"]
                    if any(
                        value
                        != (
                            (position == "on")
                            if other == role
                            else state["relays"][other]
                        )
                        for other, value in outputs.items()
                    ):
                        raise ValueError(
                            f"A transition for {role} may change only that relay."
                        )

    def _read(self, role):
        value = self.states[self.current]["readings"][role]
        if value is None:
            raise TransportError(
                f"No modeled response from {role} in state {self.current}."
            )
        return value

    def _relay_read(self, role):
        return self.states[self.current]["relays"][role]

    def _write_relay(self, role, value):
        if self._relay_read(role) == value:
            return
        target = (
            self.states[self.current]["transitions"]
            .get(role, {})
            .get("on" if value else "off")
        )
        if target is None:
            raise TransportError(
                f"{role} cannot change position from state {self.current}."
            )
        self.current = target


class AdapterBench:
    def __init__(self, transports):
        self.transports = transports

    def read(self, role, timeout=2):
        transport = self.transports[role]
        with transport_timeout(transport, timeout):
            return transport.read()

    def relay_read(self, role):
        value = self.read(role)
        if value not in (0, 1):
            raise TransportError(f"{role} did not report a binary relay state.")
        return bool(value)

    def write_relay(self, role, value):
        transport = self.transports[role]
        with transport_timeout(transport, 2):
            acknowledged = transport.write(int(value))
        if acknowledged != int(value) or self.relay_read(role) != value:
            raise TransportError(f"{role} did not verify the requested relay state.")


@contextmanager
def transport_timeout(transport, timeout):
    previous = getattr(transport, "timeout", 2)
    transport.timeout = timeout
    try:
        yield
    finally:
        transport.timeout = previous


def run_steps(
    bench,
    steps,
    report,
    *,
    request_sink=None,
    step_finished=None,
    cancelled=lambda: False,
):
    touched = {}
    try:
        for index, step in enumerate(steps):
            if cancelled():
                break
            started = time.monotonic()
            role = step["role"]
            record = {
                "name": step["name"],
                "role": role,
                "action": step["action"],
                "startedAt": now(),
            }
            report["steps"].append(record)
            try:
                with (
                    request_scope(
                        request_sink, phase="step", stepIndex=index, role=role
                    )
                    if request_sink
                    else nullcontext()
                ):
                    execute_step(bench, step, record, touched, started, cancelled)
            except (OSError, TransportError) as error:
                record.update(passed=False, error=str(error))
            finally:
                record["elapsedMs"] = round((time.monotonic() - started) * 1000)
                record["finishedAt"] = now()
            if step_finished:
                step_finished(index, record)
            if not record["passed"]:
                break
    finally:
        for role, value in reversed(list(touched.items())):
            try:
                with (
                    request_scope(request_sink, phase="restoration", role=role)
                    if request_sink
                    else nullcontext()
                ):
                    bench.write_relay(role, value)
                    report["restoration"][role] = (
                        "verified" if bench.relay_read(role) == value else "failed"
                    )
            except (OSError, TransportError) as error:
                report["restoration"][role] = f"failed: {error}"


def execute_step(bench, step, record, touched, started, cancelled):
    role = step["role"]
    if step["action"] in RELAY_ACTIONS:
        if role not in touched:
            position = bench.relay_read(role)
            if step["action"] == "fault" and position:
                raise TransportError(
                    f"{role} is already injecting a fault. Check the bench before running."
                )
            if cancelled():
                raise TransportError("Cancellation requested before the relay command.")
            touched[role] = position
        record["expected"] = step["active"]
        bench.write_relay(role, step["active"])
        record["actual"] = bench.relay_read(role)
        record["passed"] = record["actual"] == step["active"]
        return

    record.update(expected=step["value"], tolerance=step["tolerance"])
    deadline = started + step["withinSeconds"]

    def matches(value):
        return math.isclose(value, step["value"], rel_tol=0, abs_tol=step["tolerance"])

    while not cancelled() and (remaining := deadline - time.monotonic()) > 0:
        actual = bench.read(role, min(2, remaining))
        record["actual"] = actual
        if matches(actual):
            break
        time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    record["passed"] = (
        "actual" in record
        and matches(record["actual"])
        and time.monotonic() <= deadline
    )
