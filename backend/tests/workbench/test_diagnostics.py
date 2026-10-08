import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.lab import LabError


def test_diagnostics_faults_recovery_and_persistence(tmp_path):
    path = str(tmp_path / 'diagnostics.sqlite3')
    app = create_app('testing', {'LAB_DB_PATH': path, 'LAB_WORKER': False})
    lab = app.extensions['lab']
    client = app.test_client()
    device = lab.state['devices'][0]
    url = f"/api/lab/devices/{device['id']}/diagnostics"
    assert client.post(url, json={}).status_code == 200
    assert device['diagnostics'][0]['status'] == 'failed'
    assert not device.get('lastContactAt')
    lab.connect(device['id'], True)
    original = device['value']
    assert client.post(url, json={}).status_code == 200
    assert device['diagnostics'][0]['status'] == 'passed'
    assert device['value'] == original
    contact = device['lastContactAt']
    lab.fault(device['id'], 'timeout')
    lab.diagnose(device['id'])
    assert device['diagnostics'][0]['status'] == 'failed'
    assert device['lastContactAt'] == contact
    lab.fault(device['id'], 'out-of-range')
    lab.diagnose(device['id'])
    assert device['diagnostics'][0]['status'] == 'warning'
    assert device['lastError'] is None
    lab.fault(device['id'], 'none')
    for _ in range(6):
        lab.diagnose(device['id'])
    assert len(device['diagnostics']) == 5
    assert device['diagnostics'][0]['status'] == 'passed'
    lab.start(device['id'], 'control')
    with pytest.raises(LabError) as error:
        lab.diagnose(device['id'])
    assert error.value.status == 409
    lab.cancel()
    lab.close()
    restarted = create_app('testing', {'LAB_DB_PATH': path, 'LAB_WORKER': False})
    stored = restarted.extensions['lab'].state['devices'][0]
    assert len(stored['diagnostics']) == 5
    assert not stored['connected']
    restarted.extensions['lab'].close()


def test_real_adapter_check_reads_without_writing(tmp_path):
    app = create_app('testing', {'LAB_DB_PATH': str(tmp_path / 'real.sqlite3'), 'LAB_WORKER': False})
    lab = app.extensions['lab']
    device = lab.state['devices'][1]
    device.update(adapter='serial', connected=True, value=20, enabled=True)

    class ReadOnlyAdapter:
        calls = 0
        def read(self):
            self.calls += 1
            return 20
        def write(self, value):
            pytest.fail('Diagnostics must not write an output')
        def close(self):
            pass

    adapter = ReadOnlyAdapter()
    lab.adapters[device['id']] = adapter
    lab.diagnose(device['id'])
    assert adapter.calls == 1
    assert device['value'] == 20 and device['enabled']
    assert device['diagnostics'][0]['status'] == 'passed'
    lab.close()
