import pytest
from Hardware_Tester_App import create_app

PASSWORD='Test-account-passphrase-123'


@pytest.fixture
def app(tmp_path):
    app=create_app('testing',{'LAB_DB_PATH':str(tmp_path/'auth.sqlite3'),'LAB_WORKER':False,'LAB_AUTH_ENABLED':True})
    yield app
    app.extensions['lab'].close()


def setup(client):
    response=client.post('/api/auth/setup',json={'username':'admin','email':'admin@example.com','password':PASSWORD})
    assert response.status_code==200
    return response.json


def user(app,admin,csrf,role):
    result=admin.post('/api/auth/users',json={'username':role,'email':role+'@example.com','password':PASSWORD,'role':role},headers={'X-CSRF-Token':csrf})
    assert result.status_code==200
    client=app.test_client()
    login=client.post('/api/auth/login',json={'username':role,'password':PASSWORD})
    assert login.status_code==200
    return client,login.json['csrf']


def test_bootstrap_cookie_sessions_and_csrf(app):
    client=app.test_client()
    assert client.get('/api/lab').status_code==401
    assert client.get('/api/auth/session').json['setupRequired']
    signed=setup(client)
    assert client.post('/api/auth/setup',json={}).status_code==409
    assert client.get('/api/lab').status_code==200
    response=client.post('/api/lab/connect-bench',json={})
    assert response.status_code==403
    assert client.post('/api/lab/connect-bench',json={},headers={'X-CSRF-Token':signed['csrf'],'Origin':'http://untrusted.example'}).status_code==403
    assert client.post('/api/lab/connect-bench',json={},headers={'X-CSRF-Token':signed['csrf']}).status_code==200
    assert client.get_cookie(app.extensions['accounts'].cookie_name,path='/api').http_only
    assert client.post('/api/auth/logout',json={},headers={'X-CSRF-Token':signed['csrf']}).status_code==200
    assert client.get('/api/lab').status_code==401


@pytest.mark.parametrize('role', ['viewer','operator'])
def test_role_enforcement_is_on_server(app,role):
    admin=app.test_client();signed=setup(admin)
    client,csrf=user(app,admin,signed['csrf'],role)
    assert client.get('/api/lab/export').status_code==200
    assert client.get('/api/auth/users').status_code==403
    headers={'X-CSRF-Token':csrf}
    for path,data in [('/api/lab/reset',{}),('/api/lab/devices',{'name':'R','kind':'relay'}),('/api/lab/test-plans',{'name':'P','kind':'relay','steps':[{'action':'read'}]}),('/api/lab/peripherals',{}),('/api/lab/blueprints/capture',{'name':'B'})]:
        assert client.post(path,json=data,headers=headers).status_code==403
    connection=client.post('/api/lab/connect-bench',json={},headers=headers)
    assert connection.status_code==(200 if role=='operator' else 403)
    device=admin.get('/api/lab').json['state']['devices'][0]
    diagnostic=client.post(f"/api/lab/devices/{device['id']}/diagnostics",json={},headers=headers)
    assert diagnostic.status_code==(200 if role=='operator' else 403)
    run=client.post('/api/lab/runs',json={'deviceId':device['id'],'plan':'smoke'},headers=headers)
    assert run.status_code==(202 if role=='operator' else 403)
    if role=='operator':
        assert run.json['state']['runs'][0]['startedBy']['username']=='operator'


def test_role_changes_and_disabling_take_effect_for_existing_session(app):
    admin=app.test_client();signed=setup(admin)
    client,csrf=user(app,admin,signed['csrf'],'operator')
    headers={'X-CSRF-Token':signed['csrf']}
    account=next(u for u in admin.get('/api/auth/users').json['users'] if u['username']=='operator')
    assert admin.patch('/api/auth/users/'+account['id'],json={'version':1,'role':'viewer'},headers=headers).status_code==200
    assert client.post('/api/lab/connect-bench',json={},headers={'X-CSRF-Token':csrf}).status_code==403
    assert admin.patch('/api/auth/users/'+account['id'],json={'version':1,'enabled':False},headers=headers).status_code==409
    assert admin.patch('/api/auth/users/'+account['id'],json={'version':2,'enabled':False},headers=headers).status_code==200
    assert client.get('/api/lab').status_code==401


def test_last_admin_password_revocation_and_storage(app):
    client=app.test_client();signed=setup(client);headers={'X-CSRF-Token':signed['csrf']}
    account=signed['user']
    assert client.patch('/api/auth/users/'+account['id'],json={'version':1,'role':'viewer'},headers=headers).status_code==409
    assert client.patch('/api/auth/users/'+account['id'],json={'version':1,'enabled':False},headers=headers).status_code==409
    db=app.extensions['lab'].connection
    assert db.execute('SELECT password FROM lab_users').fetchone()[0]!=PASSWORD
    cookie=client.get_cookie(app.extensions['accounts'].cookie_name,path='/api').value
    assert db.execute('SELECT token FROM lab_sessions').fetchone()[0]!=cookie
    assert 'lab_users' not in client.get('/api/lab/export').get_data(as_text=True)
    assert client.patch('/api/auth/users/'+account['id'],json={'version':1,'password':'New-long-passphrase-123'},headers=headers).status_code==200
    assert client.get('/api/lab').status_code==401


def test_login_throttling_and_generic_error(app):
    client=app.test_client();setup(client)
    for _ in range(5):
        response=client.post('/api/auth/login',json={'username':'unknown','password':'wrong'})
        assert response.status_code==401 and response.json['error']=='Invalid username or password.'
    assert client.post('/api/auth/login',json={'username':'unknown','password':'wrong'}).status_code==429


def test_accounts_sessions_and_instance_survive_restart(app):
    client=app.test_client();signed=setup(client)
    cookie=client.get_cookie(app.extensions['accounts'].cookie_name,path='/api').value
    instance=client.get('/api/version').json['instance']
    path=app.config['LAB_DB_PATH'];app.extensions['lab'].close()
    restarted=create_app('testing',{'LAB_DB_PATH':path,'LAB_WORKER':False,'LAB_AUTH_ENABLED':True})
    try:
        new_client=restarted.test_client();new_client.set_cookie(restarted.extensions['accounts'].cookie_name,cookie,path='/api')
        assert new_client.get('/api/auth/session').json['user']['id']==signed['user']['id']
        assert new_client.get('/api/version').json['instance']==instance
        assert new_client.post('/api/lab/reset',json={},headers={'X-CSRF-Token':signed['csrf']}).status_code==200
        assert not new_client.get('/api/auth/session').json['setupRequired']
    finally:restarted.extensions['lab'].close()


def test_two_workspaces_keep_independent_cookies_on_same_host(app,tmp_path):
    other=create_app('testing',{'LAB_DB_PATH':str(tmp_path/'other.sqlite3'),'LAB_WORKER':False,'LAB_AUTH_ENABLED':True})
    try:
        first,second=app.test_client(),other.test_client()
        setup(first);setup(second)
        first_name,second_name=app.extensions['accounts'].cookie_name,other.extensions['accounts'].cookie_name
        assert first_name!=second_name
        first_token=first.get_cookie(first_name,path='/api').value
        second_token=second.get_cookie(second_name,path='/api').value
        first.set_cookie(second_name,second_token,path='/api')
        second.set_cookie(first_name,first_token,path='/api')
        assert first.get('/api/lab').status_code==200
        assert second.get('/api/lab').status_code==200
    finally:other.extensions['lab'].close()


def test_expiry_and_api_token_do_not_bypass_login(app):
    client=app.test_client();signed=setup(client)
    app.config['LAB_API_TOKEN']='test-api-token'
    anonymous=app.test_client()
    assert anonymous.get('/api/lab',headers={'Authorization':'Bearer test-api-token'}).status_code==401
    app.extensions['lab'].connection.execute('UPDATE lab_sessions SET expires=0')
    app.extensions['lab'].connection.commit()
    assert client.get('/api/auth/session').json['user'] is None
    assert client.get('/api/lab',headers={'Authorization':'Bearer test-api-token'}).status_code==401
