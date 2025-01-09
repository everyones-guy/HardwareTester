# configuration_views.py
# Path: HardwareTester/views/configuration_views.py

from flask import Blueprint, render_template, request, jsonify
from HardwareTester.services.configuration_service import ConfigurationService
from HardwareTester.extensions import db, logger

configuration_bp = Blueprint("configurations", __name__, url_prefix="/configurations")


@configuration_bp.route("/", methods=["GET"])
def configuration_management():
    """
    Render the Configuration Management page.
    Includes options for saving, loading, and previewing configurations.
    """
    try:
        return render_template("configuration_management.html")
    except Exception as e:
        logger.error(f"Error rendering configuration management page: {e}")
        return jsonify({"success": False, "error": "Failed to load configuration page."}), 500

@configuration_bp.route("/save", methods=["POST"])
def save_configuration():
    """
    Save a new configuration.
    Expects a JSON payload with the configuration details.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided."}), 400

        name = data.get("name")
        layout = data.get("layout")

        if not name or not layout:
            return jsonify({"success": False, "error": "Name and layout are required."}), 400

        result = ConfigurationService.save_configuration(name, layout)
        if result["success"]:
            logger.info(f"Configuration saved: {data}")
            return jsonify({"success": True, "message": result["message"]})
        else:
            logger.error(f"Failed to save configuration: {result['error']}")
            return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Unexpected error while saving configuration: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@configuration_bp.route("/list", methods=["GET"])
def list_configurations():
    """
    Load and return a list of saved configurations with optional search and pagination.
    Query Parameters:
        search: Filter configurations by name.
        page: Page number for pagination.
        per_page: Number of configurations per page.
    """
    try:
        search = request.args.get("search", "").strip()
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))

        result = ConfigurationService.list_configurations(search=search, page=page, per_page=per_page)
        if result["success"]:
            logger.info(f"Configurations listed: {len(result['configurations'])} items retrieved.")
            return jsonify({"success": True, "configurations": result["configurations"]})
        else:
            logger.warning(f"Failed to list configurations: {result['error']}")
            return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Unexpected error while listing configurations: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@configuration_bp.route("/load/<int:config_id>", methods=["GET"])
def load_configuration(config_id):
    """
    Load a specific configuration by ID.
    :param config_id: ID of the configuration to load.
    """
    try:
        result = ConfigurationService.load_configuration(config_id)
        if result["success"]:
            logger.info(f"Configuration loaded: ID {config_id}")
            return jsonify({"success": True, "configuration": result["configuration"]})
        else:
            logger.warning(f"Failed to load configuration ID {config_id}: {result['error']}")
            return jsonify({"success": False, "error": result["error"]}), 404
    except Exception as e:
        logger.error(f"Unexpected error while loading configuration ID {config_id}: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500

@configuration_bp.route("/preview/<int:config_id>", methods=["GET"])
def preview_config(config_id):
    """Generate a preview of a specific configuration."""
    try:
        result = ConfigurationService.generate_preview(config_id)
        if result["success"]:
            logger.info(f"Preview generated for configuration ID {config_id}.")
            return jsonify({"success": True, "preview": result["preview"]})
        else:
            logger.warning(f"Failed to generate preview for configuration ID {config_id}: {result['error']}")
            return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Unexpected error while generating preview for configuration ID {config_id}: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500
