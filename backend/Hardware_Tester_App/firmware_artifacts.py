"""Authenticated firmware storage, static inventory, and captured-board pairing."""

import hashlib
import hmac
import json
import os
import re
import tempfile
from pathlib import Path

from flask import g, jsonify, request, send_file

from .firmware_inventory import inspect_firmware
from .lab import LabError, now
from .pi_inventories import text_value
from .ui_catalogs import save_ui_catalog
from .utils.firmware_utils import FirmwareArchiveError

FIRMWARE_API = "/api/lab/firmware"
FIRMWARE_UPLOAD_LIMIT = 16 * 1024 * 1024
SHA256 = re.compile(r"[a-f0-9]{64}")
ARCH_ALIASES = {"arm64": "aarch64", "amd64": "x86_64", "x86-64": "x86_64"}
BOARD_ABIS = {
    "aarch64": ("aarch64", 64, "little"),
    "armv6l": ("arm", 32, "little"),
    "armv7l": ("arm", 32, "little"),
    "armv8l": ("arm", 32, "little"),
    "arm": ("arm", 32, "little"),
    "x86_64": ("x86_64", 64, "little"),
}


def normalized_architecture(value):
    name = value.casefold()
    return ARCH_ALIASES.get(name, name)


def compare_target(artifact, capture):
    differences = []
    if artifact["model"] != capture["model"]:
        differences.append("model")
    target_arch = normalized_architecture(capture["architecture"])
    if normalized_architecture(artifact["architecture"]) != target_arch:
        differences.append("architecture")
    if differences:
        return "mismatch", differences
    summary = artifact.get("inventory") or {}
    observed = {
        (abi["architecture"], abi["bits"], abi["endianness"])
        for abi in summary.get("elfAbis", [])
    }
    known = {abi for abi in observed if abi[0] != "unknown"}
    expected = BOARD_ABIS.get(target_arch)
    if expected and known and expected not in known:
        return "mismatch", ["observed ELF architecture"]
    if (
        summary.get("unknownElfCount")
        or len(known) > 1
        or (known and expected is None)
        or target_arch == "unknown"
    ):
        return "reviewRequired", ["mixed, unknown, or unsupported ABI"]
    return ("inventoryMatch" if known else "declaredMatch"), []


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
        lab.connection.execute(
            "CREATE TABLE IF NOT EXISTS firmware_inspections ("
            "digest TEXT PRIMARY KEY, format TEXT NOT NULL, summary TEXT NOT NULL, inventory TEXT NOT NULL)"
        )

    @app.get(FIRMWARE_API)
    def firmware_library():
        inventory_id = request.args.get("inventoryId")
        with lab.lock:
            rows = lab.connection.execute(
                "SELECT a.metadata, i.format, i.summary FROM firmware_artifacts a "
                "LEFT JOIN firmware_inspections i ON a.digest = i.digest ORDER BY a.rowid DESC"
            ).fetchall()
            inventory = None
            if inventory_id is not None:
                row = lab.connection.execute(
                    "SELECT inventory FROM pi_inventories WHERE id = ?", (inventory_id,)
                ).fetchone()
                if row is None:
                    raise LabError("Raspberry Pi inventory not found.", 404)
                inventory = json.loads(row[0])
        artifacts = []
        for metadata, package_format, summary in rows:
            artifact = json.loads(metadata)
            if artifact["format"] == package_format:
                artifact["inventory"] = json.loads(summary)
            if inventory is not None:
                artifact["compatibility"], artifact["differences"] = compare_target(
                    artifact, inventory
                )
            artifacts.append(artifact)
        return jsonify(artifacts=artifacts)

    @app.get(FIRMWARE_API + "/<digest>/inventory")
    def firmware_inventory(digest):
        if not SHA256.fullmatch(digest):
            raise LabError("Firmware inventory was not found.", 404)
        with lab.lock:
            row = lab.connection.execute(
                "SELECT inventory FROM firmware_inspections WHERE digest = ?", (digest,)
            ).fetchone()
        if row is None:
            raise LabError(
                "Firmware inventory was not found. Reupload an older binary to inspect it.",
                404,
            )
        return jsonify(inventory=json.loads(row[0]))

    @app.post(FIRMWARE_API)
    def upload_firmware():
        if (
            set(request.form) != {"metadata"}
            or len(request.form.getlist("metadata")) != 1
            or set(request.files) != {"binary"}
            or len(request.files.getlist("binary")) != 1
        ):
            raise LabError("Send one firmware file and its metadata.")
        artifact = parse_manifest(request.form["metadata"])
        binary = request.files["binary"]
        package_format = Path(binary.filename or "").suffix.lower().lstrip(".")
        if package_format not in {"bin", "zip"}:
            raise LabError("Upload a .bin firmware binary or .zip release bundle.")
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
                        raise LabError("Firmware uploads must be at most 16 MiB.", 413)
                    hash_result.update(chunk)
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
            if not size:
                raise LabError("The firmware file is empty.")
            if not hmac.compare_digest(hash_result.hexdigest(), expected):
                raise LabError("The firmware file does not match its expected SHA-256.")
            try:
                inventory, summary, catalog = inspect_firmware(
                    temporary, expected, package_format
                )
            except FirmwareArchiveError as error:
                raise LabError(str(error)) from error

            actor = getattr(g, "workbench_user", None)
            artifact.update(
                schemaVersion=1,
                format=package_format,
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
                inspection = lab.connection.execute(
                    "SELECT format FROM firmware_inspections WHERE digest = ?",
                    (expected,),
                ).fetchone()
                if (inspection and inspection[0] != package_format) or (
                    existing and json.loads(existing[1])["format"] != package_format
                ):
                    raise LabError(
                        "The same bytes were already registered in a different firmware format.",
                        409,
                    )
                if inspection is None:
                    if catalog:
                        save_ui_catalog(
                            lab,
                            f"{artifact['name']} · {artifact['version']}"[
                                :100
                            ].rstrip(),
                            catalog,
                        )
                    lab.connection.execute(
                        "INSERT INTO firmware_inspections VALUES (?, ?, ?, ?)",
                        (
                            expected,
                            package_format,
                            json.dumps(summary),
                            json.dumps(inventory),
                        ),
                    )
                final = storage / f"{expected}.{package_format}"
                if not final.exists():
                    os.replace(temporary, final)
                if existing:
                    return jsonify(
                        artifact=json.loads(existing[1]) | {"inventory": summary}
                    )
                lab.connection.execute(
                    "INSERT INTO firmware_artifacts "
                    "(digest, name, version, model, architecture, metadata) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (expected, *manifest_key, json.dumps(artifact)),
                )
            return jsonify(artifact=artifact | {"inventory": summary}), 201
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def download_firmware(digest, package_format, mimetype):
        if not SHA256.fullmatch(digest):
            raise LabError("Firmware was not found.", 404)
        with lab.lock:
            exists = lab.connection.execute(
                "SELECT 1 FROM firmware_artifacts WHERE digest = ? "
                "AND json_extract(metadata, '$.format') = ?",
                (digest, package_format),
            ).fetchone()
        artifact = storage / f"{digest}.{package_format}"
        if not exists or not artifact.is_file():
            raise LabError("Firmware was not found.", 404)
        return send_file(artifact, as_attachment=True, mimetype=mimetype)

    @app.get(FIRMWARE_API + "/<digest>/binary")
    def download_binary(digest):
        return download_firmware(digest, "bin", "application/octet-stream")

    @app.get(FIRMWARE_API + "/<digest>/archive")
    def download_archive(digest):
        return download_firmware(digest, "zip", "application/zip")
