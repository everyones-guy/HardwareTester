from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.api_service import APIService
from HardwareTester.services.serial_service import SerialService
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.extensions import csrf

# Initialize logger
logger = CustomLogger.get_logger("api_views")

# Blueprint for API operations
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/", methods=["GET"])
def api_overview():
    """Render the API Overview page."""
    try:
        csrf_token = csrf.generate_csrf()
        logger.info("CSRF Token generated successfully.")
        return render_template("api_overview.html", csrf_token=csrf_token)
    except Exception as e:
        logger.error(f"Error rendering API Overview page: {e}")
        return jsonify({"success": False, "error": "Failed to load API Overview page."}), 500


@api_bp.route("/test-connection", methods=["GET"])
def test_connection():
    """Test API connection."""
    try:
        result = APIService.test_api_connection()
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/fetch-data", methods=["POST"])
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
def get_available_endpoints():
    """List available API endpoints."""
    try:
        result = APIService.list_available_endpoints()
        return jsonify(result) if result["success"] else jsonify(result), 500
    except Exception as e:
        logger.error(f"Error fetching available endpoints: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/get-overview", methods=["GET"])
def get_overview():
    """Fetch a summarized overview of devices, endpoints, and state."""
    try:
        overview = {
            "devices": APIService.get_devices(),
            "endpoints": APIService.list_available_endpoints().get("endpoints", []),
            "api_logs": APIService.api_state.get("logs", [])
        }
        return jsonify({"success": True, "overview": overview})
    except Exception as e:
        logger.error(f"Error fetching overview: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/device-config", methods=["GET"])
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

@api_bp.route('/add-blueprint', methods=['POST'])
def add_blueprint():
    data = request.json
    if not data or 'name' not in data or 'description' not in data:
        return jsonify({"success": False, "message": "Missing required fields: 'name' and 'description'"}), 400

    result = EmulatorService.add_blueprint(
        name=data['name'],
        description=data['description'],
        configuration=data.get('configuration'),
        version=data.get('version'),
        author=data.get('author')
    )
    return jsonify(result), 200 if result["success"] else 400
