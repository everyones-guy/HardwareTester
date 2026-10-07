"""Configuration mapping for original controller/peripheral blueprint formats."""
import copy
import json
import math
from .lab import LabError
from .utils.validators import validate_json


def properties_valid(properties):
    if not isinstance(properties, dict):
        raise LabError('Peripheral properties must be a JSON object.')
    try:
        if len(json.dumps(properties, allow_nan=False)) > 8192:
            raise LabError('Peripheral properties exceed 8 KB.')
    except (ValueError, TypeError, RecursionError) as error:
        raise LabError('Properties must contain finite, JSON-compatible values.') from error
    threshold = properties.get('threshold')
    if threshold is not None:
        values = threshold.values() if isinstance(threshold, dict) else [threshold]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise LabError('Threshold limits must be finite numbers.')
        if isinstance(threshold, dict) and (set(threshold) - {'min', 'max'} or not threshold or threshold.get('min', -math.inf) > threshold.get('max', math.inf)):
            raise LabError('Threshold requires min and/or max, with min no greater than max.')
    return copy.deepcopy(properties)


def clean_configuration(value):
    # Configuration exports are not a credential store.
    if isinstance(value, dict):
        return {k: clean_configuration(v) for k, v in value.items() if k.lower() not in ('auth', 'password', 'username', 'token', 'access_token', 'secret', 'api_key')}
    if isinstance(value, list):
        return [clean_configuration(v) for v in value]
    return value


def kind_for(item):
    if not isinstance(item, dict):
        return None
    value = item.get('kind', item.get('type', ''))
    if not isinstance(value, str):
        return None
    value = value.lower().replace(' ', '_')
    names = {'temperature': 'temperature', 'temperature_sensor': 'temperature', 'valve': 'valve', 'proportional_valve': 'valve', 'relay': 'relay', 'relay_controller': 'relay'}
    if value == 'sensor' and 'temperature' in str(item.get('name', '')).lower():
        return 'temperature'
    return names.get(value)


def peripheral(item):
    ok, message = validate_json(item, ['name', 'type'])
    if not ok:
        raise LabError(message)
    if not isinstance(item['name'], str) or not 1 <= len(item['name'].strip()) <= 100 or not isinstance(item['type'], str) or not 1 <= len(item['type'].strip()) <= 100:
        raise LabError('Peripheral name and type must contain 1–100 characters.')
    properties = item.get('properties', {k: v for k, v in item.items() if k not in ('name', 'type', 'kind', 'id', 'device_id')})
    return {'name': item['name'].strip(), 'type': item['type'].strip(), 'properties': properties_valid(clean_configuration(properties))}


def normalize_configuration(configuration):
    if not isinstance(configuration, dict):
        raise LabError('Blueprint must be a JSON object.')
    ok, message = validate_json(configuration, ['name'])
    if not ok:
        raise LabError(message)
    source = clean_configuration(configuration)
    try:
        if len(json.dumps(source, allow_nan=False)) > 100000:
            raise LabError('Blueprint exceeds 100 KB.')
    except (ValueError, TypeError, RecursionError) as error:
        raise LabError('Blueprint must be finite, valid JSON.') from error
    if not isinstance(source['name'], str) or not 1 <= len(source['name'].strip()) <= 100:
        raise LabError('Blueprint name must contain 1–100 characters.')
    description = source.get('description', '')
    if not isinstance(description, str) or len(description) > 2000:
        raise LabError('Description must be text up to 2000 characters.')
    warnings = []
    devices = []
    if isinstance(source.get('devices'), list):
        entries = source['devices']
        direct = True
    else:
        controller = source.get('controller', source)
        if not isinstance(controller, dict) or not isinstance(controller.get('peripherals'), list):
            raise LabError('Provide devices, root peripherals, or controller.peripherals in the blueprint.')
        entries = controller['peripherals']
        direct = False
    if not entries or len(entries) > 100:
        raise LabError('A blueprint requires 1–100 device/peripheral definitions.')
    for item in entries:
        if not isinstance(item, dict):
            raise LabError('Every definition must be a JSON object.')
        kind = kind_for(item)
        if not kind:
            warnings.append(f"{str(item.get('name', 'Unnamed peripheral'))[:100]}: unsupported type retained in source configuration; no device will be created.")
            continue
        if not isinstance(item.get('name'), str) or not 1 <= len(item['name'].strip()) <= 100:
            raise LabError('Every supported device requires a name up to 100 characters.')
        attached = item.get('peripherals', []) if direct else [item]
        if not isinstance(attached, list) or len(attached) > 50:
            raise LabError('A device may have up to 50 peripheral definitions.')
        devices.append({'name': item['name'].strip(), 'kind': kind, 'peripherals': [peripheral(p) for p in attached]})
        if str(item.get('type', '')).lower() == 'sensor':
            warnings.append(f"{item['name']}: mapped the Sensor type to temperature using its name.")
    if not devices:
        raise LabError('No supported temperature, valve, or relay profiles were found. Source settings are not executable hardware adapters.')
    warnings.append('Devices will be created as disconnected simulations. Original connection/command settings are metadata; no hardware is opened.')
    if json.dumps(source, sort_keys=True) != json.dumps(configuration, sort_keys=True):
        warnings.append('Credential fields were excluded from the saved configuration.')
    return {'name': source['name'].strip(), 'description': description, 'version': str(source.get('version', '1'))[:30], 'configuration': source, 'devices': devices, 'warnings': warnings}
