"""Authenticated storage for immutable, checksummed binary firmware."""

import hashlib
import hmac
import json
import os
import re
import tempfile
from pathlib import Path

from flask import g, jsonify, request, send_file

from .lab import LabError, now
from .pi_inventories import text_value

FIRMWARE_API = "/api/lab/firmware"
FIRMWARE_UPLOAD_LIMIT = 16 * 1024 * 1024
SHA256 = re.compile(r"[a-f0-9]{64}")


def parse_manifest(raw):
    try:
        manifest = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise LabError("Firmware metadata must be a JSON object.") from exc
    labels = {
        "name": "Firmware name",
        "version": "Firmware version",
        "model": "Target board model and revision",
        "architecture": "Target architecture",
        "sha256": "SHA-256 digest",
    }
    if not isinstance(manifest, dict) or manifest.keys() != labels.keys():
        raise LabError("Specify name, version, model, architecture, and sha256.")
    values = {key: text_value(manifest[key], label) for key, label in labels.items()}
    values["sha256"] = values["sha256"].lower()
    if not SHA256.fullmatch(values["sha256"]):
        raise LabError("Enter the expected SHA-256 as 64 hexadecimal characters.")
    return values


def register_firmware(app, lab):
    database = Path(app.config["LAB_DB_PATH"]).resolve()
    storage = database.with_name(database.name + ".firmware")
    with lab.lock, lab.connection:
        lab.connection.execute(
            "CREATE TABLE IF NOT EXISTS firmware_artifacts ("
            "digest TEXT NOT NULL, name TEXT NOT NULL, version TEXT NOT NULL, "
            "model TEXT NOT NULL, architecture TEXT NOT NULL, metadata TEXT NOT NULL, "
            "PRIMARY KEY (name, version, model, architecture))"
        )

    @app.get(FIRMWARE_API)
    def firmware_library():
        inventory_id = request.args.get("inventoryId")
        with lab.lock:
            rows = lab.connection.execute(
                "SELECT metadata FROM firmware_artifacts ORDER BY rowid DESC"
            ).fetchall()
            inventory = None
            if inventory_id is not None:
                row = lab.connection.execute(
                    "SELECT inventory FROM pi_inventories WHERE id = ?", (inventory_id,)
                ).fetchone()
                if row is None:
                    raise LabError("Raspberry Pi inventory not found.", 404)
                inventory = json.loads(row[0])
        artifacts = [json.loads(row[0]) for row in rows]
        if inventory is not None:
            for artifact in artifacts:
                differences = [
                    field
                    for field in ("model", "architecture")
                    if artifact[field] != inventory[field]
                ]
                artifact["compatibility"] = (
                    "mismatch" if differences else "declaredMatch"
                )
                artifact["differences"] = differences
        return jsonify(artifacts=artifacts)

    @app.post(FIRMWARE_API)
    def upload_firmware():
        if (
            set(request.form) != {"metadata"}
            or len(request.form.getlist("metadata")) != 1
            or set(request.files) != {"binary"}
            or len(request.files.getlist("binary")) != 1
        ):
            raise LabError("Send one firmware binary and its metadata.")
        artifact = parse_manifest(request.form["metadata"])
        binary = request.files["binary"]
        if not binary.filename or not binary.filename.lower().endswith(".bin"):
            raise LabError("Upload firmware in .bin format.")
        expected = artifact["sha256"]
        hash_result = hashlib.sha256()
        size = 0
        storage.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=storage, delete=False) as destination:
                temporary = Path(destination.name)
                while chunk := binary.stream.read(64 * 1024):
                    size += len(chunk)
                    if size > FIRMWARE_UPLOAD_LIMIT:
                        raise LabError("Firmware binaries must be at most 16 MiB.", 413)
                    hash_result.update(chunk)
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
            if not size:
                raise LabError("The firmware binary is empty.")
            if not hmac.compare_digest(hash_result.hexdigest(), expected):
                raise LabError(
                    "The firmware binary does not match its expected SHA-256."
                )

            actor = getattr(g, "workbench_user", None)
            artifact.update(
                schemaVersion=1,
                format="bin",
                sizeBytes=size,
                uploadedAt=now(),
                uploadedBy=actor["username"] if actor else None,
            )
            with lab.lock, lab.connection:
                manifest_key = tuple(
                    artifact[key]
                    for key in ("name", "version", "model", "architecture")
                )
                existing = lab.connection.execute(
                    "SELECT digest, metadata FROM firmware_artifacts WHERE "
                    "name = ? AND version = ? AND model = ? AND architecture = ?",
                    manifest_key,
                ).fetchone()
                if existing and existing[0] != expected:
                    raise LabError(
                        "This target and firmware version already have another digest.",
                        409,
                    )
                final = storage / f"{expected}.bin"
                if not final.exists():
                    os.replace(temporary, final)
                if existing:
                    return jsonify(artifact=json.loads(existing[1]))
                lab.connection.execute(
                    "INSERT INTO firmware_artifacts "
                    "(digest, name, version, model, architecture, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (expected, *manifest_key, json.dumps(artifact)),
                )
            return jsonify(artifact=artifact), 201
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @app.get(FIRMWARE_API + "/<digest>/binary")
    def download_firmware(digest):
        if not SHA256.fullmatch(digest):
            raise LabError("Firmware was not found.", 404)
        with lab.lock:
            exists = lab.connection.execute(
                "SELECT 1 FROM firmware_artifacts WHERE digest = ?", (digest,)
            ).fetchone()
        artifact = storage / f"{digest}.bin"
        if not exists or not artifact.is_file():
            raise LabError("Firmware was not found.", 404)
        return send_file(
            artifact, as_attachment=True, mimetype="application/octet-stream"
        )
