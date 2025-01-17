from flask import Blueprint as FlaskBlueprint, jsonify, request, render_template
from HardwareTester.extensions import db
from HardwareTester.models import Blueprint, Emulation
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("emulator_views")

# Define the Flask Blueprint - for the front end
emulator_bp = FlaskBlueprint("emulators", __name__, url_prefix="/emulators")

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
    try:
        data = request.json
        if not data or "name" not in data:
            logger.warning("Invalid blueprint load request.")
            return jsonify({"success": False, "message": "Invalid data. 'name' is required."}), 400

        response = EmulatorService.load_blueprint(data["name"])
        return jsonify(response), 200 if response["success"] else 400
    except Exception as e:
        logger.error(f"Error loading blueprint: {e}")
        return jsonify({"success": False, "error": "Failed to load blueprint."}), 500

@emulator_bp.route("/start", methods=["POST"])
def start_emulation_endpoint():
    """Start a machine emulation."""
    try:
        data = request.json
        machine_name = data.get("machine_name")
        blueprint = data.get("blueprint")
        stress_test = data.get("stress_test", False)

        if not machine_name or not blueprint:
            logger.warning("Machine name or blueprint is missing.")
            return jsonify({"success": False, "message": "Machine name and blueprint are required."}), 400

        response = EmulatorService.start_emulation(machine_name, blueprint, stress_test)
        return jsonify(response), 200 if response["success"] else 400
    except Exception as e:
        logger.error(f"Error starting emulation for {machine_name}: {e}")
        return jsonify({"success": False, "message": "Failed to start emulation."}), 500

@emulator_bp.route("/stop", methods=["POST"])
def stop_emulation_endpoint():
    """Stop a machine emulation."""
    try:
        data = request.json
        machine_name = data.get("machine_name")

        if not machine_name:
            logger.warning("Machine name is missing.")
            return jsonify({"success": False, "message": "Machine name is required."}), 400

        response = EmulatorService.stop_emulation(machine_name)
        return jsonify(response), 200 if response["success"] else 400
    except Exception as e:
        logger.error(f"Error stopping emulation for {machine_name}: {e}")
        return jsonify({"success": False, "message": "Failed to stop emulation."}), 500

@emulator_bp.route("/list", methods=["GET"])
def list_emulations():
    """List all active emulations with additional details."""
    try:
        # Fetch active emulations
        emulations = Emulation.query.all()
        detailed_emulations = []

        for emulation in emulations:
            # Fetch associated blueprint details
            blueprint = Blueprint.query.filter_by(name=emulation.blueprint).first()
            detailed_emulations.append({
                "machine_id": emulation.id,
                "machine_name": emulation.machine_name,
                "status": emulation.status,
                "blueprint": emulation.blueprint,
                "blueprint_description": blueprint.description if blueprint else None,
                "configuration": json.loads(emulation.logs) if emulation.logs else None,
                "stress_test": emulation.stress_test,
                "start_time": emulation.start_time.isoformat(),
                "controller_id": emulation.controller_id
            })

        return jsonify({"success": True, "emulations": detailed_emulations})
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

    # Validate input
    if not machine_ids or len(machine_ids) < 2:
        logger.warning("Invalid comparison request: Less than two machines provided.")
        return jsonify({"success": False, "error": "At least two machine IDs are required for comparison."}), 400

    try:
        # Fetch the status of each machine
        machine_statuses = []
        for machine_id in machine_ids:
            status_response = EmulatorService.get_machine_status(machine_id)
            if not status_response["success"]:
                return jsonify({"success": False, "error": f"Failed to fetch status for machine ID {machine_id}."}), 400
            machine_statuses.append({"machine_id": machine_id, "status": status_response["status"]})

        # Perform the comparison
        differences = EmulatorService.compare_operations(machine_statuses)

        # Return the results
        return jsonify({"success": True, "differences": differences})
    except Exception as e:
        logger.error(f"Error comparing machines: {e}")
        return jsonify({"success": False, "error": "Failed to compare machines."}), 500

@emulator_bp.route("/add-blueprint", methods=["POST"])
def add_blueprint_or_emulator():
    """Add a new blueprint or emulator."""
    try:
        data = request.json
        if not data:
            logger.error("No data received for adding blueprint/emulator.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        # Extract required fields
        name = data.get("name")
        description = data.get("description")
        blueprint_type = data.get("type", "blueprint")  # Default to blueprint if type is not provided

        if not name or not description:
            logger.error("Missing required fields in blueprint/emulator data.")
            return jsonify({"success": False, "message": "Missing required fields."}), 400

        # Add the blueprint/emulator
        result = EmulatorService.add_blueprint(
            name=name,
            description=description,
            protocol=data.get("protocol"),
            connection=data.get("connection"),
            settings=data.get("settings"),
            commands=data.get("commands"),
            data_format=data.get("data_format"),
            default_state=data.get("default_state"),
            version=data.get("version"),
            author=data.get("author"),
        )

        if result["success"]:
            logger.info(f"Successfully added {blueprint_type} '{name}'.")
            return jsonify(result), 200
        else:
            logger.error(f"Failed to add {blueprint_type}: {result['message']}")
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Error while adding blueprint/emulator.")
        return jsonify({"success": False, "message": "Internal server error."}), 500


