"""Generate a deterministic, read-only runtime profile from a saved ELF inventory."""

import hashlib
import json
import re
from collections import defaultdict, deque
from pathlib import PurePosixPath

# SONAMEs observed in ldconfig -p in the pinned Debian 12 images. See FIRMWARE-RUNTIME.md.
BASE_LIBRARIES = frozenset("""
libacl.so.1 libanl.so.1 libapt-pkg.so.6.0 libapt-private.so.0.0 libattr.so.1 libaudit.so.1
libblkid.so.1 libBrokenLocale.so.1 libbz2.so.1.0 libc_malloc_debug.so.0 libc.so.6
libcap-ng.so.0 libcap.so.2 libcom_err.so.2 libcrypt.so.1 libdb-5.3.so libdebconfclient.so.0
libdl.so.2 libdrop_ambient.so.0 libe2p.so.2 libext2fs.so.2 libffi.so.8 libgcc_s.so.1
libgcrypt.so.20 libgmp.so.10 libgnutls.so.30 libgpg-error.so.0 libhogweed.so.6 libidn2.so.0
liblz4.so.1 liblzma.so.5 libm.so.6 libmd.so.0 libmemusage.so libmount.so.1 libnettle.so.8
libnsl.so.1 libnss_compat.so.2 libnss_dns.so.2 libnss_files.so.2 libnss_hesiod.so.2
libp11-kit.so.0 libpam_misc.so.0 libpam.so.0 libpamc.so.0 libpcprofile.so libpcre2-8.so.0
libpsx.so.2 libpthread.so.0 libresolv.so.2 librt.so.1 libseccomp.so.2 libselinux.so.1
libsemanage.so.2 libsepol.so.2 libsmartcols.so.1 libss.so.2 libstdc++.so.6 libsystemd.so.0
libtasn1.so.6 libthread_db.so.1 libtic.so.6 libtinfo.so.6 libudev.so.1 libunistring.so.2
libutil.so.1 libuuid.so.1 libxxhash.so.0 libz.so.1 libzstd.so.1
""".split())
BASES = {
    "x86_64": {
        "platform": "linux/amd64",
        "image": "docker.io/library/debian@sha256:c67e92c8099ba22853ab4cfda7cfb494d253d6012ca82dee98ba8976772af018",
        "interpreter": "/lib64/ld-linux-x86-64.so.2",
        "libraries": BASE_LIBRARIES | {"ld-linux-x86-64.so.2", "libmvec.so.1"},
    },
    "aarch64": {
        "platform": "linux/arm64",
        "image": "docker.io/library/debian@sha256:ec8534cda2cb30f29f44f23e135297af7a1496f2990fd8e4e84aa36b081a757a",
        "interpreter": "/lib/ld-linux-aarch64.so.1",
        "libraries": BASE_LIBRARIES | {"ld-linux-aarch64.so.1"},
    },
}
LIBC_PACKAGE = "2.36-9+deb12u14"
SMOKE_FLAG = re.compile(r"--[A-Za-z][A-Za-z0-9-]{0,31}")
LIBRARY_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.+\-]{0,254}")
MAX_DEPENDENCIES = 256


def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(entry):
    return {field: entry[field] for field in ("path", "sha256")}


def runtime_entrypoints(inventory):
    if inventory["format"] != "zip":
        return []
    return [
        fingerprint(entry)
        for entry in inventory["files"]
        if (elf := entry.get("elf"))
        and elf["interpreter"]
        and elf["type"] in {"executable", "shared-or-PIE"}
    ]


def abi(elf):
    return elf["architecture"], elf["bits"], elf["endianness"]


def dependency_closure(files, executable, base):
    candidates = defaultdict(dict)
    for entry in files:
        elf = entry.get("elf")
        if (
            elf
            and elf["type"] == "shared-or-PIE"
            and not elf["interpreter"]
            and abi(elf) == abi(executable["elf"])
        ):
            for name in {elf["soname"], PurePosixPath(entry["path"]).name}:
                if name:
                    candidates[name][entry["path"]] = entry

    pending = deque([executable])
    visited = set()
    bindings = {}
    edges = []
    while pending:
        entry = pending.popleft()
        if entry["path"] in visited:
            continue
        visited.add(entry["path"])
        for name in entry["elf"]["needed"]:
            if len(edges) >= MAX_DEPENDENCIES:
                return edges, [], True
            edge = {"library": name, "requiredBy": entry["path"]}
            matches = candidates[name]
            in_base = name in base["libraries"]
            if not LIBRARY_NAME.fullmatch(name):
                edge["resolution"] = "unsupportedPath"
            elif len(matches) > 1 or (in_base and matches):
                edge.update(
                    resolution="ambiguous",
                    candidates=sorted(matches),
                    alsoInBase=in_base,
                )
            elif in_base:
                edge["resolution"] = "baseImage"
            elif not matches:
                edge["resolution"] = "missing"
            else:
                match = next(iter(matches.values()))
                bindings[name] = dict(fingerprint(match), loadAs=name)
                edge.update(resolution="bundle", path=match["path"])
                pending.append(match)
            edges.append(edge)
    return edges, [bindings[name] for name in sorted(bindings)], False


def make_runtime_profile(inventory, entrypoint, argument=None):
    if argument is not None and (
        not isinstance(argument, str) or not SMOKE_FLAG.fullmatch(argument)
    ):
        raise ValueError("Enter one optional smoke-test flag such as --self-test.")
    if not any(node["path"] == entrypoint for node in runtime_entrypoints(inventory)):
        raise ValueError(
            "Choose an inspected dynamic ELF entry point from this ZIP release."
        )
    files = inventory["files"]
    executable = next(entry for entry in files if entry["path"] == entrypoint)
    elf = executable["elf"]
    base = BASES.get(elf["architecture"])
    if base and (
        abi(elf)[1:] != (64, "little")
        or elf["libc"] != "glibc"
        or elf["interpreter"] != base["interpreter"]
    ):
        base = None
    os_versions = sorted(
        {
            (entry["metadata"].get("ID", ""), entry["metadata"].get("VERSION_ID", ""))
            for entry in files
            if entry["kind"] == "os-release" and "metadata" in entry
        }
    )
    notes = []
    if os_versions != [("debian", "12")]:
        notes.append(
            "A unique Debian 12 OS declaration in etc/os-release or usr/lib/os-release is required."
        )
    if base is None:
        notes.append(
            "No pinned runtime supports the inspected ELF architecture, bitness and interpreter."
        )
    edges, libraries, truncated = (
        dependency_closure(files, executable, base) if base else ([], [], False)
    )
    missing = sorted(
        {edge["library"] for edge in edges if edge["resolution"] == "missing"}
    )
    if missing:
        notes.append(
            "Required libraries absent from the locked release and base: "
            + ", ".join(missing)
        )
    if any(edge["resolution"] == "ambiguous" for edge in edges):
        notes.append(
            "Resolve duplicate bundled libraries or libraries that shadow the pinned base."
        )
    if any(edge["resolution"] == "unsupportedPath" for edge in edges):
        notes.append(
            "The ELF contains a path-based DT_NEEDED entry. This runtime accepts library names only."
        )
    if truncated:
        notes.append("The dependency graph exceeds the supported edge limit.")
    profile = {
        "schemaVersion": 1,
        "releaseSha256": inventory["releaseSha256"],
        "entrypoint": fingerprint(executable),
        "arguments": [argument] if argument is not None else [],
        "architecture": elf["architecture"],
        "interpreter": elf["interpreter"],
        "platform": base["platform"] if base else None,
        "baseImage": base["image"] if base else None,
        "libcPackageVersion": LIBC_PACKAGE if base else None,
        "osEvidence": [
            {"id": system, "version": version} for system, version in os_versions
        ],
        "sourceManifests": [
            fingerprint(entry)
            | {"format": entry["format"], "metadata": entry.get("metadata", {})}
            for entry in files
            if entry["kind"] == "manifest"
        ],
        "dependencies": edges,
        "bundledLibraries": libraries,
        "missingLibraries": missing,
        "status": "blocked" if notes else "readyForSmokeTest",
        "diagnostics": notes,
    }
    return profile | {
        "profileSha256": hashlib.sha256(canonical_json(profile).encode()).hexdigest()
    }
