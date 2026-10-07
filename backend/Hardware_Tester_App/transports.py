"""Transport boundary. No device is opened until an explicit connect command."""
import json
import math
import threading
import time
import uuid
from urllib.parse import urlparse


class TransportError(Exception):
    pass


def numeric(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise TransportError('Device response must contain a finite numeric value.')
    return value


class SimulationTransport:
    def __init__(self, device):
        self.device = device

    def connect(self):
        pass

    def close(self):
        pass

    def read(self):
        d = self.device
        if d['fault'] == 'timeout':
            raise TransportError('Simulated transport timeout: no acknowledgement received.')
        if d['fault'] == 'out-of-range':
            return 95 if d['kind'] == 'temperature' else 150
        return d['value']

    def write(self, value):
        self.read()  # A timeout must never look like a successful command.
        self.device['value'] = value
        return self.read()


class SerialTransport:
    """Newline-delimited JSON: request {id,command,value?}, reply {id,value}."""
    def __init__(self, device):
        self.device = device
        self.port = None

    def connect(self):
        import serial
        self.port = serial.Serial(self.device['endpoint'], self.device.get('baudrate', 115200), timeout=.1, write_timeout=2)
        try:
            self.read()
        except Exception:
            self.close()
            raise

    def close(self):
        if self.port:
            self.port.close()
            self.port = None

    def exchange(self, command, value=None):
        if not self.port:
            raise TransportError('Serial device is disconnected.')
        request_id = str(uuid.uuid4())
        payload = {'id': request_id, 'command': command}
        if value is not None:
            payload['value'] = value
        try:
            self.port.write((json.dumps(payload) + '\n').encode())
            deadline = time.monotonic() + 2
            buffer = bytearray()
            while time.monotonic() < deadline:
                chunk = self.port.read(1)
                if not chunk:
                    continue
                buffer.extend(chunk)
                if len(buffer) > 4096:
                    raise TransportError('Serial response exceeded 4 KB.')
                if chunk != b'\n':
                    continue
                try:
                    response = json.loads(buffer)
                except (ValueError, UnicodeDecodeError):
                    buffer.clear()
                    continue
                buffer.clear()
                if isinstance(response, dict) and response.get('id') == request_id:
                    if response.get('error'):
                        raise TransportError(str(response['error'])[:200])
                    return numeric(response.get('value'))
            raise TransportError('Serial response timed out after 2 seconds.')
        except TransportError:
            raise
        except Exception as error:
            raise TransportError(f'Serial I/O failed: {error}') from error

    def read(self):
        return self.exchange('read')

    def write(self, value):
        return self.exchange('set', value)


class MQTTTransport:
    """mqtt://broker:1883/base/topic; correlated commands and replies, never retained."""
    def __init__(self, device):
        self.device = device
        self.client = None
        self.ready = threading.Event()
        self.replied = threading.Event()
        self.pending = None
        self.value = None
        self.error = None

    def connect(self):
        import paho.mqtt.client as mqtt
        uri = urlparse(self.device['endpoint'])
        self.topic = uri.path.strip('/')
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'ht-{uuid.uuid4().hex[:12]}')
        def on_connect(client, userdata, flags, reason, properties):
            if reason.is_failure:
                self.error = f'MQTT connection rejected: {reason}'
                self.ready.set()
            else:
                client.subscribe(self.topic + '/reply', qos=1)
        def on_subscribe(client, userdata, mid, reasons, properties):
            if any(reason.is_failure for reason in reasons):
                self.error = 'MQTT reply subscription rejected.'
            self.ready.set()
        def on_message(client, userdata, message):
            try:
                if len(message.payload) > 4096 or message.retain:
                    return
                response = json.loads(message.payload)
                if isinstance(response, dict) and response.get('id') == self.pending:
                    self.error = str(response['error'])[:200] if response.get('error') else None
                    self.value = numeric(response.get('value')) if not self.error else None
                    self.replied.set()
            except (ValueError, TransportError):
                return
        self.client.on_connect = on_connect
        self.client.on_subscribe = on_subscribe
        self.client.on_message = on_message
        try:
            self.client.connect_async(uri.hostname, uri.port or 1883)
            self.client.loop_start()
            if not self.ready.wait(3):
                raise TransportError('MQTT connection/subscription timed out after 3 seconds.')
            if self.error:
                raise TransportError(self.error)
            self.read()
        except Exception:
            self.close()
            raise

    def close(self):
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            self.client = None

    def exchange(self, command, value=None):
        if not self.client or not self.client.is_connected():
            raise TransportError('MQTT broker is disconnected.')
        self.pending = str(uuid.uuid4())
        self.replied.clear()
        self.error = None
        payload = {'id': self.pending, 'command': command}
        if value is not None:
            payload['value'] = value
        result = self.client.publish(self.topic + '/command', json.dumps(payload), qos=1, retain=False)
        if result.rc != 0 or not self.replied.wait(2):
            raise TransportError('MQTT device response timed out after 2 seconds.')
        if self.error:
            raise TransportError(self.error)
        return self.value

    def read(self):
        return self.exchange('read')

    def write(self, value):
        return self.exchange('set', value)


def create_transport(device):
    return {'simulation': SimulationTransport, 'serial': SerialTransport, 'mqtt': MQTTTransport}[device['adapter']](device)
