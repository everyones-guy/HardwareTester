"""Verify the Docker MQTT valve through the application API, then remove the test device."""
import argparse
import json
import os
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:5000')
    parser.add_argument('--endpoint', default='mqtt://broker:1883/lab/demo-valve')
    args = parser.parse_args()
    token = os.environ.get('LAB_API_TOKEN', '')

    def api(path='', method='GET', data=None):
        headers = {'Content-Type': 'application/json'}
        if token: headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(args.url.rstrip('/') + '/api/lab' + path, method=method, headers=headers, data=None if data is None else json.dumps(data).encode())
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)

    state = api()['state']
    if any(r['status'] == 'running' for r in state['runs']):
        raise RuntimeError('The bench is busy. Finish the active test before running this check.')
    if any(d['endpoint'] == args.endpoint and d['connected'] for d in state['devices']):
        raise RuntimeError('The mock valve is already connected on the bench. Disconnect it before this check.')
    device_id = None
    run_id = None
    try:
        device_id = api('/devices', 'POST', {'name':'Docker MQTT smoke check','kind':'valve','adapter':'mqtt','endpoint':args.endpoint})['deviceId']
        connected = api(f'/devices/{device_id}/connection', 'POST', {'connected':True})
        original = next(d['value'] for d in connected['state']['devices'] if d['id'] == device_id)
        run_id = api('/runs', 'POST', {'deviceId':device_id,'plan':'control'})['runId']
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            state = api()['state']
            run = next(r for r in state['runs'] if r['id'] == run_id)
            if run['status'] != 'running': break
            time.sleep(.25)
        else: raise RuntimeError('MQTT test did not finish within 40 seconds.')
        if run['status'] != 'passed':
            raise RuntimeError('MQTT run failed: ' + json.dumps(run['steps']))
        final = next(d['value'] for d in state['devices'] if d['id'] == device_id)
        if final != original:
            raise RuntimeError(f'Mock output was not restored: expected {original}, received {final}.')
        print(f'MQTT smoke check passed: connected, commanded 75%, verified, restored {original}%.', flush=True)
    finally:
        if device_id:
            state = api()['state']
            active = next((r for r in state['runs'] if r['status'] == 'running'), None)
            if active and active['id'] == run_id:
                api('/runs/cancel', 'POST', {})
                active = None
            if not active:
                api(f'/devices/{device_id}', 'DELETE', {})
            else:
                print('Another run started; temporary device was left on the bench for cleanup.', flush=True)


if __name__ == '__main__': main()
