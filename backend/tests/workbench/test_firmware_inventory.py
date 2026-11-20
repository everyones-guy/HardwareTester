import hashlib
import io
import json
import stat
import struct
import zipfile
from pathlib import Path

import pytest

from Hardware_Tester_App import create_app
from Hardware_Tester_App.elf_inventory import ElfError, inspect_elf

from test_auth import setup, user
from test_pi_inventories import INVENTORY

API = "/api/lab/firmware"
UI = Path(__file__).resolve().parents[3] / "deployment/ui-fixtures/uisee-controller"


def synthetic_elf(machine=183, library=b"libfixture.so.1", *, wide=True, little=True):
    encoding = "<" if little else ">"
    header = struct.Struct(encoding + ("HHIQQQIHHHHHH" if wide else "HHIIIIIHHHHHH"))
    program = struct.Struct(encoding + ("IIQQQQQQ" if wide else "IIIIIIII"))
    dynamic = struct.Struct(encoding + ("qQ" if wide else "iI"))
    prefix = b"\x7fELF" + bytes([2 if wide else 1, 1 if little else 2, 1]) + bytes(9)
    start = len(prefix) + header.size
    address = 0x10000
    interpreter = b"/lib/ld-linux-aarch64.so.1\0"
    strings = b"\0" + library + b"\0"
    interp_offset = start + 3 * program.size
    strings_offset = interp_offset + len(interpreter)
    dynamic_offset = strings_offset + len(strings)
    total = dynamic_offset + 4 * dynamic.size

    def segment(kind, offset, size):
        common = (offset, address + offset, 0, size, size)
        return (
            program.pack(kind, 0, *common, 1)
            if wide
            else program.pack(kind, *common, 0, 1)
        )

    return (
        prefix
        + header.pack(3, machine, 1, 0, start, 0, 0, start, program.size, 3, 0, 0, 0)
        + segment(3, interp_offset, len(interpreter))
        + segment(1, 0, total)
        + segment(2, dynamic_offset, total - dynamic_offset)
        + interpreter
        + strings
        + b"".join(
            dynamic.pack(tag, value)
            for tag, value in [
                (1, 1),
                (5, address + strings_offset),
                (10, len(strings)),
                (0, 0),
            ]
        )
    )


def zip_release(files):
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return target.getvalue()


def upload(
    client,
    contents,
    *,
    version="1.0",
    name="Fixture controller",
    filename="release.zip",
    headers=None,
):
    digest = hashlib.sha256(contents).hexdigest()
    metadata = {
        "model": INVENTORY["model"],
        "architecture": "arm64",
        "name": name,
        "version": version,
        "sha256": digest,
    }
    return digest, client.post(
        API,
        data={
            "metadata": json.dumps(metadata),
            "binary": (io.BytesIO(contents), filename),
        },
        headers=headers,
    )


def app_config(tmp_path, *, auth=False):
    return {
        "LAB_DB_PATH": str(tmp_path / "inventory.sqlite3"),
        "LAB_WORKER": False,
        "LAB_AUTH_ENABLED": auth,
        "LAB_ALLOW_HARDWARE": False,
    }


def test_static_elf_32bit_big_endian_and_malformed_dynamic_bounds():
    image = synthetic_elf(machine=8, wide=False, little=False)
    header = inspect_elf(image)
    assert (header["architecture"], header["bits"], header["endianness"]) == (
        "mips",
        32,
        "big",
    )
    assert header["needed"] == ["libfixture.so.1"]
    with pytest.raises(ElfError):
        inspect_elf(image[:-1])


def test_release_inventory_persists_and_filters_conflicting_elf(tmp_path):
    config = app_config(tmp_path)
    app = create_app("testing", config)
    try:
        client = app.test_client()
        capture = client.post(
            "/api/lab/pi-inventories",
            json={"name": "Fixture Pi", "inventory": INVENTORY},
        )
        target = capture.json["inventories"][0]["id"]
        source_files = {
            f"ui/{file.name}": file.read_bytes() for file in UI.glob("*.sql")
        }
        first = zip_release(
            source_files
            | {
                "bin/fixture": synthetic_elf(),
                "app/controller.cpp": b"// synthetic source",
                "package.json": b'{"version":"1.0.0","privateData":"fixture-canary-secret"}',
                "release.json": b'{"version":"1.0.0"}',
                "etc/os-release": b'ID=debian\nVERSION_ID="12"\n',
                "etc/systemd/system/fixture.service": b"[Service]\nEnvironment=fixture-canary-secret",
            }
        )
        second = zip_release(
            source_files
            | {"bin/fixture": synthetic_elf(machine=62, library=b"libnew.so.2")}
        )
        mixed = zip_release(
            {"bin/arm": synthetic_elf(), "bin/x86": synthetic_elf(machine=62)}
        )
        first_digest, accepted = upload(client, first)
        assert accepted.status_code == 201
        assert upload(client, first)[1].status_code == 200
        second_digest, response = upload(client, second, version="2.0")
        assert response.status_code == 201
        assert upload(client, mixed, version="3.0")[1].status_code == 201
    finally:
        app.extensions["lab"].close()

    reopened = create_app("testing", config)
    try:
        client = reopened.test_client()
        listing = client.get(f"{API}?inventoryId={target}").json["artifacts"]
        assert [artifact["compatibility"] for artifact in listing] == [
            "reviewRequired",
            "mismatch",
            "inventoryMatch",
        ]
        assert listing[1]["differences"] == ["observed ELF architecture"]
        report = client.get(f"{API}/{first_digest}/inventory")
        assert b"fixture-canary-secret" not in report.data
        inventory = report.json["inventory"]
        assert inventory["releaseSha256"] == first_digest
        assert inventory["libc"] == ["glibc"]
        assert inventory["languages"] == ["C++", "SQL"]
        assert inventory["librariesNotBundled"] == ["libfixture.so.1"]
        files = {file["path"]: file for file in inventory["files"]}
        assert (
            files["bin/fixture"]["sha256"]
            == hashlib.sha256(synthetic_elf()).hexdigest()
        )
        assert files["package.json"]["metadata"] == {"version": "1.0.0"}
        assert files["etc/os-release"]["metadata"] == {
            "ID": "debian",
            "VERSION_ID": "12",
        }
        assert files["etc/systemd/system/fixture.service"]["kind"] == "service"
        assert (
            files["ui/Valve.sql"]["sha256"]
            == hashlib.sha256(source_files["ui/Valve.sql"]).hexdigest()
        )
        second_report = client.get(f"{API}/{second_digest}/inventory").json["inventory"]
        assert second_report["neededLibraries"] == ["libnew.so.2"]
        catalog_id = inventory["uiCatalogSha256"]
        catalog = client.get(f"/api/lab/ui-catalogs/{catalog_id}").json["catalog"][
            "catalog"
        ]
        assert catalog_id == second_report["uiCatalogSha256"]
        assert "workflow" in next(
            control
            for control in catalog["controls"]
            if control["name"] == "ValveTarget"
        )
        assert len(client.get("/api/lab/ui-catalogs").json["catalogs"]) == 1
    finally:
        reopened.extensions["lab"].close()


def test_unsafe_archives_publish_nothing_and_archive_download_requires_operator(
    tmp_path,
):
    app = create_app("testing", app_config(tmp_path, auth=True))
    try:
        admin = app.test_client()
        signed = setup(admin)
        headers = {"X-CSRF-Token": signed["csrf"]}
        path = zipfile.ZipInfo("unsafe-link")
        path.create_system = 3
        path.external_attr = (stat.S_IFLNK | 0o777) << 16
        sql = (UI / "Valve.sql").read_bytes()
        for archive in (
            b"not a zip",
            zip_release({"Valve.sql": sql, "../escaped": b"outside"}),
            zip_release({"Valve.sql": sql, "valve.SQL": b"conflicting bytes"}),
            zip_release({"Valve.sql": sql, path: b"elsewhere"}),
            zip_release({"Valve.sql": sql, "bad": b"crc-canary"}).replace(
                b"crc-canary", b"crc-broken"
            ),
        ):
            digest, response = upload(admin, archive, headers=headers)
            assert response.status_code == 400
            assert admin.get(f"{API}/{digest}/inventory").status_code == 404
        assert not admin.get(API).json["artifacts"]
        assert not admin.get("/api/lab/ui-catalogs").json["catalogs"]
        assert not list(tmp_path.glob("*.firmware/*"))

        archive = zip_release({"bin/fixture": synthetic_elf()})
        digest, created = upload(admin, archive, headers=headers)
        assert created.status_code == 201
        viewer, _ = user(app, admin, signed["csrf"], "viewer")
        operator, csrf = user(app, admin, signed["csrf"], "operator")
        assert app.test_client().get(f"{API}/{digest}/inventory").status_code == 401
        assert viewer.get(f"{API}/{digest}/inventory").status_code == 200
        assert viewer.get(f"{API}/{digest}/archive").status_code == 403
        assert operator.get(f"{API}/{digest}/binary").status_code == 404
        assert operator.get(f"{API}/{digest}/archive").data == archive
        assert (
            upload(operator, archive, headers={"X-CSRF-Token": csrf})[1].status_code
            == 403
        )
    finally:
        app.extensions["lab"].close()


def test_existing_binary_can_be_inspected_on_reupload(tmp_path):
    config = app_config(tmp_path)
    app = create_app("testing", config)
    lab = app.extensions["lab"]
    try:
        client = app.test_client()
        original_bytes = b"legacy opaque image"
        digest, created = upload(client, original_bytes, filename="legacy.bin")
        assert created.status_code == 201
        # Model a pre-inspection workspace while retaining the original artifact row and binary.
        with lab.connection:
            lab.connection.execute(
                "DELETE FROM firmware_inspections WHERE digest = ?", (digest,)
            )
        old = client.get(API).json["artifacts"][0]
        assert "inventory" not in old
        assert client.get(f"{API}/{digest}/binary").data == original_bytes
        assert (
            upload(client, original_bytes, filename="legacy.bin")[1].status_code == 200
        )
        assert len(client.get(API).json["artifacts"]) == 1
        report = client.get(f"{API}/{digest}/inventory").json["inventory"]
        assert report["releaseSha256"] == digest
        assert report["files"][0]["kind"] == "unknown"
    finally:
        lab.close()
