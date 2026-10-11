"""Run the release harness against real HTTP servers and fresh SQLite files."""

from contextlib import contextmanager
import importlib.util
from pathlib import Path
import threading
import urllib.error

import pytest
from werkzeug.serving import make_server
from Hardware_Tester_App import create_app

spec = importlib.util.spec_from_file_location(
    "release_check", Path(__file__).resolve().parents[2] / "tools" / "release_check.py"
)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


@contextmanager
def server(path, frontend=None):
    app = create_app(
        "testing",
        {
            "LAB_DB_PATH": str(path),
            "LAB_WORKER": True,
            "LAB_STEP_SECONDS": 0,
            "LAB_AUTH_ENABLED": True,
            "LAB_COOKIE_SECURE": False,
            "LAB_API_TOKEN": "",
            "LAB_ALLOW_HARDWARE": False,
            "FRONTEND_BUILD": str(frontend or path.parent / "no-frontend"),
        },
    )
    http = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield check.Client(f"http://127.0.0.1:{http.server_port}")
    finally:
        http.shutdown()
        thread.join(timeout=5)
        http.server_close()
        app.extensions["lab"].close()


def test_release_workflow_survives_restart_and_recovers_independently(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    archive = tmp_path / "archive.json"
    with server(tmp_path / "source.sqlite3") as client:
        check.seed(client, checkpoint)
    with server(tmp_path / "source.sqlite3") as client:
        check.verify(client, checkpoint, archive)
    with server(tmp_path / "target.sqlite3") as client:
        check.restore(client, archive)
    assert "password" not in archive.read_text(encoding="utf-8")


def test_release_seed_refuses_an_existing_installation(tmp_path):
    with server(tmp_path / "existing.sqlite3") as client:
        client.fresh_admin("existing_admin")
        before = client.lab()["state"]
        with pytest.raises(RuntimeError, match="fresh installation"):
            check.seed(client, tmp_path / "checkpoint.json")
        assert client.lab()["state"] == before


def test_frontend_probe_fetches_compiled_assets_and_rejects_missing_files(tmp_path):
    frontend = tmp_path / "frontend"
    assets = frontend / "assets"
    assets.mkdir(parents=True)
    (frontend / "index.html").write_text(
        '<script src="/assets/app.js"></script><link href="/assets/app.css" rel="stylesheet">',
        encoding="utf-8",
    )
    (assets / "app.js").write_text("console.log('bench');", encoding="utf-8")
    (assets / "app.css").write_text("body { color: black; }", encoding="utf-8")
    with server(tmp_path / "web.sqlite3", frontend) as client:
        client.web_assets()
        (assets / "app.js").unlink()
        with pytest.raises(urllib.error.HTTPError) as error:
            client.web_assets()
        assert error.value.code == 404
