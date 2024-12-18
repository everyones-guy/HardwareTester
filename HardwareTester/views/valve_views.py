from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.valve_service import list_valves, add_valve, delete_valve

valve_bp = Blueprint("valve", __name__)

@valve_bp.route("/", methods=["GET"])
def get_valves():
    """Get all valves."""
    result = list_valves()
    if result["success"]:
        return jsonify({"success": True, "valves": result["valves"]})
    return jsonify({"success": False, "error": result["error"]}), 500

@valve_bp.route("/", methods=["POST"])
def create_valve():
    """Add a new valve."""
    data = request.form  # Changed to handle form data from 'add_valve.html'
    name = data.get("name")
    valve_type = data.get("type")
    api_endpoint = data.get("api_endpoint")
    result = add_valve(name, valve_type, api_endpoint)
    if result["success"]:
        return jsonify({"success": True, "valve": result["valve"]})
    return jsonify({"success": False, "error": result["error"]}), 400

@valve_bp.route("/<int:valve_id>", methods=["DELETE"])
def remove_valve(valve_id):
    """Delete a valve."""
    result = delete_valve(valve_id)
    if result["success"]:
        return jsonify({"success": True, "message": f"Valve ID {valve_id} deleted successfully."})
    return jsonify({"success": False, "error": result["error"]}), 400

@valve_bp.route("/management", methods=["GET"], endpoint="valve_management")
def valve_management():
    """Render the Valve Management page."""
    return render_template("valve_management.html")

@valve_bp.route("/add", methods=["GET"], endpoint="add_valve")
def add_valve_page():
    """Render the Add Valve page."""
    return render_template("add_valve.html")
