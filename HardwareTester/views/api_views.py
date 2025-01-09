# api_views.py
# Handles the API endpoints for fetching and pushing data.

from flask import Blueprint, jsonify, request
from HardwareTester.services.api_service import APIService
from HardwareTester.utils.serial_comm import SerialComm

# Blueprint for API operations
api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/", methods=["GET"])
def api_overview():
    """API Overview."""
    return jsonify({"message": "API Overview"}), 200


@api_bp.route("/test-connection", methods=["GET"])
def test_connection():
    """Test API connection."""
    result = APIService.test_api_connection()
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    return jsonify({"success": False, "error": result["error"]}), 500

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
    endpoint = data.get("endpoint")
    params = data.get("params", {})

    if not endpoint:
        return jsonify({"success": False, "error": "Endpoint is required"}), 400

    result = APIService.fetch_data_from_api(endpoint, params)
    if result["success"]:
        return jsonify({"success": True, "data": result["data"]})
    return jsonify({"success": False, "error": result["error"]}), 500

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
    endpoint = data.get("endpoint")
    payload = data.get("data", {})

    if not endpoint:
        return jsonify({"success": False, "error": "Endpoint is required"}), 400

    result = APIService.push_data_to_api(endpoint, payload)
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    return jsonify({"success": False, "error": result["error"]}), 500

@api_bp.route("/endpoints", methods=["GET"])
def get_available_endpoints():
    """List available API endpoints."""
    result = APIService.list_available_endpoints()
    if result["success"]:
        return jsonify({"success": True, "endpoints": result["endpoints"]})
    return jsonify({"success": False, "error": result["error"]}), 500

@api_bp.route("/get-overview", methods=["GET"])
def get_overview():
    """Fetch a summarized overview of devices, endpoints, and state."""
    overview = {
        "devices": [],
        "endpoints": [],
        "api_logs": [],
    }

    try:
        # Mocking or fetching devices from a service
        overview["devices"] = [
            {"id": 1, "name": "Device A", "status": "Online"},
            {"id": 2, "name": "Device B", "status": "Offline"},
        ]

        # Fetching available API endpoints
        endpoint_result = APIService.list_available_endpoints()
        if endpoint_result["success"]:
            overview["endpoints"] = endpoint_result["endpoints"]
        
        # Mocking or fetching API logs
        overview["api_logs"] = APIService.api_state.get("logs", [])
        
        return jsonify({"success": True, "overview": overview})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error fetching overview: {str(e)}"}), 500

@api_bp.route("/device-config", methods=["GET"])
def get_device_config():
    """Fetch the device configuration over serial."""
    try:
        config_data = SerialComm.read_serial_data(port="/dev/ttyUSB0")
        if "error" in config_data:
            return jsonify({"success": False, "error": config_data["error"]}), 500
        return jsonify({"success": True, "config": config_data})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error fetching device configuration: {str(e)}"}), 500

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
        # Simulate device interaction (e.g., calling a service or generating mock data)
        simulation_result = {
            "device_id": device_id,
            "action": action,
            "parameters": parameters,
            "status": "success",
            "response": f"Action '{action}' performed on device {device_id}",
        }
        return jsonify({"success": True, "result": simulation_result})
    except Exception as e:
        return jsonify({"success": False, "error": f"Simulation failed: {str(e)}"}), 500
