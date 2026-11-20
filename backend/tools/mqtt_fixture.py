"""Run a simulated valve or a configurable MQTT component on a local broker."""

import argparse
from collections import OrderedDict
from dataclasses import dataclass
import heapq
from itertools import count
import json
from pathlib import Path
import re
import signal
import sys
import threading
import time

import paho.mqtt.client as mqtt

MAX_MODEL_BYTES = 65536
MAX_REPLY_DELAY_MS = 5000
MAX_PENDING_REPLIES = 128
MAX_REMEMBERED_REQUESTS = 512
STATE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")
COMMANDS = ("read", "set")
INVALID_OUTPUT = "Valve value must be a finite number from 0 to 100."
REQUEST_CONFLICT = "Request ID already used for a different command."


def number_in_range(value, low=0, high=100):
    return type(value) in (int, float) and low <= value <= high


def object_fields(value, required, optional=()):
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    if missing := sorted(set(required) - value.keys()):
        raise ValueError(f"Missing fields: {', '.join(missing)}.")
    if unexpected := sorted(value.keys() - set(required) - set(optional)):
        raise ValueError(f"Unknown fields: {', '.join(unexpected)}.")
    return value


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate JSON field: {key}.")
        value[key] = item
    return value


@dataclass(frozen=True)
class OutputRange:
    minimum: float = 0
    maximum: float = 100
    includes_maximum: bool = True

    def matches(self, value):
        return self.minimum <= value and (
            value < self.maximum or (self.includes_maximum and value == self.maximum)
        )

    def overlaps(self, other):
        boundary = max(self.minimum, other.minimum)
        return self.matches(boundary) and other.matches(boundary)


def parse_range(value):
    condition = object_fields(value, (), ("atLeast", "below", "exactly"))
    if "exactly" in condition:
        exact = condition["exactly"]
        if len(condition) != 1 or not number_in_range(exact):
            raise ValueError("exactly must be 0–100 and used by itself.")
        return OutputRange(exact, exact)
    minimum = condition.get("atLeast", 0)
    maximum = condition.get("below", 100)
    if not number_in_range(minimum) or not number_in_range(maximum):
        raise ValueError("atLeast and below must be 0–100.")
    exclusive = "below" in condition
    if exclusive and minimum >= maximum:
        raise ValueError("atLeast must be smaller than below.")
    return OutputRange(minimum, maximum, not exclusive)


@dataclass(frozen=True)
class Reply:
    kind: str
    delay_ms: int = 0
    value: float | str | None = None

    def payload(self, output):
        if self.kind == "drop":
            return None
        if self.kind == "error":
            return {"error": self.value}
        return {"value": output if self.value is None else self.value}


def parse_reply(value):
    reply = object_fields(value, ("type",), ("delayMs", "value", "message"))
    kind = reply["type"]
    delay = reply.get("delayMs", 0)
    if type(delay) is not int or not 0 <= delay <= MAX_REPLY_DELAY_MS:
        raise ValueError(f"delayMs must be an integer from 0 to {MAX_REPLY_DELAY_MS}.")
    if kind == "value":
        measurement = reply.get("value")
        if "message" in reply or (
            "value" in reply and not number_in_range(measurement, -1e6, 1e6)
        ):
            raise ValueError(
                "Value replies accept only an optional finite measurement."
            )
        return Reply(kind, delay, measurement)
    if kind == "error":
        message = reply.get("message")
        if (
            "value" in reply
            or not isinstance(message, str)
            or not message.strip()
            or len(message) > 160
        ):
            raise ValueError(
                "Error replies require a message of at most 160 characters."
            )
        return Reply(kind, delay, message)
    if kind == "drop" and len(reply) == 1:
        return Reply(kind)
    raise ValueError("Reply must be value, error, or drop without additional fields.")


@dataclass(frozen=True)
class Transition:
    command: str
    target: str
    condition: OutputRange
    update_output: bool
    reply: Reply


def parse_transition(raw, state_names):
    value = object_fields(raw, ("command", "target", "reply"), ("when", "updateOutput"))
    command = value["command"]
    target = value["target"]
    update = value.get("updateOutput", False)
    if command not in COMMANDS:
        raise ValueError("command must be read or set.")
    if not isinstance(target, str) or target not in state_names:
        raise ValueError("target must name a declared state.")
    if type(update) is not bool:
        raise ValueError("updateOutput must be true or false.")
    if command == "read" and ("when" in value or update):
        raise ValueError("Only set transitions can use when or update the output.")
    condition = parse_range(value.get("when", {}))
    return Transition(command, target, condition, update, parse_reply(value["reply"]))


class Model:
    def __init__(self, initial_state, initial_value, states):
        self.state = initial_state
        self.output = initial_value
        self.states = states

    def execute(self, command, value=0):
        for transition in self.states[self.state]:
            if transition.command == command and transition.condition.matches(value):
                if transition.update_output:
                    self.output = value
                self.state = transition.target
                return transition.reply.payload(self.output), transition.reply.delay_ms
        return {"error": f"{command} is unavailable in state {self.state}."}, 0


class RequestReplies:
    """Remember outcomes per fixture topic on the serialized MQTT callback thread."""

    def __init__(self):
        self.completed = OrderedDict()

    def resolve(self, request, execute):
        request_id, command, value = request
        if command == "set" and not number_in_range(value):
            return {"id": request_id, "error": INVALID_OUTPUT}, 0
        key = (command, value)
        if request_id in self.completed:
            previous_key, reply = self.completed[request_id]
            if previous_key != key:
                return {"id": request_id, "error": REQUEST_CONFLICT}, 0
            return reply, 0
        payload, delay = execute(command, value)
        reply = {"id": request_id, **payload} if payload is not None else None
        self.completed[request_id] = (key, reply)
        if len(self.completed) > MAX_REMEMBERED_REQUESTS:
            self.completed.popitem(last=False)
        return reply, delay


def load_model(path):
    if not path.is_file():
        raise ValueError("Model path must point to a JSON file.")
    with path.open("rb") as source:
        content = source.read(MAX_MODEL_BYTES + 1)
    if len(content) > MAX_MODEL_BYTES:
        raise ValueError("Model exceeds the 64 KiB limit.")
    raw = object_fields(
        json.loads(content, object_pairs_hook=unique_object),
        ("schemaVersion", "initialState", "initialValue", "states"),
    )
    if type(raw["schemaVersion"]) is not int or raw["schemaVersion"] != 1:
        raise ValueError("schemaVersion must be 1.")
    initial = raw["initialState"]
    initial_value = raw["initialValue"]
    states = raw["states"]
    if not isinstance(states, dict) or not 1 <= len(states) <= 24:
        raise ValueError("A model must declare 1–24 named states.")
    if any(not STATE_NAME.fullmatch(state) for state in states):
        raise ValueError(
            "State names must start with a letter and use letters, digits, _ or -."
        )
    if not isinstance(initial, str) or initial not in states:
        raise ValueError("initialState must name a declared state.")
    if not number_in_range(initial_value):
        raise ValueError("initialValue must be 0–100.")
    parsed = {}
    for name, rules in states.items():
        if not isinstance(rules, list) or not 1 <= len(rules) <= 16:
            raise ValueError(f"State {name} must declare 1–16 transitions.")
        transitions = []
        for index, rule in enumerate(rules, start=1):
            try:
                transition = parse_transition(rule, states)
                if any(
                    prior.command == transition.command
                    and prior.condition.overlaps(transition.condition)
                    for prior in transitions
                ):
                    raise ValueError(f"Overlapping {transition.command} conditions.")
            except ValueError as error:
                raise ValueError(
                    f"State {name}, transition {index}: {error}"
                ) from error
            transitions.append(transition)
        parsed[name] = transitions
    return Model(initial, initial_value, parsed)


class DelayedReplies:
    def __init__(self, publish):
        self.publish = publish
        self.condition = threading.Condition()
        self.pending = []
        self.order = count()
        self.closed = False
        self.worker = threading.Thread(target=self.run, name="mqtt-fixture-replies")

    def has_capacity(self):
        with self.condition:
            return len(self.pending) < MAX_PENDING_REPLIES

    def schedule(self, delay_ms, reply):
        with self.condition:
            due = time.monotonic() + delay_ms / 1000
            heapq.heappush(self.pending, (due, next(self.order), reply))
            self.condition.notify()

    def run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or self.pending)
                if self.closed:
                    return
                remaining = self.pending[0][0] - time.monotonic()
                if remaining > 0:
                    self.condition.wait(remaining)
                    continue
                _, _, reply = heapq.heappop(self.pending)
            self.publish(reply)

    def close(self):
        with self.condition:
            self.closed = True
            self.pending.clear()
            self.condition.notify()
        self.worker.join()


def decode_request(message):
    if getattr(message, "retain", False) or len(message.payload) > 4096:
        return None
    try:
        request = json.loads(message.payload, object_pairs_hook=unique_object)
    except (ValueError, RecursionError):
        return None
    if not isinstance(request, dict):
        return None
    request_id = request.get("id")
    command = request.get("command")
    if command not in COMMANDS or not isinstance(request_id, str):
        return None
    if not 1 <= len(request_id) <= 128:
        return None
    return request_id, command, request.get("value") if command == "set" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--topic", default="lab/demo-valve")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="Probe with a correlated read."
    )
    mode.add_argument(
        "--model", type=Path, help="Load a declarative state machine from JSON."
    )
    args = parser.parse_args()
    if args.check:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from Hardware_Tester_App.transports import MQTTTransport

        peer = MQTTTransport(
            {"endpoint": f"mqtt://{args.broker}:{args.port}/{args.topic}"}
        )
        try:
            peer.connect()
        finally:
            peer.close()
        return
    model = None
    if args.model:
        try:
            model = load_model(args.model)
        except (OSError, ValueError, RecursionError) as error:
            parser.error(str(error))

    value = 0
    stopped = threading.Event()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if model is not None:
        client.max_queued_messages_set(MAX_PENDING_REPLIES * 2)

    def publish(reply):
        client.publish(args.topic + "/reply", json.dumps(reply), qos=1, retain=False)

    delayed = DelayedReplies(publish) if model is not None else None
    replies = RequestReplies()

    def execute(command, requested):
        nonlocal value
        if model is not None:
            if not delayed.has_capacity():
                return {"error": "Fixture reply queue is full."}, 0
            return model.execute(command, requested)
        if command == "set":
            value = requested
        return {"value": value}, 0

    def connected(client, userdata, flags, reason, properties):
        if reason.is_failure:
            print(f"Connection rejected: {reason}", flush=True)
            stopped.set()
            return
        client.subscribe(args.topic + "/command", qos=1)
        peer = "State machine" if model is not None else "Mock valve"
        print(
            f"{peer} ready: mqtt://{args.broker}:{args.port}/{args.topic}", flush=True
        )

    def message(client, userdata, msg):
        request = decode_request(msg)
        if request is None:
            return
        reply, delay = replies.resolve(request, execute)
        if reply is not None:
            if delay:
                delayed.schedule(delay, reply)
            else:
                publish(reply)

    client.on_connect = connected
    client.on_message = message
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    client.connect(args.broker, args.port)
    if delayed is not None:
        delayed.worker.start()
    try:
        client.loop_start()
        stopped.wait()
    finally:
        if delayed is not None:
            delayed.close()
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
