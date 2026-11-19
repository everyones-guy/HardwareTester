import hashlib
import io
import json

from Hardware_Tester_App import create_app

from test_auth import setup, user
from test_pi_inventories import INVENTORY


def test_firmware_upload_digest_permissions_and_inventory_matching(tmp_path):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(tmp_path / "firmware.sqlite3"),
            "LAB_WORKER": False,
            "LAB_AUTH_ENABLED": True,
        },
    )
    try:
        admin = app.test_client()
        signed = setup(admin)
        admin_headers = {"X-CSRF-Token": signed["csrf"]}
        data = b"sample lab firmware binary"
        digest = hashlib.sha256(data).hexdigest()
        metadata = {
            "name": "Temperature controller",
            "version": "1.2.3",
            "architecture": INVENTORY["architecture"],
            "model": INVENTORY["model"],
            "sha256": digest,
        }

        def upload(client, headers, contents=data, **changes):
            return client.post(
                "/api/lab/firmware",
                headers=headers,
                data={
                    "metadata": json.dumps(metadata | changes),
                    "binary": (io.BytesIO(contents), "firmware.bin"),
                },
            )

        assert app.test_client().get("/api/lab/firmware").status_code == 401
        assert upload(admin, admin_headers, b"wrong bytes").status_code == 400
        saved = upload(admin, admin_headers)
        assert saved.status_code == 201
        assert saved.json["artifact"]["uploadedBy"] == "admin"
        assert upload(admin, admin_headers).status_code == 200
        other = b"another binary"
        assert (
            upload(
                admin, admin_headers, other, sha256=hashlib.sha256(other).hexdigest()
            ).status_code
            == 409
        )
        assert (
            upload(admin, admin_headers, model="Another board revision").status_code
            == 201
        )
        inventory = admin.post(
            "/api/lab/pi-inventories",
            json={"name": "Lab", "inventory": INVENTORY},
            headers=admin_headers,
        ).json["inventories"][0]["id"]
        options = admin.get(f"/api/lab/firmware?inventoryId={inventory}").json[
            "artifacts"
        ]
        assert [option["compatibility"] for option in options] == [
            "mismatch",
            "declaredMatch",
        ]
        binary = f"/api/lab/firmware/{digest}/binary"
        viewer, csrf = user(app, admin, signed["csrf"], "viewer")
        assert viewer.get(binary).status_code == 403
        operator, csrf = user(app, admin, signed["csrf"], "operator")
        assert upload(operator, {"X-CSRF-Token": csrf}).status_code == 403
        assert operator.get(binary).data == data
    finally:
        app.extensions["lab"].close()
