
from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.emulator_service import EmulatorService

emulator_bp = Blueprint("emulator", __name__, url_prefix="/emulator")

@emulator_bp.route("/emulator", methods=["GET"])
def emulator_dashboard():
    """Render the emulator dashboard."""
    return render_template("emulator.html")

@emulator_bp.route("/emulator/blueprints", methods=["GET"])
def get_blueprints():
    """Fetch available blueprints."""
    response = EmulatorService.fetch_blueprints()
    return jsonify(response)

@emulator_bp.route("/emulator/load-blueprint", methods=["POST"])
def load_blueprint_endpoint():
    """Load a new blueprint."""
    blueprint_file = request.files.get("blueprint_file")
    if not blueprint_file:
        return jsonify({"success": False, "error": "No blueprint file provided"}), 400
    response = EmulatorService.load_blueprint(blueprint_file)
    return jsonify(response)

@emulator_bp.route("/emulator/start", methods=["POST"])
def start_emulation_endpoint():
    """Start a machine emulation."""
    data = request.json
    machine_name = data.get("machine_name")
    blueprint = data.get("blueprint")
    stress_test = data.get("stress_test", False)

    if not machine_name or not blueprint:
        return jsonify({"success": False, "error": "Machine name and blueprint are required"}), 400

    response = EmulatorService.start_emulation(machine_name, blueprint, stress_test)
    return jsonify(response)

@emulator_bp.route("/emulator/stop", methods=["POST"])
def stop_emulation_endpoint():
    """Stop a machine emulation."""
    data = request.json
    machine_name = data.get("machine_name")

    if not machine_name:
        return jsonify({"success": False, "error": "Machine name is required"}), 400

    response = EmulatorService.stop_emulation(machine_name)
    return jsonify(response)

@emulator_bp.route("/emulator/list", methods=["GET"])
def list_emulations():
    """List all active emulations."""
    response = EmulatorService.list_active_emulations()
    return jsonify(response)

@emulator_bp.route("/emulator/logs", methods=["GET"])
def get_logs():
    """Fetch emulator logs."""
    response = EmulatorService.get_emulator_logs()
    return jsonify(response)

