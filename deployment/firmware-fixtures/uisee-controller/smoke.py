"""Verify the reviewed compiled fixture using the existing workbench transport."""

import hashlib
import json
from pathlib import Path
import subprocess

from Hardware_Tester_App.transports import MQTTTransport, TransportError

CONTROLLER = Path("/app/bin/uisee-controller")


def main():
    native = subprocess.run(
        [str(CONTROLLER)],
        input="READ\nSET 37.5\nSET 101\nREAD\n",
        capture_output=True,
        text=True,
        check=True,
        timeout=2,
    )
    if native.stdout.splitlines() != ["OK 0", "OK 37.5", "ERROR", "OK 37.5"]:
        raise RuntimeError("Unexpected controller protocol or target limits.")
    peer = MQTTTransport({"endpoint": "mqtt://broker:1883/lab/compiled-valve"})
    try:
        peer.connect()
        initial = peer.read()
        try:
            if peer.write(37.5) != 37.5 or peer.read() != 37.5:
                raise RuntimeError("Compiled controller did not retain its setpoint.")
            try:
                peer.write(101)
            except TransportError as error:
                if "0 to 100" not in str(error):
                    raise
            else:
                raise RuntimeError("Invalid setpoint accepted.")
            if peer.read() != 37.5:
                raise RuntimeError(
                    "Invalid setpoint unexpectedly changed controller state."
                )
        finally:
            if peer.write(initial) != initial or peer.read() != initial:
                raise RuntimeError("Failed to restore compiled fixture state.")
    finally:
        peer.close()
    print(
        json.dumps(
            {
                "fixture": "synthetic compiled valve controller",
                "artifactSha256": hashlib.sha256(CONTROLLER.read_bytes()).hexdigest(),
                "handler": "setValveTarget",
                "transport": "MQTTTransport",
                "readback": 37.5,
                "invalidSetpointRejected": True,
                "restored": initial,
                "physicalEquipmentTested": False,
            }
        )
    )


if __name__ == "__main__":
    main()
