"""Saved, simulation-only validation suites coordinated by the lab worker."""

import copy
import uuid
from flask import g, jsonify, request
from .lab import LabError, PLANS, now

RESTORED = (
    "scenario",
    "scenarioCursor",
    "scenarioOutput",
    "fault",
    "value",
    "enabled",
    "lastError",
    "safetyWarning",
)


def normalize(data):
    if not isinstance(data, dict):
        raise LabError("Use a JSON object.")
    name, kind, plan = data.get("name"), data.get("kind"), data.get("planId")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise LabError("Suite name must contain 1–100 characters.")
    if (
        kind not in ("temperature", "valve", "relay")
        or not isinstance(plan, str)
        or not plan
    ):
        raise LabError("Choose a device profile and test plan.")
    description = data.get("description", "")
    if not isinstance(description, str) or len(description) > 2000:
        raise LabError("Description must be text up to 2000 characters.")
    cases = data.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 10:
        raise LabError("A suite requires 1–10 cases.")
    normalized = []
    for case in cases:
        if not isinstance(case, dict):
            raise LabError("Every case must be an object.")
        label, scenario, expected = (
            case.get("name"),
            case.get("scenarioId"),
            case.get("expected"),
        )
        if (
            not isinstance(label, str)
            or not 1 <= len(label.strip()) <= 100
            or not isinstance(scenario, str)
            or not scenario
        ):
            raise LabError("Every case requires a name and saved scenario.")
        if (
            not isinstance(expected, list)
            or not 1 <= len(expected) <= 3
            or any(e not in ("passed", "failed") for e in expected)
        ):
            raise LabError("Each case requires 1–3 expected pass/fail outcomes.")
        normalized.append(
            {"name": label.strip(), "scenarioId": scenario, "expected": expected[:]}
        )
    if sum(len(c["expected"]) for c in normalized) > 20:
        raise LabError("A suite supports at most 20 test attempts.")
    return dict(
        name=name.strip(),
        kind=kind,
        planId=plan,
        description=description,
        cases=normalized,
    )


class SuiteRunner:
    def __init__(self, lab):
        self.lab = lab
        self.active = None
        lab.state.setdefault("validationSuites", [])
        lab.state.setdefault("suiteRuns", [])
        for report in lab.state["suiteRuns"]:
            if report["status"] == "running":
                self.active = report
                self.tick(launch=False)
                self.finish(
                    "cancelled", "Server restarted; interrupted suite was cancelled."
                )
        lab.save()

    def find(self, collection, identity):
        result = next(
            (s for s in self.lab.state[collection] if s["id"] == identity), None
        )
        if result is None:
            raise LabError("Validation suite or report not found.", 404)
        return result

    def resolve(self, suite):
        if suite["planId"] not in PLANS:
            plan = self.find("testPlans", suite["planId"])
            if plan["kind"] != suite["kind"]:
                raise LabError("Plan profile must match the suite.", 409)
        else:
            plan = {
                "id": suite["planId"],
                "version": 1,
                "name": PLANS[suite["planId"]][0],
            }
        scenarios = [
            copy.deepcopy(self.find("scenarios", c["scenarioId"]))
            for c in suite["cases"]
        ]
        return copy.deepcopy(plan), scenarios

    def start(self, identity, device_id, actor=None):
        lab = self.lab
        if lab.active or self.active:
            raise LabError("Stop the active test or suite first.", 409)
        suite = copy.deepcopy(self.find("validationSuites", identity))
        device = lab.device(device_id)
        if device["adapter"] != "simulation":
            raise LabError("Validation suites run on simulated devices only.", 403)
        if device["kind"] != suite["kind"] or not device["connected"]:
            raise LabError("Connect a simulated device with the matching profile.", 409)
        plan, scenarios = self.resolve(suite)
        report = dict(
            id=str(uuid.uuid4()),
            suite=suite,
            plan=plan,
            device=copy.deepcopy(device),
            peripherals=copy.deepcopy(
                [p for p in lab.state["peripherals"] if p["device_id"] == device_id]
            ),
            startedAt=now(),
            status="running",
            cases=[
                dict(c, scenario=s, attempts=[], status="pending")
                for c, s in zip(suite["cases"], scenarios)
            ],
        )
        if actor:
            report["startedBy"] = {k: actor[k] for k in ("id", "username", "role")}
        self.active = report
        lab.state["suiteRuns"].insert(0, report)
        del lab.state["suiteRuns"][10:]
        self.tick()
        lab.save()
        return report["id"]

    def finish(self, status, detail=""):
        report, lab = self.active, self.lab
        if not report:
            return
        original = report["device"]
        device = next(
            (d for d in lab.state["devices"] if d["id"] == original["id"]), None
        )
        if device:
            for key in RESTORED:
                if key in original:
                    device[key] = copy.deepcopy(original[key])
                else:
                    device.pop(key, None)
        for case in report["cases"]:
            if case["status"] in ("pending", "running"):
                case["status"] = "cancelled" if status == "cancelled" else "error"
        report.update(
            status=status, finishedAt=now(), detail=detail, restoration="restored"
        )
        self.active = None
        lab.log(
            f"Validation suite {report['suite']['name']}: {status}.",
            "success" if status == "passed" else "error",
            device_id=original["id"],
        )
        lab.save()

    def cancel(self):
        if not self.active:
            raise LabError("No validation suite is running.", 409)
        if self.lab.active:
            self.lab.cancel()
        self.tick(launch=False)
        self.finish(
            "cancelled", "Suite stopped; original simulation settings restored."
        )

    def tick(self, launch=True):
        report, lab = self.active, self.lab
        if not report or lab.active:
            return
        try:
            case = next(
                (c for c in report["cases"] if c["status"] in ("pending", "running")),
                None,
            )
            if case is None:
                self.finish(
                    "passed"
                    if all(c["status"] == "passed" for c in report["cases"])
                    else "failed"
                )
                return
            if case.get("runId"):
                run = self.find("runs", case.pop("runId"))
                expected = case["expected"][len(case["attempts"])]
                matched = (
                    run["status"] == expected and run.get("restoration") != "failed"
                )
                case["attempts"].append(
                    dict(expected=expected, matched=matched, run=copy.deepcopy(run))
                )
                if run["status"] == "cancelled":
                    self.finish(
                        "cancelled", "Test cancelled; remaining cases were not run."
                    )
                    return
                if len(case["attempts"]) == len(case["expected"]):
                    case["status"] = (
                        "passed"
                        if all(a["matched"] for a in case["attempts"])
                        else "failed"
                    )
                    lab.save()
                    if launch:
                        self.tick()
                    return
            if not launch:
                return
            device = lab.device(report["device"]["id"])
            if case["status"] == "pending":
                baseline = report["device"].get(
                    "scenarioOutput", report["device"]["value"]
                )
                maximum = {"temperature": 50, "valve": 100, "relay": 1}[device["kind"]]
                if not 0 <= baseline <= maximum:
                    baseline = 24 if device["kind"] == "temperature" else 0
                device.update(
                    scenario=copy.deepcopy(case["scenario"]),
                    scenarioCursor=0,
                    scenarioOutput=baseline,
                    value=baseline,
                    enabled=report["device"]["enabled"],
                    fault="none",
                    lastError=None,
                )
                case["status"] = "running"
            case["runId"] = lab.start(
                device["id"], report["suite"]["planId"], actor=report.get("startedBy")
            )
            lab.active["run"]["suiteRunId"] = report["id"]
            lab.save()
        except Exception as error:
            if lab.active:
                lab.cancel()
            self.finish("error", str(error)[:300])


def register_suites(app, lab):
    lab.suites = runner = SuiteRunner(lab)

    @app.route("/api/lab/validation-suites", methods=["POST"])
    @app.route("/api/lab/validation-suites/<identity>", methods=["PUT", "DELETE"])
    @app.post("/api/lab/validation-suites/<identity>/run")
    def suites(identity=None):
        with lab.lock:
            data = request.get_json()
            if not isinstance(data, dict):
                raise LabError("Use a JSON object.")
            if lab.active or runner.active:
                raise LabError("Stop the active test or suite first.", 409)
            extra = {}
            if request.path.endswith("/run"):
                extra["suiteRunId"] = runner.start(
                    identity, data.get("deviceId"), getattr(g, "workbench_user", None)
                )
            else:
                item = runner.find("validationSuites", identity) if identity else None
                if item and (
                    type(data.get("version")) is not int
                    or data["version"] != item["version"]
                ):
                    raise LabError(
                        "Suite changed. Reload before saving or deleting.", 409
                    )
                if request.method == "DELETE":
                    lab.state["validationSuites"].remove(item)
                else:
                    normalized = normalize(data)
                    runner.resolve(normalized)
                    if item:
                        item.update(normalized, version=item["version"] + 1)
                    else:
                        if len(lab.state["validationSuites"]) >= 100:
                            raise LabError("The library supports 100 suites.", 409)
                        item = dict(normalized, id=str(uuid.uuid4()), version=1)
                        lab.state["validationSuites"].append(item)
                    extra["suiteId"] = item["id"]
                lab.save()
            return jsonify(state=lab.snapshot(), **extra)

    @app.post("/api/lab/suite-runs/cancel")
    def cancel_suite():
        with lab.lock:
            runner.cancel()
            return jsonify(state=lab.snapshot())
