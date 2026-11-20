"""Expose the reviewed compiled valve fixture through the Workbench MQTT protocol."""

import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import threading
import time

import paho.mqtt.client as mqtt

from tools.mqtt_fixture import RequestReplies, decode_request, number_in_range

CONTROLLER = Path("/app/bin/uisee-controller")
TOPIC = "lab/compiled-valve"
BROKER = "broker"
REPLY_TIMEOUT = 1.0
MAX_REPLY_BYTES = 128


def exchange(controller, ready, command, value):
    request = f"SET {value:.17g}" if command == "set" else "READ"
    controller.stdin.write((request + "\n").encode("ascii"))
    response = bytearray()
    deadline = time.monotonic() + REPLY_TIMEOUT
    while b"\n" not in response:
        if not ready.select(max(0, deadline - time.monotonic())):
            raise ValueError("Compiled controller reply timed out.")
        chunk = os.read(controller.stdout.fileno(), MAX_REPLY_BYTES + 1 - len(response))
        response.extend(chunk)
        if not chunk or len(response) > MAX_REPLY_BYTES:
            raise ValueError("Compiled controller returned an incomplete reply.")
    if not response.startswith(b"OK ") or response.count(b"\n") != 1:
        raise ValueError("Compiled controller rejected the request.")
    if not response.endswith(b"\n"):
        raise ValueError("Compiled controller returned an ambiguous reply.")
    observed = float(response[3:-1])
    if not number_in_range(observed):
        raise ValueError("Compiled controller returned an invalid position.")
    return observed


def main():
    stopped = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    peer = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    replies = RequestReplies()
    failed = False

    with (
        subprocess.Popen(
            [str(CONTROLLER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0
        ) as controller,
        selectors.DefaultSelector() as ready,
    ):
        ready.register(controller.stdout, selectors.EVENT_READ)

        def connected(client, userdata, flags, reason, properties):
            if reason.is_failure:
                print(
                    f"Compiled valve fixture broker rejected the connection: {reason}"
                )
                stopped.set()
                return
            client.subscribe(TOPIC + "/command", qos=1)

        def execute(command, requested):
            nonlocal failed
            if failed:
                return {
                    "error": "Compiled controller unavailable. Restart the fixture."
                }, 0
            try:
                return {"value": exchange(controller, ready, command, requested)}, 0
            except (OSError, ValueError) as error:
                failed = True
                print(f"Compiled controller failed: {error}")
                return {"error": "Compiled controller failed. Restart the fixture."}, 0

        def message(client, userdata, incoming):
            request = decode_request(incoming)
            if request is None:
                return
            reply, _ = replies.resolve(request, execute)
            client.publish(TOPIC + "/reply", json.dumps(reply), qos=1, retain=False)

        try:
            peer.on_connect = connected
            peer.on_message = message
            peer.connect(BROKER, 1883)
            peer.loop_start()
            while not stopped.wait(0.2):
                if controller.poll() is not None:
                    raise RuntimeError("Compiled controller exited.")
        finally:
            peer.disconnect()
            peer.loop_stop()
            controller.stdin.close()
            try:
                controller.wait(timeout=2)
            except subprocess.TimeoutExpired:
                controller.kill()
                controller.wait()


if __name__ == "__main__":
    main()
