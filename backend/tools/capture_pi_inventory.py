#!/usr/bin/env python3
"""Print a read-only Raspberry Pi inventory as JSON. Run on the Pi without sudo.

On the Pi: python3 capture_pi_inventory.py > pi-inventory.json

From Bash on a workstation with the Pi's verified key in known_hosts:
    ssh -T -o StrictHostKeyChecking=yes -o BatchMode=yes -o ConnectTimeout=10 \
        USER@PI_HOST python3 - < backend/tools/capture_pi_inventory.py > pi-inventory.json

Interfaces describe categories visible to Linux. They cannot identify hardware
behind a bus, verify wiring, or describe interfaces Linux has disabled.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys

INTERFACE_PATTERNS = {
    "gpio": (
        "sys/bus/gpio/devices/gpiochip*",
        "sys/class/gpio/gpiochip*",
        "dev/gpiochip*",
    ),
    "i2c": ("sys/bus/i2c/devices/i2c-*", "dev/i2c-*"),
    "spi": ("sys/class/spi_master/spi[0-9]*", "dev/spidev*"),
    "serial": (
        "dev/serial[0-9]*",
        "sys/class/tty/ttyAMA*",
        "sys/class/tty/ttyUSB*",
        "sys/class/tty/ttyACM*",
    ),
    "usb": ("sys/bus/usb/devices/usb[0-9]*",),
    "bluetooth": ("sys/class/bluetooth/hci[0-9]*",),
}
SERVICE_UNITS = ("NetworkManager.service", "mosquitto.service", "ssh.service")
SERVICE_PROPERTIES = {
    "LoadState": "loadState",
    "ActiveState": "activeState",
    "UnitFileState": "unitFileState",
}
FIRMWARE_FIELDS = ("videoCoreRevision", "startElfSha256")
CONFIG_FILES = {"bootConfigSha256": "config.txt", "bootCmdlineSha256": "cmdline.txt"}
STATE_TOKEN = re.compile(r"[a-z][a-z0-9-]{0,39}")
REVISION = re.compile(r"^version ([a-fA-F0-9]{7,64})(?: |$)", re.MULTILINE)


def read_model(root):
    for path in ("sys/firmware/devicetree/base/model", "proc/device-tree/model"):
        try:
            model = (root / path).read_bytes().rstrip(b"\0\r\n ").decode("utf-8")
        except FileNotFoundError:
            continue
        if model.startswith("Raspberry Pi "):
            return model
    raise ValueError("A Raspberry Pi device-tree model is required.")


def read_os_release(root):
    for path in ("etc/os-release", "usr/lib/os-release"):
        try:
            contents = (root / path).read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        values = {}
        for line in contents.splitlines():
            key, _, raw_value = line.partition("=")
            if key in ("ID", "VERSION_ID"):
                tokens = shlex.split(raw_value, comments=True)
                if len(tokens) == 1 and tokens[0]:
                    values[key] = tokens[0]
        return values.get("ID", "linux"), values.get("VERSION_ID", "unknown")
    raise ValueError("Linux distribution information is unavailable.")


def read_memory_mib(root):
    with (root / "proc/meminfo").open(encoding="ascii") as stream:
        for line in stream:
            name, _, raw_value = line.partition(":")
            if name == "MemTotal":
                value, units = raw_value.split()
                if units == "kB" and int(value) >= 1024:
                    return int(value) // 1024
                break
    raise ValueError("Linux-visible memory is unavailable.")


def read_interfaces(root):
    interfaces = set()
    for category, patterns in INTERFACE_PATTERNS.items():
        if any(entry.exists() for pattern in patterns for entry in root.glob(pattern)):
            interfaces.add(category)
    for interface in (root / "sys/class/net").glob("*"):
        if (interface / "wireless").exists() or (interface / "phy80211").exists():
            interfaces.add("wifi")
        elif (interface / "device").exists():
            try:
                if (interface / "type").read_text(encoding="ascii").strip() == "1":
                    interfaces.add("ethernet")
            except FileNotFoundError:
                # An adapter can disappear during collection.
                continue
    return sorted(interfaces)


def command_output(arguments):
    try:
        return subprocess.run(
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
            errors="replace",
            timeout=3,
            check=False,
            env=os.environ | {"LC_ALL": "C", "SYSTEMD_COLORS": "0"},
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def read_services(run):
    output = run(
        [
            "systemctl",
            "show",
            "--no-pager",
            "--property=Id,LoadState,ActiveState,UnitFileState",
            *SERVICE_UNITS,
        ]
    )
    services = dict.fromkeys(SERVICE_UNITS)
    for block in output.strip().split("\n\n"):
        details = dict(line.split("=", 1) for line in block.splitlines() if "=" in line)
        identity = details.get("Id")
        if identity not in services:
            continue
        values = {
            key: token if STATE_TOKEN.fullmatch(token) else None
            for system_key, key in SERVICE_PROPERTIES.items()
            for token in [details.get(system_key, "")]
        }
        if values["loadState"] and values["activeState"]:
            services[identity] = values
    return services


def hash_boot_file(root, name, maximum):
    for directory in ("boot/firmware", "boot"):
        path = root / directory / name
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
                return None
            with path.open("rb") as stream:
                data = stream.read(maximum + 1)
            after = path.lstat()
            if len(data) == info.st_size and all(
                getattr(info, field) == getattr(after, field)
                for field in (
                    "st_dev",
                    "st_ino",
                    "st_size",
                    "st_mtime_ns",
                    "st_ctime_ns",
                )
            ):
                return hashlib.sha256(data).hexdigest()
            return None
        except FileNotFoundError:
            continue
        except OSError:
            return None
    return None


def collect_inventory(root, system, run=command_output):
    os_id, os_version = read_os_release(root)
    model = read_model(root)
    architecture = system.machine.lower()
    revision = REVISION.search(run(["vcgencmd", "version"]))
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schemaVersion": 2,
        "capturedAt": captured_at.replace("+00:00", "Z"),
        "model": model,
        "architecture": "aarch64" if architecture == "arm64" else architecture,
        "kernel": system.release,
        "osId": os_id,
        "osVersion": os_version,
        "memoryMiB": read_memory_mib(root),
        "interfaces": read_interfaces(root),
        "observations": {
            "firmware": {
                "videoCoreRevision": revision[1].lower() if revision else None,
                "startElfSha256": hash_boot_file(root, "start.elf", 16 * 1024 * 1024),
            },
            "services": read_services(run),
            "configuration": {
                key: hash_boot_file(root, filename, 1024 * 1024)
                for key, filename in CONFIG_FILES.items()
            },
        },
    }


def main():
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    if sys.platform != "linux":
        print(
            "Run the inventory collector on a Raspberry Pi running Linux.",
            file=sys.stderr,
        )
        return 1
    try:
        inventory = collect_inventory(Path("/"), os.uname())
    except OSError:
        print("The Linux inventory files could not be read.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Inventory could not be collected. {error}", file=sys.stderr)
        return 1
    print(json.dumps(inventory, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
