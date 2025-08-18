#!/usr/bin/env python3
"""
Rewrite doubled frontend API paths to /api/<module>/...

Patterns handled:
  /emulators/api/emulators/ -> /api/emulators/
  /hardware/api/hardware/   -> /api/hardware/
  /users/api/users/         -> /api/users/
  /settings/api/settings/   -> /api/settings/
  /test-plans/api/test-plans/ -> /api/test-plans/
  /logs/api/logs/           -> /api/logs/
  /mqtt/api/mqtt/           -> /api/mqtt/
  /valves/api/valves/       -> /api/valves/
  /reports/api/reports/     -> /api/reports/
  /upload/api/...           -> /api/...
  /configurations/api/configurations/ -> /api/configurations/
"""

import re
from pathlib import Path

MODULES = [
    "emulators", "hardware", "users", "settings", "test-plans",
    "logs", "mqtt", "valves", "reports", "upload", "configurations",
    "dashboard", "peripherals", "system-status",
]

def rewrite_text(s: str) -> str:
    for m in MODULES:
        s = re.sub(rf"/{m}/api/{m}/", f"/api/{m}/", s)
        s = re.sub(rf"/api/{m}/api/{m}/", f"/api/{m}/", s)
        s = re.sub(rf"/{m}/api/", f"/api/{m}/", s)
    return s

def main():
    fe = Path("frontend/src")
    ts_tsx = list(fe.rglob("*.ts")) + list(fe.rglob("*.tsx"))
    changed = False
    for f in ts_tsx:
        txt = f.read_text(encoding="utf-8")
        new = rewrite_text(txt)
        if new != txt:
            f.write_text(new, encoding="utf-8")
            print(f"[UPDATED] {f}")
            changed = True
    if not changed:
        print("No frontend path updates detected.")

if __name__ == "__main__":
    main()
