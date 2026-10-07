import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import paho.mqtt.client as mqtt
from Hardware_Tester_App import transports


def fixture_module():
    spec = importlib.util.spec_from_file_location('fixture', Path(__file__).parents[2] / 'tools/mqtt_fixture.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('failure', [False, True])
def test_health_probe_is_read_only_and_closes_on_failure(monkeypatch, failure):
    fixture = fixture_module()
    calls = []
    class Peer:
        def __init__(self, device):
            assert device['endpoint'] == 'mqtt://broker:1883/lab/demo-valve'
        def connect(self):
            calls.append('connect')
            if failure:
                raise RuntimeError('unavailable')
        def close(self):
            calls.append('close')
    monkeypatch.setattr(transports, 'MQTTTransport', Peer)
    monkeypatch.setattr('sys.argv', ['mqtt_fixture.py', '--broker', 'broker', '--check'])
    if failure:
        with pytest.raises(RuntimeError):
            fixture.main()
    else:
        fixture.main()
    assert calls == ['connect', 'close']


def test_mock_valve_correlates_replies_and_rejects_invalid_outputs(monkeypatch):
    fixture = fixture_module()
    replies = []
    class Client:
        def __init__(self, *args): pass
        def connect(self, *args): pass
        def disconnect(self): pass
        def loop_stop(self): pass
        def publish(self, topic, payload, **options):
            assert topic == 'lab/demo-valve/reply'
            assert options == {'qos': 1, 'retain': False}
            replies.append(json.loads(payload))
        def loop_start(self):
            for request in [{'id':'a','command':'read'}, {'id':'b','command':'set','value':75}, {'id':'c','command':'set','value':True}, {'id':'d','command':'set','value':200}, {'id':'e','command':'read'}, []]:
                self.on_message(self, None, SimpleNamespace(payload=json.dumps(request).encode()))
    monkeypatch.setattr(mqtt, 'Client', Client)
    monkeypatch.setattr(fixture.signal, 'signal', lambda *args: None)
    monkeypatch.setattr(fixture.threading.Event, 'wait', lambda *args: None)
    monkeypatch.setattr('sys.argv', ['mqtt_fixture.py'])
    fixture.main()
    assert replies[0] == {'id':'a','value':0}
    assert replies[1] == {'id':'b','value':75}
    assert all('error' in r for r in replies[2:4])
    assert replies[4] == {'id':'e','value':75}
