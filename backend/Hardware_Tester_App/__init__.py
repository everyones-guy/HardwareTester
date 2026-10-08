"""Workbench factory. Legacy modules are imported only when explicitly requested."""
import atexit
import hmac
import os
import hashlib
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, g
from werkzeug.exceptions import HTTPException
from .lab import Lab, LabError


def create_app(config_name='development', overrides=None, **kwargs):
    root = Path(__file__).resolve().parents[2]
    app = Flask(__name__, static_folder=None, instance_path=str(root / 'backend' / 'instance'))
    app.config.update(
        TESTING=config_name == 'testing',
        LAB_DB_PATH=os.environ.get('LAB_DB_PATH', str(Path(app.instance_path) / 'workbench.sqlite3')),
        LAB_ALLOW_HARDWARE=os.environ.get('LAB_ALLOW_HARDWARE', 'false').lower() == 'true',
        LAB_WORKER=True,
        LAB_AUTH_ENABLED=os.environ.get('LAB_AUTH_ENABLED', 'false' if config_name == 'testing' else 'true').lower() == 'true',
        LAB_COOKIE_SECURE=os.environ.get('LAB_COOKIE_SECURE', 'false').lower() == 'true',
        LAB_BUILD_ID=os.environ.get('LAB_BUILD_ID', ''),
        LAB_API_TOKEN=os.environ.get('LAB_API_TOKEN', ''),
        LAB_ALLOWED_ORIGINS=os.environ.get('LAB_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080').split(','),
        FRONTEND_BUILD=str(root / 'frontend' / 'build'),
        MAX_CONTENT_LENGTH=131072,
    )
    if overrides:
        app.config.update(overrides)
    lab = Lab(app.config['LAB_DB_PATH'], allow_hardware=app.config['LAB_ALLOW_HARDWARE'], autostart=app.config['LAB_WORKER'], step_seconds=app.config.get('LAB_STEP_SECONDS', .75))
    app.extensions['lab'] = lab
    from .catalog import register_catalog
    register_catalog(app, lab)
    from .test_plans import register_plans
    register_plans(app, lab)
    from .auth import register_auth, required_role
    with lab.lock:
        register_auth(app, lab)
    source_hash=hashlib.sha256()
    for source in sorted(Path(__file__).parent.rglob('*.py')):
        source_hash.update(str(source.relative_to(Path(__file__).parent)).replace('\\','/').encode())
        source_hash.update(source.read_bytes())
    build_id=app.config['LAB_BUILD_ID'] or source_hash.hexdigest()[:12]
    instance=app.extensions['accounts'].instance
    if not app.testing:
        atexit.register(lab.close)

    @app.before_request
    def guard_api():
        if not request.path.startswith(('/api/lab','/api/auth')):
            return
        if request.method != 'GET':
            origin = request.headers.get('Origin')
            if origin and origin.rstrip('/') != request.host_url.rstrip('/') and origin not in app.config['LAB_ALLOWED_ORIGINS']:
                raise LabError('This origin is not allowed to control the lab.', 403)
            if not request.is_json:
                raise LabError('Use application/json for lab commands.', 415)
        token = app.config['LAB_API_TOKEN']
        if request.path.startswith('/api/lab') and token and not hmac.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + token):
            raise LabError('A valid lab API token is required.', 401)
        if request.path.startswith('/api/lab') and app.config['LAB_AUTH_ENABLED']:
            with lab.lock:
                g.workbench_user=app.extensions['accounts'].require(required_role(request.path,request.method),csrf=request.method!='GET')

    @app.after_request
    def headers(response):
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.errorhandler(LabError)
    def lab_error(error):
        return jsonify(error=str(error)), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description), error.code
        return error

    @app.get('/api/health')
    def health():
        # Do not disclose paths or device configuration in an unauthenticated probe.
        return jsonify(status='ok', service='hardware-tester', version=2)

    @app.get('/api/version')
    def version():
        return jsonify(version='0.4.0',build=build_id,instance=instance,deployment=os.environ.get('LAB_DEPLOYMENT','local'),apiOrigin=request.host_url.rstrip('/'),authEnabled=app.config['LAB_AUTH_ENABLED'])

    @app.get('/api/lab')
    def state():
        return jsonify(state=lab.snapshot(), capabilities={'hardware': lab.allow_hardware, 'adapters': ['simulation', 'serial', 'mqtt'], 'persistence': 'sqlite'})

    def body():
        data = request.get_json()
        if not isinstance(data, dict):
            raise LabError('Request body must be a JSON object.')
        return data

    def result(**extra):
        return jsonify(state=lab.snapshot(), **extra)

    @app.post('/api/lab/devices')
    def add():
        device_id = lab.add(body())
        return result(deviceId=device_id), 201

    @app.delete('/api/lab/devices/<device_id>')
    def remove(device_id):
        body()
        lab.remove(device_id)
        return result()

    @app.post('/api/lab/devices/<device_id>/connection')
    def connection(device_id):
        lab.connect(device_id, body().get('connected'))
        return result()

    @app.post('/api/lab/devices/<device_id>/diagnostics')
    def diagnostics(device_id):
        body()
        lab.diagnose(device_id)
        return result()

    @app.post('/api/lab/connect-bench')
    def connect_bench():
        body()
        lab.connect_bench()
        return result()

    @app.post('/api/lab/devices/<device_id>/fault')
    def fault(device_id):
        lab.fault(device_id, body().get('fault'))
        return result()

    @app.post('/api/lab/devices/<device_id>/command')
    def command(device_id):
        lab.command(device_id, body().get('value'))
        return result()

    @app.post('/api/lab/runs')
    def start():
        payload = body()
        if payload.get('plan') in ('smoke', 'control'):
            run_id = lab.start(payload.get('deviceId'), payload.get('plan'), actor=getattr(g,'workbench_user',None))
        else:
            from .services.test_plan_service import TestPlanService
            run_id = TestPlanService.run_test_plan(payload.get('plan'), device_id=payload.get('deviceId'), repository=app.extensions['plan_repository'])['runId']
        return result(runId=run_id), 202

    @app.post('/api/lab/runs/cancel')
    def cancel():
        body()
        lab.cancel()
        return result()

    @app.post('/api/lab/reset')
    def reset():
        body()
        lab.reset()
        return result()

    @app.get('/api/lab/export')
    def export():
        return jsonify(version=1, mode='server', workspace=lab.snapshot())

    @app.get('/', defaults={'path': ''})
    @app.get('/<path:path>')
    def frontend(path):
        if path.startswith('api/') or path == 'api':
            return jsonify(error='API route not found.'), 404
        build = Path(app.config['FRONTEND_BUILD'])
        target = (build / path).resolve()
        if path and target.is_relative_to(build.resolve()) and target.is_file():
            return send_from_directory(build, path)
        if path.startswith('assets/') or path.endswith(('.js', '.css', '.png', '.ico', '.json')):
            return jsonify(error='Asset not found.'), 404
        if not (build / 'index.html').exists():
            return jsonify(error='Frontend build missing. Run npm run build in frontend, or use Vite on port 5173.'), 503
        return send_from_directory(build, 'index.html')

    return app


def create_legacy_app(*args, **kwargs):
    """Opt-in access to the previous application; never imported at lab startup."""
    from .legacy_app import create_app as legacy_factory
    return legacy_factory(*args, **kwargs)
