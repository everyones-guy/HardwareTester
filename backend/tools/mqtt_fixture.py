"""A mock valve peer for a local MQTT broker. No physical hardware is controlled."""
import argparse
import json
import signal
import threading
import paho.mqtt.client as mqtt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--broker', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--topic', default='lab/demo-valve')
    args = parser.parse_args()
    value = 0
    stopped = threading.Event()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    def connected(client, userdata, flags, reason, properties):
        if reason.is_failure: print(f'Connection rejected: {reason}', flush=True); stopped.set(); return
        client.subscribe(args.topic + '/command', qos=1)
        print(f'Mock valve ready: mqtt://{args.broker}:{args.port}/{args.topic}', flush=True)
    def message(client, userdata, msg):
        nonlocal value
        try:
            request = json.loads(msg.payload)
            if request.get('command') == 'set': value = request['value']
            if request.get('command') not in ('set', 'read'): return
            client.publish(args.topic + '/reply', json.dumps({'id': request['id'], 'value': value}), qos=1, retain=False)
        except (ValueError, KeyError, TypeError): pass
    client.on_connect = connected; client.on_message = message
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    client.connect(args.broker, args.port)
    client.loop_start()
    try: stopped.wait()
    finally: client.disconnect(); client.loop_stop()


if __name__ == '__main__': main()
