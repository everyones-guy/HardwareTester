"""Inspect firmware as data under the same path rules used for source archives."""

import hashlib
import json
import re
import struct
import tempfile
import tomllib
import zipfile
import zlib
from pathlib import Path, PurePosixPath

from .elf_inventory import ElfError, inspect_elf
from .ui_discovery import MAX_FILES, MAX_SOURCE_BYTES, UiDiscoveryError, discover_ui
from .utils.firmware_utils import FirmwareArchiveError, StagedArchive, read_zip

LANGUAGES = {
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".ts": "TypeScript",
    ".sh": "Shell",
    ".sql": "SQL",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".java": "Java",
    ".lua": "Lua",
}
MANIFESTS = {
    "release.json": "release",
    "package.json": "npm",
    "package-lock.json": "npm lock",
    "yarn.lock": "Yarn lock",
    "pnpm-lock.yaml": "pnpm lock",
    "pyproject.toml": "Python",
    "uv.lock": "uv lock",
    "poetry.lock": "Poetry lock",
    "cargo.toml": "Cargo",
    "cargo.lock": "Cargo lock",
    "go.mod": "Go modules",
    "go.sum": "Go module checksums",
    "makefile": "Make",
    "cmakelists.txt": "CMake",
    "meson.build": "Meson",
    "dockerfile": "Docker recipe",
}
METADATA_LIMIT = 128 * 1024
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+_~:-]{0,79}")
OS_FIELD = re.compile(r"(ID|VERSION_ID)=(?:\"([A-Za-z0-9_.+-]+)\"|([A-Za-z0-9_.+-]+))")


def manifest_metadata(path, kind):
    if path.stat().st_size > METADATA_LIMIT:
        return {}
    if kind in {"release", "npm", "npm lock"}:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    elif kind in {"Python", "Cargo"}:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        data = data.get("project" if kind == "Python" else "package")
    else:
        return {}
    if not isinstance(data, dict):
        return {}
    version = data.get("version")
    metadata = {}
    if isinstance(version, str) and VERSION.fullmatch(version):
        metadata["version"] = version
    lock_version = data.get("lockfileVersion")
    if kind == "npm lock" and type(lock_version) is int and 1 <= lock_version <= 100:
        metadata["lockfileVersion"] = lock_version
    return metadata


def inspect_file(path, relative, diagnostics):
    location = PurePosixPath(relative.lower())
    name, extension = location.name, location.suffix
    with path.open("rb") as stream:
        prefix = stream.read(4)
        stream.seek(0)
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    result = {
        "path": relative,
        "sizeBytes": path.stat().st_size,
        "sha256": digest,
        "kind": "unknown",
        "confidence": "unclassified",
    }
    if prefix == b"\x7fELF":
        result.update(kind="elf", confidence="magic")
        try:
            result.update(elf=inspect_elf(path.read_bytes()), confidence="headers")
        except ElfError as error:
            diagnostics.append({"path": relative, "message": str(error)})
        return result

    manifest = MANIFESTS.get(name)
    if name.startswith("requirements") and extension == ".txt":
        manifest = "Python requirements"
    if manifest:
        result.update(kind="manifest", format=manifest, confidence="filename")
        try:
            version = manifest_metadata(path, manifest)
            if version:
                result.update(metadata=version, confidence="parsed metadata")
        except (ValueError, RecursionError):
            diagnostics.append(
                {"path": relative, "message": "Manifest version could not be read."}
            )
    elif location.parts[-2:] == ("etc", "os-release") or location.parts[-3:] == (
        "usr",
        "lib",
        "os-release",
    ):
        result.update(kind="os-release", confidence="filename")
        if result["sizeBytes"] <= METADATA_LIMIT:
            fields = [
                OS_FIELD.fullmatch(line)
                for line in path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            ]
            metadata = {
                match[1]: match[2] or match[3]
                for match in fields
                if match and len(match[2] or match[3]) <= 80
            }
            if metadata:
                result.update(metadata=metadata, confidence="parsed metadata")
    elif extension in {".service", ".socket", ".timer"} or location.parts[:-1][-2:] == (
        "etc",
        "init.d",
    ):
        result.update(kind="service", confidence="filename")
    elif extension in {".sql", ".ui", ".qml", ".html"} or name in {
        "panel.json",
        "widgets.json",
    }:
        result.update(kind="ui-resource", confidence="filename")
    if extension in LANGUAGES:
        result["language"] = LANGUAGES[extension]
        if result["kind"] == "unknown":
            result.update(kind="source", confidence="filename")
    return result


def discover_release_ui(paths, diagnostics):
    if not paths:
        return None
    if (
        len(paths) > MAX_FILES
        or sum(path.stat().st_size for path in paths.values()) > MAX_SOURCE_BYTES
    ):
        diagnostics.append(
            {"message": "SQL resources exceed the UI catalog input limits."}
        )
        return None
    try:
        catalog = discover_ui(
            {name: path.read_bytes().decode("utf-8") for name, path in paths.items()}
        )
    except (UnicodeError, UiDiscoveryError):
        diagnostics.append(
            {"message": "The release SQL could not be read as supported UI source."}
        )
        return None
    if not catalog["pages"] and not catalog["controls"]:
        diagnostics.append(
            {"message": "SQL resources contain no supported UI records."}
        )
        return None
    return catalog


def summarize_inventory(digest, package_format, paths):
    diagnostics = []
    files = [
        inspect_file(path, relative, diagnostics)
        for relative, path in sorted(paths.items())
    ]
    elfs = [entry["elf"] for entry in files if "elf" in entry]
    abis = sorted(
        {
            (elf["architecture"] or "unknown", elf["bits"], elf["endianness"])
            for elf in elfs
        }
    )
    libraries = sorted({library for elf in elfs for library in elf["needed"]})
    bundled = sorted(
        {
            entry["elf"]["soname"] or PurePosixPath(entry["path"]).name
            for entry in files
            if "elf" in entry
            and entry["elf"]["type"] == "shared-or-PIE"
            and not entry["elf"]["interpreter"]
        }
    )
    catalog = discover_release_ui(
        {name: path for name, path in paths.items() if name.lower().endswith(".sql")},
        diagnostics,
    )
    summary = {
        "fileCount": len(files),
        "elfAbis": [
            dict(architecture=abi, bits=bits, endianness=order)
            for abi, bits, order in abis
        ],
        "unknownElfCount": sum(
            entry["kind"] == "elf"
            and ("elf" not in entry or entry["elf"]["architecture"] is None)
            for entry in files
        ),
    }
    inventory = {
        "schemaVersion": 1,
        "releaseSha256": digest,
        "format": package_format,
        **summary,
        "languages": sorted(
            {entry["language"] for entry in files if "language" in entry}
        ),
        "libc": sorted({elf["libc"] for elf in elfs if elf["libc"]}),
        "neededLibraries": libraries,
        "bundledLibraries": bundled,
        "librariesNotBundled": sorted(set(libraries) - set(bundled)),
        "uiCatalogSha256": catalog["catalogSha256"] if catalog else None,
        "files": files,
        "diagnostics": diagnostics,
    }
    return inventory, summary, catalog


def inspect_firmware(path, digest, package_format):
    if package_format == "bin":
        return summarize_inventory(digest, package_format, {"firmware.bin": path})
    with tempfile.TemporaryDirectory(
        prefix="release-inspection-", dir=path.parent
    ) as temporary:
        root = Path(temporary)
        stage = StagedArchive(
            root,
            max_members=512,
            max_member_bytes=16 * 1024 * 1024,
            max_expanded_bytes=64 * 1024 * 1024,
        )
        try:
            with path.open("rb") as source:
                read_zip(
                    source,
                    stage,
                    compression={zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED},
                )
        except (
            EOFError,
            OSError,
            RuntimeError,
            zipfile.BadZipFile,
            struct.error,
            zlib.error,
            UnicodeError,
        ) as error:
            raise FirmwareArchiveError(
                "ZIP is invalid or uses an unsupported format."
            ) from error
        paths = {
            name: root / name
            for name, directory in stage.members.values()
            if not directory
        }
        if not paths:
            raise FirmwareArchiveError("ZIP must contain at least one regular file.")
        return summarize_inventory(digest, package_format, paths)
