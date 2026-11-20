"""Launch the shared role-based system runner under Workbench bench ownership."""

import threading
import uuid

from flask import g, jsonify, request

from .lab import LabError, now
from .run_audit import append_request, audit_record, json_digest, release_reference
from .system_plan import (
    AdapterBench,
    ModelBench,
    StateMachineBench,
    run_steps,
    validate_plan,
)


def prepare_bench(lab, roles, binding):
    mode = binding.get("mode")
    if mode == "modeled":
        model = StateMachineBench if "states" in binding else ModelBench
        return model(roles, binding), [
            {"role": role, "roleKind": kind, "name": role, "adapter": "simulation"}
            for role, kind in roles.items()
        ]
    if mode != "connected" or not lab.allow_hardware:
        raise LabError(
            "Choose a modeled bench or enable connected hardware for this workspace.",
            403,
        )
    if (
        binding.keys() != {"mode", "devices"}
        or not isinstance(binding["devices"], dict)
        or binding["devices"].keys() != roles.keys()
    ):
        raise ValueError("Bind each role to a registered Workbench device ID.")
    transports, providers, endpoints = {}, [], set()
    approvals = {
        "commandRelay": "approvedCommandRelay",
        "faultRelay": "approvedFaultRelay",
    }
    for role, kind in roles.items():
        spec = binding["devices"][role]
        approval = approvals.get(kind)
        fields = {"deviceId", approval} if approval else {"deviceId"}
        if (
            not isinstance(spec, dict)
            or spec.keys() != fields
            or not isinstance(spec["deviceId"], str)
        ):
            raise ValueError(
                f"Bind {role} to a registered device and supply its required relay approval."
            )
        if approval and spec[approval] is not True:
            raise ValueError(
                f"The operator must explicitly approve the relay bound to {role}."
            )
        device = lab.device(spec["deviceId"])
        adapter = device["adapter"]
        if (
            adapter not in {"mqtt", "serial"}
            or not device["connected"]
            or device["id"] not in lab.adapters
        ):
            raise LabError(
                f"Connect the registered MQTT or serial device for {role} before running.",
                409,
            )
        if approval and (device["kind"] != "relay" or device.get("safetyWarning")):
            raise LabError(
                f"{role} requires a relay with no pending safety warning.", 409
            )
        address = adapter, device["endpoint"]
        if address in endpoints:
            raise ValueError("Each system role needs a distinct device endpoint.")
        endpoints.add(address)
        transports[role] = lab.adapters[device["id"]]
        providers.append(
            {
                "role": role,
                "roleKind": kind,
                "name": device["name"],
                "adapter": adapter,
                "deviceId": device["id"],
            }
        )
    return AdapterBench(transports), providers


def execute(lab, active, bench, steps):
    run = active["run"]
    audit = run["audit"]
    raw = {"steps": [], "restoration": {}}

    def record_request(event):
        with lab.lock:
            append_request(audit, event)

    def record_step(index, record):
        with lab.lock:
            step = run["steps"][index]
            step.update(
                status="passed" if record["passed"] else "failed",
                startedAt=record["startedAt"],
                finishedAt=record["finishedAt"],
                durationMs=record["elapsedMs"],
                detail=(
                    record.get("error")
                    or (
                        f"{record['role']}: expected result observed."
                        if record["passed"]
                        else f"{record['role']}: expected result was not observed before the deadline."
                    )
                )[:300],
            )
            if "expected" in record:
                value = record["expected"]
                step["expected"] = {
                    "value": int(value) if type(value) is bool else value,
                    "tolerance": record.get("tolerance", 0),
                }
            if "actual" in record:
                value = record["actual"]
                step["observed"] = int(value) if type(value) is bool else value
            lab.log(
                step["detail"],
                "success" if record["passed"] else "error",
                run_id=run["id"],
            )
            lab.save()

    issue = None
    try:
        run_steps(
            bench,
            steps,
            raw,
            request_sink=record_request,
            step_finished=record_step,
            cancelled=active["cancel"].is_set,
        )
    except Exception as error:
        issue = str(error)[:300]
    with lab.lock:
        restored = {role: value[:300] for role, value in raw["restoration"].items()}
        audit["restorationByRole"] = restored
        failed = {role for role, value in restored.items() if value != "verified"}
        for provider in audit["providers"]:
            if provider["role"] in failed and "deviceId" in provider:
                device = lab.device(provider["deviceId"])
                device["safetyWarning"] = (
                    "System run could not confirm relay restoration. Inspect the output before another run."
                )
        if issue:
            audit["error"] = issue
            lab.log(issue, "error", run_id=run["id"])
        status = "failed"
        if active["cancel"].is_set():
            status = "cancelled"
        elif (
            not failed
            and not issue
            and all(step["status"] == "passed" for step in run["steps"])
        ):
            status = "passed"
        run.update(
            status=status,
            finishedAt=now(),
            restoration=(
                "failed" if failed else "restored" if restored else "not-needed"
            ),
        )
        lab.log(
            f"System run {run['plan']}: {status}.",
            "success" if status == "passed" else "error",
            run_id=run["id"],
        )
        lab.active = None
        lab.save()


def start_system(lab, payload, actor):
    with lab.lock:
        if lab.active or lab.suites.active:
            raise LabError("The bench already has an active test.", 409)
        if (
            not isinstance(payload, dict)
            or payload.keys() - {"plan", "bench", "releaseSha256"}
            or not isinstance(payload.get("plan"), dict)
            or not isinstance(payload.get("bench"), dict)
        ):
            raise LabError(
                "Provide a system plan and bench binding, with an optional firmware digest."
            )
        plan, binding = payload["plan"], payload["bench"]
        try:
            roles, steps = validate_plan(plan)
            plan_sha, binding_sha = json_digest(plan), json_digest(binding)
            release = release_reference(lab.connection, payload.get("releaseSha256"))
            bench, providers = prepare_bench(lab, roles, binding)
        except (ValueError, RecursionError) as error:
            raise LabError(str(error)) from error
        audit = audit_record("system", actor, providers, release)
        audit.update(
            planSha256=plan_sha, bindingSha256=binding_sha, benchMode=binding["mode"]
        )
        run = {
            "id": str(uuid.uuid4()),
            "deviceId": f"system:{binding_sha}",
            "deviceName": (
                "Modeled system bench"
                if binding["mode"] == "modeled"
                else "Connected system bench"
            ),
            "planId": f"system:{plan_sha}",
            "plan": plan["name"],
            "startedAt": now(),
            "status": "running",
            "audit": audit,
            "steps": [
                {
                    "name": step["name"][:100],
                    "status": "pending",
                    "detail": "Waiting to execute",
                }
                for step in steps
            ],
        }
        if audit["operator"]:
            run["startedBy"] = audit["operator"]
        active = {
            "system": True,
            "run": run,
            "device": {"id": run["deviceId"]},
            "cancel": threading.Event(),
        }
        worker = threading.Thread(
            target=execute,
            args=(lab, active, bench, steps),
            name="system-plan",
            daemon=True,
        )
        active["worker"] = worker
        lab.state["runs"].insert(0, run)
        del lab.state["runs"][100:]
        lab.active = active
        lab.log(f"Started system plan {run['plan']}.", run_id=run["id"])
        lab.save()
        worker.start()
        return run["id"]


def register_system_runs(app, lab):
    @app.post("/api/lab/system-runs")
    def launch_system_run():
        identity = start_system(
            lab, request.get_json(), getattr(g, "workbench_user", None)
        )
        return jsonify(state=lab.snapshot(), runId=identity), 202
