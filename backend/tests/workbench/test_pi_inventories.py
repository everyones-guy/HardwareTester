import pytest

from Hardware_Tester_App import create_app

from test_auth import setup, user

API = "/api/lab/pi-inventories"
INVENTORY = {
    "schemaVersion": 1,
    "capturedAt": "2026-01-10T13:30:00Z",
    "model": "Raspberry Pi 3 Model B Rev 1.2",
    "architecture": "aarch64",
    "kernel": "6.12.47+rpt-rpi-v8",
    "osId": "debian",
    "osVersion": "13",
    "memoryMiB": 921,
    "interfaces": ["usb", "i2c"],
}


@pytest.fixture
def db_config(tmp_path):
    return {"LAB_DB_PATH": str(tmp_path / "pi.sqlite3"), "LAB_WORKER": False}


@pytest.fixture
def app(db_config):
    app = create_app("testing", db_config)
    yield app
    app.extensions["lab"].close()


def test_snapshot_import_check_restart_and_delete(app, db_config):
    client = app.test_client()
    added = client.post(API, json={"name": "Lab controller", "inventory": INVENTORY})
    assert added.status_code == 201
    saved = added.json["inventories"][0]
    assert saved["name"] == "Lab controller"
    assert saved["inventory"]["interfaces"] == ["i2c", "usb"]
    path = f"{API}/{saved['id']}"

    result = client.post(
        f"{path}/checks",
        json={
            "checkIds": ["arm-kernel", "pi3b-64bit"],
            "customChecks": [
                {"field": "osVersion", "value": "13"},
                {"field": "interface", "value": "ethernet"},
            ],
        },
    )
    assert result.status_code == 200
    checks = result.json["checks"]
    assert [check["passed"] for check in checks] == [True, True, True, False]
    assert checks[-1]["actual"] == "i2c, usb"

    app.extensions["lab"].close()
    restarted = create_app("testing", db_config)
    try:
        client = restarted.test_client()
        assert client.get(API).json["inventories"] == [saved]
        assert client.delete(path, json={}).json["inventories"] == []
        assert client.post(f"{path}/checks", json={}).status_code == 404
    finally:
        restarted.extensions["lab"].close()


@pytest.mark.parametrize(
    "changes",
    [
        {"capturedAt": "2026-02-30T13:30:00Z"},
        {"memoryMiB": True},
        {"interfaces": ["usb", "usb"]},
        {"interfaces": [{}]},
        {"deviceAddress": "unexpected extra field"},
    ],
)
def test_invalid_inventory_leaves_library_unchanged(app, changes):
    client = app.test_client()
    response = client.post(API, json={"name": "Bad", "inventory": INVENTORY | changes})
    assert response.status_code == 400
    assert client.get(API).json["inventories"] == []


def test_role_boundaries(db_config):
    app = create_app("testing", db_config | {"LAB_AUTH_ENABLED": True})
    try:
        admin = app.test_client()
        signed = setup(admin)
        headers = {"X-CSRF-Token": signed["csrf"]}
        data = {"name": "Lab controller", "inventory": INVENTORY}
        added = admin.post(API, json=data, headers=headers)
        path = f"{API}/{added.json['inventories'][0]['id']}"
        assert app.test_client().get(API).status_code == 401
        for role in ("viewer", "operator"):
            client, csrf = user(app, admin, signed["csrf"], role)
            headers = {"X-CSRF-Token": csrf}
            assert client.get(API).status_code == 200
            assert client.post(API, json=data, headers=headers).status_code == 403
            assert client.delete(path, json={}, headers=headers).status_code == 403
            checks = {"checkIds": ["pi3b-64bit"]}
            assert client.post(f"{path}/checks", json=checks).status_code == 403
            result = client.post(f"{path}/checks", json=checks, headers=headers)
            assert result.status_code == (403 if role == "viewer" else 200)
            plan = client.post(
                f"{path}/provisioning-plan", json={"manifest": {}}, headers=headers
            )
            assert plan.status_code == (403 if role == "viewer" else 400)
    finally:
        app.extensions["lab"].close()
