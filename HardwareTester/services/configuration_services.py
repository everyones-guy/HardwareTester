from HardwareTester.extensions import db
from HardwareTester.models import Configuration
import json

def save_configuration(name, layout):
    """
    Save a configuration layout to the database.
    :param name: Name of the configuration.
    :param layout: JSON layout of valves and peripherals.
    :return: Dictionary with success message or error.
    """
    try:
        config = Configuration(name=name, layout=layout)
        db.session.add(config)
        db.session.commit()
        return {"success": True, "message": f"Configuration '{name}' saved successfully."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}

def load_configuration(config_id):
    """
    Load a specific configuration by ID.
    :param config_id: ID of the configuration to load.
    :return: Dictionary with configuration data or error.
    """
    try:
        config = Configuration.query.get(config_id)
        if config:
            return {"success": True, "configuration": {"name": config.name, "layout": json.loads(config.layout)}}
        return {"success": False, "message": "Configuration not found."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def list_configurations():
    """
    List all saved configurations.
    :return: List of configurations or error.
    """
    try:
        configs = Configuration.query.all()
        return {"success": True, "configurations": [{"id": config.id, "name": config.name} for config in configs]}
    except Exception as e:
        return {"success": False, "error": str(e)}
