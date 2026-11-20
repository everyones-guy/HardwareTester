"""Bounded provenance shared by device runs and role-based system runs."""

import hashlib
import json
import math
import re
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone

MAX_REQUESTS = 256
_request_scope = ContextVar("request_scope", default=None)


def now():
    return datetime.now(timezone.utc).isoformat()


def json_digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def operator_snapshot(actor):
    return {key: actor[key] for key in ("id", "username", "role")} if actor else None


def audit_record(kind, actor, providers, release=None):
    return {
        "schemaVersion": 1,
        "kind": kind,
        "operator": operator_snapshot(actor),
        "release": release,
        "providers": providers,
        "requests": [],
        "droppedRequests": 0,
    }


def release_reference(connection, digest):
    if digest is None:
        return None
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Choose a firmware release by its SHA-256 digest.")
    rows = connection.execute(
        "SELECT name, version, model, architecture FROM firmware_artifacts WHERE digest = ? ORDER BY name, version, model, architecture LIMIT 2",
        (digest,),
    ).fetchall()
    if not rows:
        raise ValueError("The selected firmware release is missing from the library.")
    return {
        "sha256": digest,
        "source": "operator-selected",
        "name": rows[0][0] if len(rows) == 1 else None,
        "version": rows[0][1] if len(rows) == 1 else None,
    }


@contextmanager
def request_scope(sink, **context):
    token = _request_scope.set((sink, context))
    try:
        yield
    finally:
        _request_scope.reset(token)


def append_request(audit, event):
    if len(audit["requests"]) < MAX_REQUESTS:
        audit["requests"].append(event)
    else:
        audit["droppedRequests"] += 1


def exchange(provider, operation, invoke, value=None, *, wire=False):
    context = _request_scope.get()
    if context is None:
        return invoke(str(uuid.uuid4()) if wire else None)
    sink, target = context
    request_id = str(uuid.uuid4())
    event = {
        **target,
        "requestId": request_id,
        "idSource": "wire" if wire else "local",
        "provider": provider,
        "operation": operation,
        "startedAt": now(),
    }
    if value is not None:
        event["requested"] = value
    try:
        result = invoke(request_id)
        event["outcome"] = "succeeded"
        if type(result) in (int, float, bool) and math.isfinite(result):
            event["observed"] = result
        return result
    except Exception as error:
        event.update(outcome="failed", error=str(error)[:300])
        raise
    finally:
        event["finishedAt"] = now()
        if "outcome" in event:
            sink(event)
