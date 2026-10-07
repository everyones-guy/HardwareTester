import json
from pathlib import Path
import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.services.peripheral_service import PeripheralService


@pytest.fixture
def app(tmp_path):
    app = create_app('testing', {'LAB_DB_PATH': str(tmp_path / 'catalog.sqlite3'), 'LAB_WORKER': False})
    yield app
    app.extensions['lab'].close()


def test_original_controller_import_and_append(app):
    client = app.test_client()
    source = json.loads((Path(__file__).parents[2] / 'Hardware_Tester_App/uploads/saved_configs/dynamic_controller_blueprint_test3.json').read_text())
    preview = client.post('/api/lab/blueprints/preview', json={'configuration': source})
    assert preview.status_code == 200
    mapped = preview.json['preview']
    assert len(mapped['devices']) == 2
    assert any('unsupported type' in w for w in mapped['warnings'])
    assert 'auth' not in json.dumps(mapped['configuration'])
    saved = client.post('/api/lab/blueprints', json={'configuration': source})
    identity = saved.json['blueprintId']
    original = saved.json['state']['devices']
    applied = client.post(f'/api/lab/blueprints/{identity}/apply', json={})
    assert applied.json['state']['devices'][:3] == original
    assert len(applied.json['state']['devices']) == 5
    assert all(not d['connected'] and d['adapter'] == 'simulation' for d in applied.json['state']['devices'][3:])
    assert len(applied.json['state']['peripherals']) == 2
    assert any(p['properties'].get('threshold') == 75 for p in applied.json['state']['peripherals'])


def test_peripheral_service_crud_and_threshold_execution(app, monkeypatch):
    client = app.test_client()
    lab = app.extensions['lab']
    d = lab.snapshot()['devices'][0]
    called = []
    original = PeripheralService.add_peripheral
    def tracked(*args, **kwargs):
        called.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(PeripheralService, 'add_peripheral', tracked)
    result = client.post('/api/lab/peripherals', json={'name': 'Strict range', 'type': 'Sensor', 'device_id': d['id'], 'properties': {'threshold': {'min': 0, 'max': 10}}})
    assert called and result.status_code == 200
    identity = result.json['peripheralId']
    assert client.get('/api/lab/peripherals').json['peripherals'][0]['id'] == identity
    lab.connect(d['id'], True)
    lab.start(d['id'], 'smoke')
    assert client.patch(f'/api/lab/peripherals/{identity}', json={'version': 1, 'properties': {}}).status_code == 409
    while lab.active:
        lab.advance()
    assert lab.snapshot()['runs'][0]['status'] == 'failed'
    assert client.patch(f'/api/lab/peripherals/{identity}', json={'version': 1, 'properties': {'threshold': 50}}).status_code == 200
    assert client.patch(f'/api/lab/peripherals/{identity}', json={'version': 1, 'properties': {}}).status_code == 409
    assert client.delete(f'/api/lab/peripherals/{identity}', json={'version': 2}).status_code == 200
    assert not lab.snapshot()['peripherals']


def test_capture_restart_reset_and_cascade(app):
    lab = app.extensions['lab']
    client = app.test_client()
    result = client.post('/api/lab/blueprints/capture', json={'name': 'Saved bench'})
    identity = result.json['blueprintId']
    path = app.config['LAB_DB_PATH']
    lab.close()
    restarted = create_app('testing', {'LAB_DB_PATH': path, 'LAB_WORKER': False})
    try:
        lab = restarted.extensions['lab']
        assert lab.snapshot()['blueprints'][0]['id'] == identity
        lab.reset()
        assert lab.snapshot()['blueprints'][0]['id'] == identity
        client = restarted.test_client()
        d = lab.snapshot()['devices'][0]
        client.post('/api/lab/peripherals', json={'name': 'Attached', 'type': 'Sensor', 'device_id': d['id'], 'properties': {}})
        lab.remove(d['id'])
        assert not lab.snapshot()['peripherals']
    finally:
        restarted.extensions['lab'].close()


@pytest.mark.parametrize('source', [None, [], {}, {'name': 'bad', 'peripherals': [{'name': 'bad', 'type': 'ph_sensor'}]}, {'name': 'bad', 'peripherals': [{'name': 'T', 'type': 'temperature', 'threshold': {'min': 10, 'max': 0}}]}])
def test_invalid_import_has_no_mutation(app, source):
    before = app.extensions['lab'].snapshot()
    response = app.test_client().post('/api/lab/blueprints', json={'configuration': source})
    assert response.status_code == 400
    assert app.extensions['lab'].snapshot() == before


def test_capacity_apply_is_atomic(app):
    client = app.test_client()
    saved = client.post('/api/lab/blueprints', json={'configuration': {'name': 'Too many', 'devices': [{'kind': 'relay', 'name': f'R{i}'} for i in range(100)]}})
    before = app.extensions['lab'].snapshot()
    assert client.post(f"/api/lab/blueprints/{saved.json['blueprintId']}/apply", json={}).status_code == 409
    assert app.extensions['lab'].snapshot() == before
