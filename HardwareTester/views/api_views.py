from flask import Blueprint, jsonify, request
from HardwareTester.services.api_service import (
    test_api_connection,
    fetch_data_from_api,
    push_data_to_api,
    list_available_endpoints,
)

api_bp = Blueprint("api", __name__)

@api_bp.route("/test-connection", methods=["GET"])
def test_connection():
    """Test API connection."""
    result = test_api_connection()
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

    result = fetch_data_from_api(endpoint, params)
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

    result = push_data_to_api(endpoint, payload)
    if result["success"]:
        return jsonify({"success": True, "message": result["message"]})
    return jsonify({"success": False, "error": result["error"]}), 500

@api_bp.route("/endpoints", methods=["GET"])
def get_available_endpoints():
    """List available API endpoints."""
    result = list_available_endpoints()
    if result["success"]:
        return jsonify({"success": True, "endpoints": result["endpoints"]})
    return jsonify({"success": False, "error": result["error"]}), 500
