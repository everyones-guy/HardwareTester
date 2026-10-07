import time
import pytest
from Hardware_Tester_App import create_app
from Hardware_Tester_App.services.test_plan_service import TestPlanService
from Hardware_Tester_App.transports import SimulationTransport


@pytest.fixture
def app(tmp_path):
    app = create_app('testing', {'LAB_DB_PATH': str(tmp_path / 'plans.sqlite3'), 'LAB_WORKER': False})
    yield app
    app.extensions['lab'].close()


def create(client, steps, kind='valve'):
    result = client.post('/api/lab/test-plans', json={'name':'Custom plan','kind':kind,'steps':steps})
    assert result.status_code == 200
    return result.json['planId']


def run(app, identity, kind='valve'):
    lab = app.extensions['lab']
    d = next(d for d in lab.state['devices'] if d['kind'] == kind)
    lab.connect(d['id'], True)
    result = app.test_client().post('/api/lab/runs', json={'deviceId':d['id'],'plan':identity})
    assert result.status_code == 202
    while lab.active:
        lab.advance()
    return lab, d, lab.snapshot()['runs'][0]


def test_service_create_preview_run_and_snapshot(app, monkeypatch):
    calls = []
    original = TestPlanService.create_test_plan
    def tracked(*args, **kwargs):
        calls.append('create')
        return original(*args, **kwargs)
    monkeypatch.setattr(TestPlanService, 'create_test_plan', tracked)
    client = app.test_client()
    identity = create(client, [{'action':'set','value':60}, {'action':'assert_equal','value':60,'tolerance':.5}, {'action':'assert_range','min':55,'max':65}])
    assert calls == ['create']
    saved = client.get(f'/api/lab/test-plans/{identity}').json['plan']
    assert client.get('/api/lab/test-plans').json['total'] == 1
    lab, device, result = run(app, identity)
    assert result['status'] == 'passed'
    assert result['steps'][0]['name'] == 'Connection handshake'
    assert result['steps'][-1]['name'] == 'Restore initial state'
    assert device['value'] == 0
    assert result['steps'][2]['observed'] == 60
    assert result['configuration']['plan']['version'] == 1
    assert result['configuration']['plan']['steps'][0]['value'] == 60
    changed = dict(saved, name='Renamed', steps=[{'action':'read'}])
    assert client.put(f'/api/lab/test-plans/{identity}', json=changed).status_code == 200
    assert client.put(f'/api/lab/test-plans/{identity}', json=changed).status_code == 409
    assert lab.snapshot()['runs'][0]['configuration'] == result['configuration']
    assert client.delete(f'/api/lab/test-plans/{identity}', json={'version':1}).status_code == 409
    assert client.delete(f'/api/lab/test-plans/{identity}', json={'version':2}).status_code == 200
    assert lab.snapshot()['runs'][0]['configuration']['plan']['id'] == identity


def test_failed_assertion_skips_subsequent_output_and_restores(app):
    identity = create(app.test_client(), [{'action':'set','value':60}, {'action':'assert_equal','value':20}, {'action':'set','value':90}])
    _, device, result = run(app, identity)
    assert result['status'] == 'failed'
    assert 'Expected 20' in result['steps'][2]['detail']
    assert result['steps'][2]['observed'] == 60
    assert 'skipped' in result['steps'][3]['detail']
    assert device['value'] == 0


def test_wait_yields_and_cancel_restores(app):
    lab = app.extensions['lab']
    client = app.test_client()
    identity = create(client, [{'action':'set','value':75}, {'action':'wait','seconds':30}, {'action':'read'}])
    d = lab.state['devices'][1]
    lab.connect(d['id'], True)
    client.post(f'/api/lab/test-plans/{identity}/run', json={'deviceId':d['id']})
    lab.advance(); lab.advance(); lab.advance()
    assert lab.active['index'] == 2 and d['value'] == 75
    plan = client.get(f'/api/lab/test-plans/{identity}').json['plan']
    assert client.put(f'/api/lab/test-plans/{identity}', json=plan).status_code == 409
    lab.cancel()
    assert d['value'] == 0
    assert lab.snapshot()['runs'][0]['status'] == 'cancelled'


def test_profile_mismatch_and_fault_never_set_output(app):
    client = app.test_client()
    identity = create(client, [{'action':'set','value':75}])
    lab = app.extensions['lab']
    temp, valve = lab.state['devices'][:2]
    lab.connect(temp['id'], True)
    assert client.post('/api/lab/runs', json={'deviceId':temp['id'],'plan':identity}).status_code == 409
    lab.connect(valve['id'], True)
    lab.fault(valve['id'], 'timeout')
    lab.start(valve['id'], identity)
    while lab.active: lab.advance()
    assert lab.snapshot()['runs'][0]['status'] == 'failed'
    assert valve['value'] == 0
    assert 'skipped' in lab.snapshot()['runs'][0]['steps'][1]['detail']


def test_saved_plan_and_run_survive_restart_and_reset(app):
    identity = create(app.test_client(), [{'action':'read'}])
    lab, _, result = run(app, identity)
    path = app.config['LAB_DB_PATH']
    lab.close()
    restarted = create_app('testing', {'LAB_DB_PATH':path,'LAB_WORKER':False})
    try:
        lab = restarted.extensions['lab']
        assert lab.snapshot()['runs'][0]['configuration'] == result['configuration']
        lab.reset()
        assert lab.snapshot()['testPlans'][0]['id'] == identity
    finally: restarted.extensions['lab'].close()


def test_per_step_timeout_is_enforced_and_transport_setting_restored(app):
    lab = app.extensions['lab']
    class SlowPeer(SimulationTransport):
        def read(self):
            time.sleep(.12)
            return super().read()
    lab.transport_factory = SlowPeer
    identity = create(app.test_client(), [{'action':'read','timeout':.1}])
    _, d, result = run(app, identity)
    assert result['status'] == 'failed'
    assert 'exceeded its timeout' in result['steps'][1]['detail']
    assert lab.adapters[d['id']].timeout == 2


@pytest.mark.parametrize('steps', [[{'action':'shell','value':'unsafe'}], [{'action':'set','value':101}], [{'action':'assert_range','min':10,'max':0}], [{'action':'wait','seconds':31}], [{'action':'read','timeout':0}], [{'action':'assert_equal','value':True}], []])
def test_invalid_plans_do_not_mutate_state(app, steps):
    before = app.extensions['lab'].snapshot()
    response = app.test_client().post('/api/lab/test-plans', json={'name':'Bad','kind':'valve','steps':steps})
    assert response.status_code == 400
    assert app.extensions['lab'].snapshot() == before
