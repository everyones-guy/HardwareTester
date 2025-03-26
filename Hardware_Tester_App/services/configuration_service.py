from Hardware_Tester_App.extensions import db, logger
from Hardware_Tester_App.models.configuration_models import Configuration, DynamicConfiguration
import json


class ConfigurationService:
    @staticmethod
    def save_configuration(name, layout):
        """
        Save a configuration layout to the database.
        """
        try:
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
    def add_dynamic_configuration(data, user_id):
        """
        Add a dynamic configuration to the database.
        """
        try:
            dynamic_config = DynamicConfiguration(
                type=data["type"],
                name=data.get("name"),
                description=data.get("description"),
                properties=data.get("properties", {}),
                created_by=user_id,
                modified_by=user_id,
            )
            db.session.add(dynamic_config)
            db.session.commit()
            logger.info(f"Dynamic configuration '{dynamic_config.name}' added successfully.")
            return {"success": True, "message": f"Dynamic configuration '{dynamic_config.name}' added successfully."}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding dynamic configuration: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_configurations(search=None, page=1, per_page=10):
        """
        List saved configurations with optional search and pagination.
        """
        try:
            query = Configuration.query
            if search:
                query = query.filter(Configuration.name.ilike(f"%{search}%"))
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)

            configurations = [
                {"id": config.id, "name": config.name} for config in paginated.items
            ]
            return {"success": True, "configurations": configurations, "total": paginated.total}
        except Exception as e:
            logger.error(f"Error listing configurations: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def load_configuration(config_id):
        """
        Load a specific configuration by ID.
        """
        try:
            config = Configuration.query.get(config_id)
            if config:
                logger.info(f"Loaded configuration '{config.name}' successfully.")
                return {"success": True, "configuration": {"name": config.name, "layout": json.loads(config.layout)}}
            return {"success": False, "error": "Configuration not found."}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_configuration_by_name(name):
        try:
            configuration = Configuration.query.filter(Configuration.name.ilike(name)).first()

            if configuration:
                return {"success": True, "configuration": configuration.to_dict()}
            return {"success": False, "error": "Configuration not found."}
        except Exception as e:
            logger.error(f"Error fetching configuration by name '{name}': {e}")
            return {"success": False, "error": str(e)}
