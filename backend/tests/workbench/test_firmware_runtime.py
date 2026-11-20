import copy
import json

import pytest

from Hardware_Tester_App import create_app
from Hardware_Tester_App.firmware_runtime import BASES, make_runtime_profile
from tools import run_firmware_runtime

from test_firmware_inventory import API, app_config, synthetic_elf, upload, zip_release


def profile_fixture(needed=b"libc.so.6"):
    return zip_release(
        {
            "bin/controller": synthetic_elf(library=needed),
            "usr/lib/os-release": b'ID=debian\nVERSION_ID="12"\n',
            "package.json": b'{"version":"1.0.0"}',
        }
    )


def test_saved_release_resolves_base_dependencies_and_rejects_unknown_entry(tmp_path):
    app = create_app("testing", app_config(tmp_path))
    try:
        client = app.test_client()
        digest, uploaded = upload(client, profile_fixture())
        assert uploaded.status_code == 201
        url = f"{API}/{digest}/runtime-profile"
        response = client.get(url, query_string={"argument": "--self-test"})
        profile = response.json["profile"]
        assert profile["status"] == "readyForSmokeTest"
        assert profile["releaseSha256"] == digest
        assert profile["arguments"] == ["--self-test"]
        assert profile["platform"] == "linux/arm64"
        assert profile["baseImage"] == BASES["aarch64"]["image"]
        assert profile["dependencies"] == [
            {
                "library": "libc.so.6",
                "requiredBy": "bin/controller",
                "resolution": "baseImage",
            }
        ]
        assert profile["sourceManifests"][0]["metadata"]["version"] == "1.0.0"
        assert client.get(url, query_string={"entrypoint": "../bad"}).status_code == 400
        assert (
            client.get(
                url, query_string={"argument": "--flag; another thing"}
            ).status_code
            == 400
        )
        assert (
            client.get(url, query_string={"argument": "--self-test"}).json
            == response.json
        )

        source_digest, uploaded = upload(
            client, zip_release({"package.json": b'{"version":"1.0.0"}'}), version="2"
        )
        assert uploaded.status_code == 201
        assert client.get(f"{API}/{source_digest}/runtime-profile").json == {
            "entrypoints": [],
            "profile": None,
        }
    finally:
        app.extensions["lab"].close()


@pytest.mark.parametrize("missing", [False, True], ids=["complete", "missing-library"])
def test_workbench_lock_roundtrip_and_lack_of_approval(tmp_path, monkeypatch, missing):
    calls = []
    monkeypatch.setattr(
        run_firmware_runtime,
        "run_container",
        lambda profile, payload: calls.append(payload) or {"exitCode": 0},
    )
    app = create_app("testing", app_config(tmp_path))
    try:
        client = app.test_client()
        raw = profile_fixture(b"libuhtguard.so.1" if missing else b"libc.so.6")
        digest, uploaded = upload(client, raw)
        assert uploaded.status_code == 201
        profile = client.get(f"{API}/{digest}/runtime-profile").json["profile"]
        bundle = tmp_path / "release.zip"
        bundle.write_bytes(raw)
        lock = tmp_path / "profile.json"
        lock.write_text(json.dumps(profile), encoding="utf-8")

        def verify(run=False, approved=None):
            return run_firmware_runtime.verify_and_run(
                lock, bundle, run=run, approved_sha256=approved
            )

        status, report = verify()
        assert report["dockerInvoked"] is False and calls == []
        if missing:
            assert status == 2
            assert report["profile"]["missingLibraries"] == ["libuhtguard.so.1"]
            assert verify(run=True, approved=digest)[0] == 2
            assert not calls
        else:
            assert status == 0
            with pytest.raises(ValueError, match="approved-sha256"):
                verify(run=True)
            lock.write_text(
                json.dumps(profile | {"baseImage": "some-other-image"}),
                encoding="utf-8",
            )
            with pytest.raises(ValueError, match="differs"):
                verify(run=True, approved=digest)
            lock.write_text(json.dumps(profile), encoding="utf-8")
            bundle.write_bytes(raw + b"changed")
            with pytest.raises(ValueError, match="does not match"):
                verify(run=True, approved=digest)
            assert not calls
            bundle.write_bytes(raw)
            assert verify(run=True, approved=digest)[1]["status"] == "passed"
            assert len(calls) == 1
    finally:
        app.extensions["lab"].close()


def test_transitive_closure_reports_duplicate_and_wrong_abi_libraries(tmp_path):
    app = create_app("testing", app_config(tmp_path))
    try:
        client = app.test_client()
        digest, _ = upload(client, profile_fixture(b"libfixture.so.1"))
        inventory = client.get(f"{API}/{digest}/inventory").json["inventory"]
        original = next(
            file for file in inventory["files"] if file["path"] == "bin/controller"
        )
        library = copy.deepcopy(original)
        library.update(path="lib/fixture-release-name.so")
        library["elf"].update(
            interpreter=None, soname="libfixture.so.1", needed=["libextra.so.1"]
        )
        wrong_abi = copy.deepcopy(library)
        wrong_abi.update(path="lib/libextra.so.1")
        wrong_abi["elf"].update(architecture="x86_64", soname="libextra.so.1")
        inventory["files"].extend([library, wrong_abi])
        profile = make_runtime_profile(inventory, "bin/controller")
        assert profile["bundledLibraries"][0]["loadAs"] == "libfixture.so.1"
        assert profile["missingLibraries"] == ["libextra.so.1"]
        assert profile["dependencies"][1]["requiredBy"] == library["path"]
        inventory["files"].append(library | {"path": "another/libfixture.so.1"})
        profile = make_runtime_profile(inventory, "bin/controller")
        assert profile["dependencies"][0]["resolution"] == "ambiguous"
        assert profile["status"] == "blocked"
    finally:
        app.extensions["lab"].close()
