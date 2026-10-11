"""Exercise disposable installations over HTTP; never point this at a real bench.

Checkpoints contain disposable credentials and belong in the test volume. The
separate archive contains workspace data only and can be copied to a new stack.
"""

import argparse
import http.cookiejar
from html.parser import HTMLParser
import json
from pathlib import Path
import secrets
import time
import urllib.error
import urllib.request


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Client:
    def __init__(self, url):
        self.url = url.rstrip("/")
        self.csrf = ""
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def request(self, path, data=None):
        request = urllib.request.Request(
            self.url + path,
            data=None if data is None else json.dumps(data).encode(),
            headers={"Content-Type": "application/json", "X-CSRF-Token": self.csrf},
        )
        try:
            with self.opener.open(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            # Do not include request bodies, credentials, or server debug output.
            raise RuntimeError(f"{path}: HTTP {error.code}") from None

    def lab(self, path="", data=None):
        return self.request("/api/lab" + path, data)

    def login(self, account):
        self.csrf = self.request("/api/auth/login", account)["csrf"]

    def web_assets(self):
        class Assets(HTMLParser):
            def __init__(self):
                super().__init__()
                self.paths = set()

            def handle_starttag(self, tag, attrs):
                for name, value in attrs:
                    if (
                        name in ("src", "href")
                        and value
                        and value.startswith("/assets/")
                    ):
                        self.paths.add(value)

        with self.opener.open(self.url + "/", timeout=30) as response:
            require(
                response.headers.get_content_type() == "text/html",
                "Frontend HTML missing.",
            )
            html = response.read().decode("utf-8")
        assets = Assets()
        assets.feed(html)
        require(
            any(p.endswith(".js") for p in assets.paths), "Frontend script missing."
        )
        require(
            any(p.endswith(".css") for p in assets.paths), "Frontend styles missing."
        )
        for path in assets.paths:
            with self.opener.open(self.url + path, timeout=30) as response:
                require(
                    response.read()
                    and response.headers.get_content_type() != "text/html",
                    f"Frontend asset missing: {path}",
                )
        print("PASS: nginx serves the frontend and its compiled assets.", flush=True)

    def fresh_admin(self, username):
        session = self.request("/api/auth/session")
        require(
            session["enabled"] and session["setupRequired"],
            "Release checks require a fresh installation with authentication enabled.",
        )
        account = {"username": username, "password": secrets.token_urlsafe(32)}
        self.csrf = self.request(
            "/api/auth/setup", {**account, "email": username + "@example.invalid"}
        )["csrf"]
        return account

    def run_suite(self, suite, device):
        self.lab(f"/devices/{device}/connection", {"connected": True})
        identity = self.lab(f"/validation-suites/{suite}/run", {"deviceId": device})[
            "suiteRunId"
        ]
        report = self.wait("suiteRuns", identity)
        require(report["status"] == "passed", "Validation suite failed.")
        require(report["restoration"] == "restored", "Suite did not restore its input.")
        actual = [
            [attempt["run"]["status"] for attempt in case["attempts"]]
            for case in report["cases"]
        ]
        require(
            actual == [["passed"], ["failed"], ["failed", "passed"]],
            "Healthy, expected failure, and recovery outcomes differ.",
        )
        return identity

    def wait(self, collection, identity):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            report = next(
                r for r in self.lab()["state"][collection] if r["id"] == identity
            )
            if report["status"] != "running":
                return report
            time.sleep(0.25)
        raise RuntimeError("Test did not finish within 120 seconds.")


def seed(client, checkpoint, mqtt=False):
    account = client.fresh_admin("release_admin")
    client.request(
        "/api/auth/users",
        {
            "username": "release_operator",
            "email": "operator@example.invalid",
            "password": secrets.token_urlsafe(32),
            "role": "operator",
        },
    )
    device = client.lab(
        "/devices",
        {"name": "Release temperature", "kind": "temperature", "adapter": "simulation"},
    )["deviceId"]
    plan = client.lab(
        "/test-plans",
        {
            "name": "Release saved plan",
            "kind": "temperature",
            "steps": [{"action": "assert_range", "min": 0, "max": 50}],
        },
    )["planId"]
    scenario = client.lab(
        "/scenarios",
        {
            "name": "Release saved healthy",
            "frames": [{"behavior": "healthy", "count": 1}],
        },
    )["scenarioId"]
    suite = client.lab(
        "/validation-suites",
        {
            "name": "Release acceptance",
            "kind": "temperature",
            "planId": plan,
            "cases": [
                {"name": "Healthy", "scenarioId": scenario, "expected": ["passed"]},
                {
                    "name": "Expected failure",
                    "scenarioId": "preset-sustained-bad-reading",
                    "expected": ["failed"],
                },
                {
                    "name": "Recovery",
                    "scenarioId": "preset-recovery",
                    "expected": ["failed", "passed"],
                },
            ],
        },
    )["suiteId"]
    report = client.run_suite(suite, device)
    if mqtt:
        mqtt_device = client.lab(
            "/devices",
            {
                "name": "Release MQTT valve",
                "kind": "valve",
                "adapter": "mqtt",
                "endpoint": "mqtt://broker:1883/lab/demo-valve",
            },
        )["deviceId"]
        state = client.lab(f"/devices/{mqtt_device}/connection", {"connected": True})[
            "state"
        ]
        original = next(d["value"] for d in state["devices"] if d["id"] == mqtt_device)
        run = client.lab("/runs", {"deviceId": mqtt_device, "plan": "control"})["runId"]
        require(
            client.wait("runs", run)["status"] == "passed", "MQTT control run failed."
        )
        final = next(
            d for d in client.lab()["state"]["devices"] if d["id"] == mqtt_device
        )
        require(final["value"] == original, "MQTT output was not restored.")
        print("PASS: MQTT connect, command, verify, and restore.", flush=True)
    saved = dict(
        account=account,
        device=device,
        plan=plan,
        scenario=scenario,
        suite=suite,
        report=report,
    )
    checkpoint.write_text(json.dumps(saved), encoding="utf-8")
    print(
        "PASS: first administrator, operator, saved libraries, and four suite attempts.",
        flush=True,
    )


def verify(client, checkpoint, archive):
    saved = json.loads(checkpoint.read_text(encoding="utf-8"))
    client.login(saved["account"])
    state = client.lab()["state"]
    for collection, key in (
        ("devices", "device"),
        ("testPlans", "plan"),
        ("scenarios", "scenario"),
        ("validationSuites", "suite"),
        ("suiteRuns", "report"),
    ):
        require(
            any(item["id"] == saved[key] for item in state[collection]),
            f"{collection} lost after restart.",
        )
    require(
        all(not d["connected"] for d in state["devices"]),
        "Restart retained a live connection.",
    )
    users = client.request("/api/auth/users")["users"]
    require(
        {u["username"] for u in users} == {"release_admin", "release_operator"},
        "Accounts lost after restart.",
    )
    require(
        next(r for r in state["suiteRuns"] if r["id"] == saved["report"])["status"]
        == "passed",
        "Saved verdict changed.",
    )
    archive.write_text(json.dumps(client.lab("/workspace/backup")), encoding="utf-8")
    print(
        "PASS: restart preserves accounts, libraries, and reports; transports disconnected; archive exported.",
        flush=True,
    )


def restore(client, archive):
    account = client.fresh_admin("recovery_admin")
    payload = dict(
        archive=json.loads(archive.read_text(encoding="utf-8")),
        policy="copy",
        includeHistory=True,
    )
    preview = client.lab("/workspace/preview", payload)["preview"]
    state = client.lab(
        "/workspace/import",
        {**payload, **{k: preview[k] for k in ("revision", "digest")}},
    )["state"]
    require(
        all(not d["connected"] for d in state["devices"]),
        "Imported transports connected automatically.",
    )
    require(
        [u["username"] for u in client.request("/api/auth/users")["users"]]
        == [account["username"]],
        "Import changed target accounts.",
    )
    suite = next(
        s for s in state["validationSuites"] if s["name"] == "Release acceptance"
    )
    device = next(d for d in state["devices"] if d["name"] == "Release temperature")
    require(
        any(
            r["status"] == "passed" and r["suite"]["name"] == suite["name"]
            for r in state["suiteRuns"]
        ),
        "Archived report missing.",
    )
    client.run_suite(suite["id"], device["id"])
    print(
        "PASS: separate installation imports history, keeps its own accounts, and reruns the restored suite.",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("seed", "verify", "restore"))
    parser.add_argument("--url", default="http://workbench")
    parser.add_argument(
        "--checkpoint", type=Path, default=Path("/data/release-check.json")
    )
    parser.add_argument(
        "--archive", type=Path, default=Path("/data/release-archive.json")
    )
    parser.add_argument("--mqtt", action="store_true")
    parser.add_argument("--web", action="store_true")
    args = parser.parse_args()
    client = Client(args.url)
    require(client.request("/api/health")["status"] == "ok", "Health probe failed.")
    if args.web:
        client.web_assets()
    if args.phase == "seed":
        seed(client, args.checkpoint, args.mqtt)
    elif args.phase == "verify":
        verify(client, args.checkpoint, args.archive)
    else:
        restore(client, args.archive)


if __name__ == "__main__":
    main()
