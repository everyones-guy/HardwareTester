from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.api_service import APIService
from HardwareTester.utils.serial_comm import SerialComm
from HardwareTester.extensions import logger
from flask_wtf.csrf import generate_csrf

# Blueprint for API operations
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/", methods=["GET"])
def api_overview():
    """Render the API Overview page."""
    try:
        #csrf_token = generate_csrf()
        #logger.info(f"CSRF Token: {csrf_token}, Type: {type(csrf_token)}")
        #return render_template("api_overview.html", csrf_token=csrf_token)
        return render_template("api_overview.html")
    except Exception as e:
        logger.error(f"Error rendering API Overview page: {e}")
        return jsonify({"success": False, "error": "Failed to load API Overview page."}), 500



@api_bp.route("/test-connection", methods=["GET"])
def test_connection():
    """Test API connection."""
    try:
        result = APIService.test_api_connection()
        if result["success"]:
            return jsonify({"success": True, "message": result["message"]})
        return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@api_bp.route("/fetch-data", methods=["POST"])
def fetch_data():
    """
    Fetch data from an API endpoint.
    Request Body:
        {
            "endpoint": "/example-endpoint",
            "params": {"key": "value"}
        }
    """
    data = request.json
    if not data or "endpoint" not in data:
        return jsonify({"success": False, "error": "Missing required field: 'endpoint'"}), 400

    endpoint = data.get("endpoint")
    params = data.get("params", {})

    try:
        result = APIService.fetch_data_from_api(endpoint, params)
        if result["success"]:
            return jsonify({"success": True, "data": result["data"]})
        return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Error fetching data from endpoint {endpoint}: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@api_bp.route("/push-data", methods=["POST"])
def push_data():
    """
    Push data to an API endpoint.
    Request Body:
        {
            "endpoint": "/example-endpoint",
            "data": {"key": "value"}
        }
    """
    data = request.json
    if not data or "endpoint" not in data:
        return jsonify({"success": False, "error": "Missing required field: 'endpoint'"}), 400

    endpoint = data.get("endpoint")
    payload = data.get("data", {})

    try:
        result = APIService.push_data_to_api(endpoint, payload)
        if result["success"]:
            return jsonify({"success": True, "message": result["message"]})
        return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Error pushing data to endpoint {endpoint}: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@api_bp.route("/endpoints", methods=["GET"])
def get_available_endpoints():
    """List available API endpoints."""
    try:
        result = APIService.list_available_endpoints()
        if result["success"]:
            return jsonify({"success": True, "endpoints": result["endpoints"]})
        return jsonify({"success": False, "error": result["error"]}), 500
    except Exception as e:
        logger.error(f"Error fetching available endpoints: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@api_bp.route("/get-overview", methods=["GET"])
def get_overview():
    """Fetch a summarized overview of devices, endpoints, and state."""
    try:
        overview = {
            "devices": [
                {"id": 1, "name": "Device A", "status": "Online"},
                {"id": 2, "name": "Device B", "status": "Offline"}
            ],
            "endpoints": APIService.list_available_endpoints().get("endpoints", []),
            "api_logs": APIService.api_state.get("logs", [])
        }
        return jsonify({"success": True, "overview": overview})
    except Exception as e:
        logger.error(f"Error fetching overview: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@api_bp.route("/device-config", methods=["GET"])
def get_device_config():
    """Fetch the device configuration over serial."""
    try:
        config_data = SerialComm.read_serial_data(port="/dev/ttyUSB0")
        if "error" in config_data:
            logger.error(f"Error reading serial data: {config_data['error']}")
            return jsonify({"success": False, "error": config_data["error"]}), 500
        return jsonify({"success": True, "config": config_data})
    except Exception as e:
        logger.error(f"Error fetching device configuration: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@api_bp.route("/simulate-device", methods=["POST"])
def simulate_device():
    """
    Simulate a device's behavior based on input.
    Request Body:
        {
            "device_id": 1,
            "action": "open_valve",
            "parameters": {"position": 50}
        }
    """
    data = request.json
    device_id = data.get("device_id")
    action = data.get("action")
    parameters = data.get("parameters", {})

    if not device_id or not action:
        return jsonify({"success": False, "error": "Device ID and action are required"}), 400

    try:
        simulation_result = {
            "device_id": device_id,
            "action": action,
            "parameters": parameters,
            "status": "success",
            "response": f"Action '{action}' performed on device {device_id}"
        }
        return jsonify({"success": True, "result": simulation_result})
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        return jsonify({"success": False, "error": f"Simulation failed: {str(e)}"}), 500
