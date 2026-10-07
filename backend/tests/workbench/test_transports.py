"""Exercise the real adapters with controlled peers; no physical outputs involved."""
import json
import socket
import struct
import threading
import pytest
from Hardware_Tester_App.transports import SerialTransport, MQTTTransport, TransportError


def test_serial_protocol_handles_partial_frames_and_ignores_stale_ids(monkeypatch):
    class DevicePort:
        def __init__(self, *args, **kwargs): self.buffer = bytearray(); self.value = 0; self.closed = False
        def write(self, payload):
            request = json.loads(payload)
            if request['command'] == 'set': self.value = request['value']
            self.buffer.extend(b'not-json\n' + json.dumps({'id': 'old', 'value': 999}).encode() + b'\n')
            self.buffer.extend(json.dumps({'id': request['id'], 'value': self.value}).encode() + b'\n')
        def read(self, size):
            if not self.buffer: return b''
            chunk = bytes(self.buffer[:size]); del self.buffer[:size]; return chunk
        def close(self): self.closed = True
    import serial
    monkeypatch.setattr(serial, 'Serial', DevicePort)
    adapter = SerialTransport({'endpoint': 'COM-TEST'})
    adapter.connect()
    assert adapter.write(75) == 75
    assert adapter.read() == 75
    port = adapter.port; adapter.close()
    assert port.closed


def test_serial_rejects_nonnumeric_response(monkeypatch):
    class InvalidPort:
        def __init__(self, *args, **kwargs): self.buffer = b''
        def write(self, payload):
            self.buffer = (json.dumps({'id': json.loads(payload)['id'], 'value': 'not-a-number'}) + '\n').encode()
        def read(self, size): value, self.buffer = self.buffer[:size], self.buffer[size:]; return value
        def close(self): pass
    import serial
    monkeypatch.setattr(serial, 'Serial', InvalidPort)
    with pytest.raises(TransportError, match='numeric'):
        SerialTransport({'endpoint': 'COM-TEST'}).connect()


def remaining_length(n):
    result = bytearray()
    while True:
        digit = n % 128; n //= 128
        result.append(digit | (128 if n else 0))
        if not n: return bytes(result)


def packet(header, body): return bytes([header]) + remaining_length(len(body)) + body


def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk: raise EOFError
        data += chunk
    return data


def test_mqtt_adapter_round_trip_over_tcp():
    # Minimal MQTT 3.1.1 peer for this adapter contract, not a production broker.
    listener = socket.socket(); listener.bind(('127.0.0.1', 0)); listener.listen()
    port = listener.getsockname()[1]
    errors = []
    def serve():
        value = 0
        try:
            with listener.accept()[0] as connection:
                while True:
                    header = recv_exact(connection, 1)[0]
                    length = 0; multiplier = 1
                    while True:
                        digit = recv_exact(connection, 1)[0]; length += (digit & 127) * multiplier
                        if not digit & 128: break
                        multiplier *= 128
                    body = recv_exact(connection, length)
                    kind = header >> 4
                    if kind == 1: connection.sendall(packet(0x20, b'\x00\x00'))
                    elif kind == 8: connection.sendall(packet(0x90, body[:2] + b'\x01'))
                    elif kind == 3:
                        topic_len = struct.unpack('!H', body[:2])[0]
                        topic = body[2:2 + topic_len].decode()
                        offset = 2 + topic_len
                        qos = (header >> 1) & 3
                        if qos:
                            connection.sendall(packet(0x40, body[offset:offset+2])); offset += 2
                        request = json.loads(body[offset:])
                        if request['command'] == 'set': value = request['value']
                        reply_topic = topic.removesuffix('/command') + '/reply'
                        encoded = reply_topic.encode()
                        response = json.dumps({'id': request['id'], 'value': value}).encode()
                        connection.sendall(packet(0x30, struct.pack('!H', len(encoded)) + encoded + response))
                    elif kind == 12: connection.sendall(packet(0xD0, b''))
                    elif kind == 14: break
        except EOFError: pass
        except Exception as error: errors.append(error)
    worker = threading.Thread(target=serve, daemon=True); worker.start()
    adapter = MQTTTransport({'endpoint': f'mqtt://127.0.0.1:{port}/lab/fixture'})
    try:
        adapter.connect()
        assert adapter.write(75) == 75
        assert adapter.read() == 75
        assert adapter.write(0) == 0
    finally:
        adapter.close(); listener.close(); worker.join(3)
    assert not worker.is_alive()
    assert not errors
