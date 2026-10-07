"""Validated executable plans and persistent adapter for the original plan service."""
import copy
import math
import uuid
from flask import jsonify, request
from .lab import LabError, now
from .utils.validators import validate_json


def number(value, label, minimum=-1e9, maximum=1e9):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise LabError(f'{label} must be a finite number between {minimum} and {maximum}.')
    return value


def normalize_plan(data):
    ok, message = validate_json(data, ['name', 'kind', 'steps'])
    if not ok:
        raise LabError(message)
    if not isinstance(data['name'], str) or not 1 <= len(data['name'].strip()) <= 100:
        raise LabError('Plan name must contain 1–100 characters.')
    if data['kind'] not in ('temperature', 'valve', 'relay'):
        raise LabError('Choose a temperature, valve, or relay plan profile.')
    description = data.get('description', '')
    if not isinstance(description, str) or len(description) > 2000:
        raise LabError('Description must be text up to 2000 characters.')
    if not isinstance(data['steps'], list) or not 1 <= len(data['steps']) <= 30:
        raise LabError('A plan requires 1–30 steps.')
    steps = []
    for item in data['steps']:
        if not isinstance(item, dict):
            raise LabError('Every step must be a JSON object.')
        action = item.get('action')
        if action not in ('read', 'set', 'assert_range', 'assert_equal', 'wait'):
            raise LabError('Supported actions: read, set, assert_range, assert_equal, wait.')
        label = item.get('name', action.replace('_', ' ').title())
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
            raise LabError('Step name must contain 1–100 characters.')
        step = {'name': label.strip(), 'action': action}
        if action == 'wait':
            step['seconds'] = number(item.get('seconds'), 'Wait duration', 0, 30)
        else:
            step['timeout'] = number(item.get('timeout', 2), 'Response timeout', .1, 10)
        if action in ('set', 'assert_equal'):
            step['value'] = number(item.get('value'), 'Value')
            if action == 'set' and not 0 <= step['value'] <= {'temperature': 50, 'valve': 100, 'relay': 1}[data['kind']]:
                raise LabError('Set value is outside the device profile command limits.')
            if action == 'set' and data['kind'] == 'relay' and step['value'] not in (0, 1):
                raise LabError('Relay set commands must be 0 or 1.')
            if action == 'assert_equal':
                step['tolerance'] = number(item.get('tolerance', 0), 'Tolerance', 0, 1e6)
        if action == 'assert_range':
            step['min'] = number(item.get('min'), 'Minimum')
            step['max'] = number(item.get('max'), 'Maximum')
            if step['min'] > step['max']:
                raise LabError('Range minimum cannot exceed maximum.')
        steps.append(step)
    return {'name': data['name'].strip(), 'kind': data['kind'], 'description': description, 'steps': steps}


class PlanRepository:
    def __init__(self, lab):
        self.lab = lab
        lab.state.setdefault('testPlans', [])

    def editable(self):
        if self.lab.active:
            raise LabError('Stop the active test before editing plans.', 409)

    def find(self, identity):
        plan = next((p for p in self.lab.state['testPlans'] if p['id'] == identity), None)
        if plan is None:
            raise LabError('Test plan not found.', 404)
        return plan

    def list_test_plans(self, search=None, page=1, per_page=10):
        plans = [p for p in self.lab.state['testPlans'] if not search or search.lower() in p['name'].lower()]
        return {'success': True, 'testPlans': copy.deepcopy(plans), 'total': len(plans)}

    def create_test_plan(self, data, created_by=None):
        self.editable()
        if len(self.lab.state['testPlans']) >= 100:
            raise LabError('The library supports 100 test plans.', 409)
        plan = normalize_plan(data)
        plan.update(id=str(uuid.uuid4()), version=1, updatedAt=now())
        self.lab.state['testPlans'].append(plan)
        self.lab.log(f"Created test plan {plan['name']}.")
        self.lab.save()
        return {'success': True, 'planId': plan['id']}

    def preview_test_plan(self, identity):
        return {'success': True, 'plan': copy.deepcopy(self.find(identity))}

    def run_test_plan(self, identity, device_id):
        return {'success': True, 'runId': self.lab.start(device_id, identity)}

    def update(self, identity, data):
        self.editable()
        previous = self.find(identity)
        if data.get('version') != previous['version']:
            raise LabError('This plan changed. Reload it before saving.', 409)
        normalized = normalize_plan(data)
        previous.update(normalized, version=previous['version'] + 1, updatedAt=now())
        self.lab.log(f"Updated test plan {previous['name']}.")
        self.lab.save()

    def delete(self, identity, version):
        self.editable()
        plan = self.find(identity)
        if version != plan['version']:
            raise LabError('This plan changed. Reload it before deleting.', 409)
        self.lab.state['testPlans'].remove(plan)
        self.lab.log(f"Deleted test plan {plan['name']}.")
        self.lab.save()


def register_plans(app, lab):
    from .services.test_plan_service import TestPlanService
    repository = PlanRepository(lab)
    app.extensions['plan_repository'] = repository

    @app.route('/api/lab/test-plans', methods=['GET', 'POST'])
    @app.route('/api/lab/test-plans/<identity>', methods=['GET', 'PUT', 'DELETE'])
    @app.route('/api/lab/test-plans/<identity>/run', methods=['POST'])
    def plans(identity=None):
        with lab.lock:
            data = {} if request.method == 'GET' else request.get_json()
            if not isinstance(data, dict):
                raise LabError('Request body must be a JSON object.')
            extra = {}
            if request.path.endswith('/run'):
                extra = TestPlanService.run_test_plan(identity, device_id=data.get('deviceId'), repository=repository)
            elif request.method == 'GET':
                extra = TestPlanService.preview_test_plan(identity, repository=repository) if identity else TestPlanService.list_test_plans(repository=repository)
            elif request.method == 'POST':
                extra = TestPlanService.create_test_plan(data, None, repository=repository)
            elif request.method == 'PUT':
                repository.update(identity, data)
            else:
                repository.delete(identity, data.get('version'))
            return jsonify(state=lab.snapshot(), **extra)
