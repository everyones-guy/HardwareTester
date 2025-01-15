
from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.emulator_service import EmulatorService

emulator_bp = Blueprint("emulator", __name__, url_prefix="/emulators")

@emulator_bp.route("/", methods=["GET"])
def emulator_dashboard():
    """Render the emulator dashboard."""
    return render_template("emulator.html")

@emulator_bp.route("/blueprints", methods=["GET"])
def get_blueprints():
    """Fetch available blueprints."""
    response = EmulatorService.fetch_blueprints()
    return jsonify(response)

@emulator_bp.route("/load-blueprint", methods=["POST"])
def load_blueprint_endpoint():
    """Load a new blueprint."""
    blueprint_file = request.files.get("blueprint_file")
    if not blueprint_file:
        return jsonify({"success": False, "error": "No blueprint file provided"}), 400
    response = EmulatorService.load_blueprint(blueprint_file)
    return jsonify(response)

@emulator_bp.route("/start", methods=["POST"])
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

@emulator_bp.route("/stop", methods=["POST"])
def stop_emulation_endpoint():
    """Stop a machine emulation."""
    data = request.json
    machine_name = data.get("machine_name")

    if not machine_name:
        return jsonify({"success": False, "error": "Machine name is required"}), 400

    response = EmulatorService.stop_emulation(machine_name)
    return jsonify(response)

@emulator_bp.route("/list", methods=["GET"])
def list_emulations():
    """List all active emulations."""
    response = EmulatorService.list_active_emulations()
    return jsonify(response)

@emulator_bp.route("/logs", methods=["GET"])
def get_logs():
    """Fetch emulator logs."""
    response = EmulatorService.get_emulator_logs()
    return jsonify(response)

@emulator_bp.route("/compare", methods=["POST"])
def compare_machines():
    """Compare the operation of machines running different firmware."""
    data = request.json
    machine_ids = data.get("machine_ids", [])

    if not machine_ids or len(machine_ids) < 2:
        return jsonify({"success": False, "error": "At least two machines are required for comparison"}), 400

    comparisons = []
    for machine_id in machine_ids:
        status = EmulatorService.get_machine_status(machine_id)  # Fetch status
        comparisons.append({"machine_id": machine_id, "status": status})

    # Process and highlight differences
    differences = EmulatorService.compare_operations(comparisons)
    return jsonify({"success": True, "differences": differences})
