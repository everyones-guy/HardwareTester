# configuration_service.py imports the Configuration model from models/__init__.py.
from HardwareTester.extensions import db, logger
from HardwareTester.models.configuration_models import Configuration
import json

class ConfigurationService:
    @staticmethod
    def save_configuration(name, layout):
        """dddd
        Save a configuration layout to the database.
        :param name: Name of the configuration.
        :param layout: JSON layout of valves and peripherals.
        :return: Dictionary with success message or error.
        """
        try:
            # Validate layout
            if not isinstance(layout, dict):
                return {"success": False, "error": "Invalid layout format. Must be a JSON object."}

            config = Configuration(name=name, layout=json.dumps(layout))
            db.session.add(config)
            db.session.commit()
            logger.info(f"Configuration '{name}' saved successfully.")
            return {"success": True, "message": f"Configuration '{name}' saved successfully."}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving configuration: {e}")
            return {"success": False, "error": str(e)}
    @staticmethod
    def load_configuration(config_id):
        """
        Load a specific configuration by ID.
        :param config_id: ID of the configuration to load.
        :return: Dictionary with configuration data or error.
        """
        try:
            config = Configuration.query.get(config_id)
            if config:
                logger.info(f"Loaded configuration '{config.name}' successfully.")
                return {"success": True, "configuration": {"name": config.name, "layout": json.loads(config.layout)}}
            return {"success": False, "message": "Configuration not found."}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {"success": False, "error": str(e)}
    @staticmethod
    def list_configurations():
        """
        List all saved configurations.
        :return: List of configurations or error.
        """
        try:
            configs = Configuration.query.all()
            logger.info("Fetched all configurations successfully.")
            return {"success": True, "configurations": [{"id": config.id, "name": config.name} for config in configs]}
        except Exception as e:
            logger.error(f"Error listing configurations: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def generate_preview(config_id):
        """
        Generate a preview for a specific configuration.
        :param config_id: ID of the configuration to preview.
        :return: HTML snippet or error message.
        """
        try:
            # Mock preview logic
            configuration = {"id": config_id, "name": f"Config {config_id}"}
            preview_html = f"<div>Preview: {configuration['name']}</div>"
            return {"success": True, "preview": preview_html}
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return {"success": False, "error": str(e)}
