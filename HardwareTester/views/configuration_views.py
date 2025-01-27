from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from HardwareTester.services.configuration_service import ConfigurationService
from HardwareTester.extensions import logger

configuration_bp = Blueprint("configurations", __name__, url_prefix="/configurations")


@configuration_bp.route("/", methods=["GET"])
@login_required
def configuration_management():
    """
    Render the Configuration Management page.
    """
    try:
        return render_template("configuration_management.html")
    except Exception as e:
        logger.error(f"Error rendering configuration management page: {e}")
        return jsonify({"success": False, "error": "Failed to load configuration page."}), 500


@configuration_bp.route("/save", methods=["POST"])
@login_required
def save_configuration():
    """
    Save a new configuration.
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
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Unexpected error while saving configuration: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@configuration_bp.route("/add-configuration", methods=["POST"])
@login_required
def add_configuration():
    """
    Add a dynamic configuration.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided."}), 400

        result = ConfigurationService.add_dynamic_configuration(data, current_user.id)
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Unexpected error while adding configuration: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@configuration_bp.route("/list", methods=["GET"])
@login_required
def list_configurations():
    """
    List saved configurations.
    """
    try:
        search = request.args.get("search", "").strip()
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))

        result = ConfigurationService.list_configurations(search=search, page=page, per_page=per_page)
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Unexpected error while listing configurations: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@configuration_bp.route("/load/<int:config_id>", methods=["GET"])
@login_required
def load_configuration(config_id):
    """
    Load a specific configuration by ID.
    """
    try:
        result = ConfigurationService.load_configuration(config_id)
        return jsonify(result) if result["success"] else jsonify(result), 404
    except Exception as e:
        logger.error(f"Unexpected error while loading configuration ID {config_id}: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500
