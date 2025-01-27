from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from urllib.parse import unquote
from HardwareTester.services.api_service import APIService
from HardwareTester.services.configuration_service import ConfigurationService
from HardwareTester.services.serial_service import SerialService
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("API_Views", per_module=True)

# Blueprint for API operations
api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/", methods=["GET"])
@login_required
def api_overview():
    """Render the API Overview page."""
    try:
        logger.info("Rendering API Overview page.")
        return render_template("api_overview.html")
    except Exception as e:
        logger.error(f"Error rendering API Overview page: {e}")
        return jsonify({"success": False, "error": "Failed to load API Overview page."}), 500


@api_bp.route("/configurations/<string:blueprint>", methods=["GET"])
@login_required
def get_configuration_by_blueprint(blueprint):
    """
    Fetch configuration details by blueprint name.
    :param blueprint: Name of the blueprint (URL encoded or plain string).
    """
    try:
        # Decode the blueprint name if URL-encoded
        decoded_blueprint = unquote(blueprint)
        logger.info(f"Fetching configuration for blueprint: {decoded_blueprint}")

        # Fetch the configuration using the service
        result = ConfigurationService.get_configuration_by_name(decoded_blueprint)
        if result["success"]:
            return jsonify({"success": True, "configuration": result["configuration"]})
        else:
            logger.warning(f"Configuration for blueprint '{decoded_blueprint}' not found.")
            return jsonify({"success": False, "error": result["error"]}), 404
    except Exception as e:
        logger.error(f"Error fetching configuration for blueprint '{blueprint}': {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@api_bp.route("/test-connection", methods=["GET"])
@login_required
def test_connection():
    """Test API connection."""
    try:
        result = APIService.test_api_connection()
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/fetch-data", methods=["POST"])
@login_required
def fetch_data():
    """Fetch data from an API endpoint."""
    data = request.json
    endpoint = data.get("endpoint")
    params = data.get("params", {})

    if not endpoint:
        return jsonify({"success": False, "error": "Missing required field: 'endpoint'"}), 400

    try:
        result = APIService.fetch_data_from_api(endpoint, params)
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Error fetching data from endpoint {endpoint}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/push-data", methods=["POST"])
@login_required
def push_data():
    """Push data to an API endpoint."""
    data = request.json
    endpoint = data.get("endpoint")
    payload = data.get("data", {})

    if not endpoint:
        return jsonify({"success": False, "error": "Missing required field: 'endpoint'"}), 400

    try:
        result = APIService.push_data_to_api(endpoint, payload)
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Error pushing data to endpoint {endpoint}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/endpoints", methods=["GET"])
@login_required
def get_available_endpoints():
    """List available API endpoints."""
    try:
        result = APIService.list_available_endpoints()
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Error fetching available endpoints: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/get-overview", methods=["GET"])
@login_required
def get_overview():
    """Fetch a summarized overview of devices, endpoints, and state."""
    try:
        overview = {
            "devices": APIService.get_devices(),
            "endpoints": APIService.list_available_endpoints().get("endpoints", []),
            "api_logs": APIService.api_state.get("logs", []),
        }
        return jsonify({"success": True, "overview": overview})
    except Exception as e:
        logger.error(f"Error fetching overview: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/device-config", methods=["GET"])
@login_required
def get_device_config():
    """Fetch the device configuration over serial."""
    try:
        config_data = SerialService(port="/dev/ttyUSB0").read_data()
        if "error" in config_data:
            logger.error(f"Error reading serial data: {config_data['error']}")
            return jsonify({"success": False, "error": config_data["error"]}), 500
        return jsonify({"success": True, "config": config_data})
    except Exception as e:
        logger.error(f"Error fetching device configuration: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/simulate-device", methods=["POST"])
@login_required
def simulate_device():
    """Simulate a device's behavior based on input."""
    data = request.json
    device_id = data.get("device_id")
    action = data.get("action")
    parameters = data.get("parameters", {})

    if not device_id or not action:
        return jsonify({"success": False, "error": "Device ID and action are required"}), 400

    try:
        simulation_result = APIService.simulate_device(device_id, action, parameters)
        return jsonify({"success": True, "result": simulation_result})
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/api/test-plans", methods=["POST"])
def create_test_plan():
    test_plan_name = request.form.get("testPlanName")
    test_plan_description = request.form.get("testPlanDescription")
    screen = request.form.get("testPlanScreen")
    event = request.form.get("testPlanEvent")
    timing = request.form.get("testPlanTiming")

    # Validate timing
    if not timing.isdigit() or int(timing) < 0:
        return jsonify({"error": "Invalid timing value. Must be a positive number."}), 400

    # Convert timing to integer
    timing = int(timing)

    # Perform validation and save the test plan
    if not all([test_plan_name, screen, event]):
        return jsonify({"error": "All fields are required"}), 400

    # Save to database or any persistent storage
    new_test_plan = {
        "name": test_plan_name,
        "description": test_plan_description,
        "screen": screen,
        "event": event,
        "timing": timing,
    }

    # Example: Save to database
    # db.session.add(new_test_plan)
    # db.session.commit()

    return jsonify({"message": "Test plan created successfully!"}), 201
