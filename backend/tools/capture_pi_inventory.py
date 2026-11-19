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
import json
import os
from pathlib import Path
import shlex
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


def collect_inventory(root, system):
    os_id, os_version = read_os_release(root)
    architecture = system.machine.lower()
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schemaVersion": 1,
        "capturedAt": captured_at.replace("+00:00", "Z"),
        "model": read_model(root),
        "architecture": "aarch64" if architecture == "arm64" else architecture,
        "kernel": system.release,
        "osId": os_id,
        "osVersion": os_version,
        "memoryMiB": read_memory_mib(root),
        "interfaces": read_interfaces(root),
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
