import json
import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.lab import Lab, LabError
from Hardware_Tester_App.transports import SimulationTransport, TransportError


@pytest.fixture
def app(tmp_path):
    app = create_app('testing', {'LAB_DB_PATH': str(tmp_path / 'lab.sqlite3'), 'LAB_WORKER': False})
    yield app
    app.extensions['lab'].close()


def post(client, url, payload=None):
    return client.post('/api/lab' + url, json=payload or {})


@pytest.mark.parametrize('kind', ['temperature', 'valve', 'relay'])
@pytest.mark.parametrize('plan', ['smoke', 'control'])
def test_healthy_plans(app, kind, plan):
    lab = app.extensions['lab']
    d = next(d for d in lab.snapshot()['devices'] if d['kind'] == kind)
    lab.connect(d['id'], True)
    original = d['value']
    lab.start(d['id'], plan)
    while lab.active:
        lab.advance()
    run = lab.snapshot()['runs'][0]
    assert run['status'] == 'passed'
    assert all(s['status'] == 'passed' for s in run['steps'])
    assert lab.device(d['id'])['value'] == original


@pytest.mark.parametrize('fault', ['timeout', 'out-of-range'])
def test_faults_fail(app, fault):
    lab = app.extensions['lab']
    d = lab.snapshot()['devices'][0]
    lab.connect(d['id'], True)
    lab.fault(d['id'], fault)
    lab.start(d['id'], 'smoke')
    for _ in range(3):
        lab.advance()
    assert lab.snapshot()['runs'][0]['status'] == 'failed'


def test_cancel_restores_output(app):
    lab = app.extensions['lab']
    d = lab.snapshot()['devices'][1]
    lab.connect(d['id'], True)
    lab.command(d['id'], 20)
    lab.start(d['id'], 'control')
    lab.advance(); lab.advance()
    assert lab.device(d['id'])['value'] == 75
    lab.cancel()
    assert lab.device(d['id'])['value'] == 20
    assert lab.snapshot()['runs'][0]['status'] == 'cancelled'


def test_restart_cancels_interrupted_run_and_preserves_results(tmp_path):
    path = tmp_path / 'persistent.sqlite3'
    lab = Lab(path, autostart=False)
    d = lab.snapshot()['devices'][1]
    lab.connect(d['id'], True)
    lab.start(d['id'], 'control')
    lab.advance(); lab.advance()
    # Simulate a process crash without invoking graceful cancellation.
    lab.connection.close()
    restored = Lab(path, autostart=False)
    assert restored.snapshot()['runs'][0]['status'] == 'cancelled'
    assert restored.device(d['id'])['value'] == 0
    assert not restored.device(d['id'])['connected']
    restored.close()


def test_api_validation_conflicts_and_export(app):
    client = app.test_client()
    assert client.get('/api/health').json['status'] == 'ok'
    d = client.get('/api/lab').json['state']['devices'][0]
    assert post(client, '/runs', {'deviceId': d['id'], 'plan': 'smoke'}).status_code == 409
    assert post(client, f"/devices/{d['id']}/connection", {'connected': 'yes'}).status_code == 400
    assert post(client, '/devices', {'name': '', 'kind': 'relay'}).status_code == 400
    assert post(client, '/devices', {'name': 'x', 'kind': 'bad'}).status_code == 400
    assert post(client, '/devices', {'name': 'x', 'kind': 'relay', 'adapter': 'serial', 'endpoint': 'COM3'}).status_code == 403
    assert post(client, '/connect-bench').status_code == 200
    assert post(client, f"/devices/{d['id']}/command", {'value': float('inf')}).status_code == 400
    assert post(client, f"/devices/{d['id']}/command", {'value': True}).status_code == 400
    assert post(client, '/runs', {'deviceId': d['id'], 'plan': 'smoke'}).status_code == 202
    assert post(client, '/runs', {'deviceId': d['id'], 'plan': 'smoke'}).status_code == 409
    assert post(client, '/reset').status_code == 409
    assert client.delete('/api/lab/devices/' + d['id'], json={}).status_code == 409
    assert post(client, '/runs/cancel').status_code == 200
    assert post(client, '/runs/cancel').status_code == 409
    assert client.get('/api/lab/export').json['workspace']['runs'][0]['status'] == 'cancelled'


def test_invalid_json_origin_and_token(app):
    client = app.test_client()
    assert client.post('/api/lab/reset').status_code == 415
    assert client.post('/api/lab/reset', json=[]).status_code == 400
    assert client.post('/api/lab/reset', json={}, headers={'Origin': 'https://untrusted.example'}).status_code == 403
    app.config['LAB_API_TOKEN'] = 'test-token'
    assert client.get('/api/lab').status_code == 401
    assert client.get('/api/lab', headers={'Authorization': 'Bearer test-token'}).status_code == 200
    assert client.get('/api/health').status_code == 200
    assert client.get('/api/not-real').status_code == 404


def test_spa_routes_and_missing_assets(app, tmp_path):
    build = tmp_path / 'build'; build.mkdir(); (build / 'index.html').write_text('<html>workbench</html>')
    app.config['FRONTEND_BUILD'] = str(build)
    client = app.test_client()
    for route in ('/', '/logs', '/settings', '/results'):
        assert client.get(route).status_code == 200
    assert client.get('/assets/missing.js').status_code == 404
    assert client.get('/api/lab/missing').status_code == 404


def test_revision_increases_across_reset(app):
    lab = app.extensions['lab']; revision = lab.snapshot()['revision']
    lab.reset()
    assert lab.snapshot()['revision'] > revision


def test_adapter_failure_does_not_fake_a_connection(tmp_path):
    class Broken(SimulationTransport):
        def connect(self):
            raise TransportError('Device not responding')
    lab = Lab(tmp_path / 'lab.db', autostart=False, transport_factory=Broken)
    d = lab.snapshot()['devices'][0]
    with pytest.raises(LabError, match='Device not responding'):
        lab.connect(d['id'], True)
    assert not lab.device(d['id'])['connected']
    assert lab.snapshot()['logs'][0]['level'] == 'error'
    lab.close()


def test_real_adapter_response_is_checked_and_cleanup_failure_is_reported(tmp_path):
    class Mismatched:
        def __init__(self, device): self.value = 0
        def connect(self): pass
        def close(self): pass
        def read(self): return self.value
        def write(self, value): self.value = 42; return self.value
    lab = Lab(tmp_path / 'lab.db', autostart=False, allow_hardware=True, transport_factory=Mismatched)
    device_id = lab.add({'kind': 'valve', 'name': 'physical fixture', 'adapter': 'serial', 'endpoint': 'COM-MOCK'})
    lab.connect(device_id, True); lab.start(device_id, 'control')
    for _ in range(4): lab.advance()
    run = lab.snapshot()['runs'][0]
    assert run['status'] == 'failed'
    assert any('mismatch' in s['detail'] for s in run['steps'])
    assert any(s['name'] == 'Cleanup original output' for s in run['steps'])
    assert 'inspect hardware' in lab.device(device_id)['lastError']
    lab.read(lab.device(device_id))
    assert 'inspect hardware' in lab.device(device_id)['safetyWarning']
    lab.close()


def test_failed_handshake_does_not_send_control_to_hardware(tmp_path):
    class Peer:
        writes = []
        def __init__(self, device): self.fail = False
        def connect(self): pass
        def close(self): pass
        def read(self):
            if self.fail: raise TransportError('response timed out')
            return 0
        def write(self, value): self.writes.append(value); return value
    lab = Lab(tmp_path / 'lab.db', autostart=False, allow_hardware=True, transport_factory=Peer)
    device_id = lab.add({'kind': 'relay', 'name': 'fixture', 'adapter': 'serial', 'endpoint': 'COM-MOCK'})
    lab.connect(device_id, True)
    lab.adapters[device_id].fail = True
    lab.start(device_id, 'control')
    for _ in range(4): lab.advance()
    assert lab.snapshot()['runs'][0]['status'] == 'failed'
    assert Peer.writes == []
    lab.close()


def test_bulk_connect_skips_physical_devices(tmp_path):
    lab = Lab(tmp_path / 'lab.db', autostart=False, allow_hardware=True)
    device_id = lab.add({'kind': 'relay', 'name': 'real relay', 'adapter': 'serial', 'endpoint': 'COM-MOCK'})
    lab.connect_bench()
    assert not lab.device(device_id)['connected']
    assert sum(d['connected'] for d in lab.snapshot()['devices']) == 3
    lab.close()
