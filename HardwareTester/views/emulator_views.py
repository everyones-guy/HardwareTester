from flask import Blueprint, jsonify, request, render_template
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.utils.custom_logger import CustomLogger
import json

# Initialize logger
logger = CustomLogger.get_logger("emulator_views")

# Define the Blueprint
emulator_bp = Blueprint("emulators", __name__, url_prefix="/emulators")

@emulator_bp.route("/", methods=["GET"])
def emulator_dashboard():
    """Render the emulator dashboard."""
    try:
        return render_template("emulator.html")
    except Exception as e:
        logger.error(f"Error rendering emulator dashboard: {e}")
        return jsonify({"success": False, "error": "Failed to render the emulator dashboard."}), 500

@emulator_bp.route("/blueprints", methods=["GET"])
def get_blueprints():
    """Fetch available blueprints."""
    try:
        response = EmulatorService.fetch_blueprints()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching blueprints: {e}")
        return jsonify({"success": False, "error": "Failed to fetch blueprints."}), 500

@emulator_bp.route("/load-blueprint", methods=["POST"])
def load_blueprint_endpoint():
    """Load a new blueprint."""
    blueprint_file = request.files.get("blueprint_file")
    if not blueprint_file:
        logger.warning("No blueprint file provided.")
        return jsonify({"success": False, "error": "No blueprint file provided."}), 400
    try:
        response = EmulatorService.load_blueprint(blueprint_file)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error loading blueprint: {e}")
        return jsonify({"success": False, "error": "Failed to load blueprint."}), 500

@emulator_bp.route("/start", methods=["POST"])
def start_emulation_endpoint():
    """Start a machine emulation."""
    data = request.json
    machine_name = data.get("machine_name")
    blueprint = data.get("blueprint")
    stress_test = data.get("stress_test", False)

    if not machine_name or not blueprint:
        logger.warning("Machine name or blueprint is missing.")
        return jsonify({"success": False, "error": "Machine name and blueprint are required."}), 400

    try:
        response = EmulatorService.start_emulation(machine_name, blueprint, stress_test)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error starting emulation for {machine_name}: {e}")
        return jsonify({"success": False, "error": "Failed to start emulation."}), 500

@emulator_bp.route("/stop", methods=["POST"])
def stop_emulation_endpoint():
    """Stop a machine emulation."""
    data = request.json
    machine_name = data.get("machine_name")

    if not machine_name:
        logger.warning("Machine name is missing.")
        return jsonify({"success": False, "error": "Machine name is required."}), 400

    try:
        response = EmulatorService.stop_emulation(machine_name)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error stopping emulation for {machine_name}: {e}")
        return jsonify({"success": False, "error": "Failed to stop emulation."}), 500

@emulator_bp.route("/list", methods=["GET"])
def list_emulations():
    """List all active emulations."""
    try:
        response = EmulatorService.list_active_emulations()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error listing active emulations: {e}")
        return jsonify({"success": False, "error": "Failed to fetch active emulations."}), 500

@emulator_bp.route("/logs", methods=["GET"])
def get_logs():
    """Fetch emulator logs."""
    try:
        response = EmulatorService.get_emulator_logs()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching emulator logs: {e}")
        return jsonify({"success": False, "error": "Failed to fetch emulator logs."}), 500

@emulator_bp.route("/compare", methods=["POST"])
def compare_machines():
    """Compare the operation of machines running different firmware."""
    data = request.json
    machine_ids = data.get("machine_ids", [])

    if not machine_ids or len(machine_ids) < 2:
        logger.warning("Invalid comparison request: Less than two machines provided.")
        return jsonify({"success": False, "error": "At least two machines are required for comparison."}), 400

    try:
        comparisons = [
            {"machine_id": machine_id, "status": EmulatorService.get_machine_status(machine_id)}
            for machine_id in machine_ids
        ]
        differences = EmulatorService.compare_operations(comparisons)
        return jsonify({"success": True, "differences": differences})
    except Exception as e:
        logger.error(f"Error comparing machines: {e}")
        return jsonify({"success": False, "error": "Failed to compare machines."}), 500

# blueprint is the same as a configuration so adding a blueprint is the same adding an emulator...
@emulator_bp.route('/add', methods=['POST'])
def add_emulator():
    """
    Add a new emulator by creating a blueprint.
    """
    try:
        data = request.json
        if not data:
            logger.warning("No data provided for adding emulator.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        # Validate required fields
        required_fields = ["name", "description", "configuration", "author"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}.")
                return jsonify({"success": False, "message": f"Missing field: {field}"}), 400

        # Add the optional version field if provided
        version = data.get("version", "1.0")  # Default to "1.0" if version not specified

        # Call the service to add a blueprint
        response = EmulatorService.add_blueprint(
            name=data["name"],
            description=data["description"],
            configuration=data["configuration"],  # Assuming configuration is passed as a dict
            version=version,
            author=data["author"]
        )

        # Check response and return appropriate message
        if response["success"]:
            return jsonify({"success": True, "message": response["message"]}), 201
        else:
            logger.error(f"Failed to add emulator: {response['message']}")
            return jsonify({"success": False, "message": response["message"]}), 400

    except Exception as e:
        logger.error(f"Error adding emulator: {e}")
        return jsonify({"success": False, "message": "Failed to add emulator."}), 500



