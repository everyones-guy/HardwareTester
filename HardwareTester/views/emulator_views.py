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

@emulator_bp.route("/add-blueprint", methods=["POST"])
def add_blueprint():
    """Add a new blueprint."""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        # Extract fields
        name = data.get("name")
        description = data.get("description")
        configuration = data.get("configuration")
        version = data.get("version")
        author = data.get("author")

        if not name or not description:
            return jsonify({"success": False, "message": "Name and description are required."}), 400

        response = EmulatorService.add_blueprint(name, description, configuration, version, author)
        return jsonify(response), 200 if response["success"] else 400
    except Exception as e:
        logger.error(f"Error adding blueprint: {e}")
        return jsonify({"success": False, "message": "Failed to add blueprint."}), 500

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

@emulator_bp.route("/add-emulator", methods=["POST"])
def add_emulator():
    """Add a new emulator."""
    try:
        data = request.json
        if not data:
            logger.error("No data received for adding emulator.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        # Extract required fields from the JSON
        name = data.get("name")
        description = data.get("description")
        configuration = data.get("configuration")
        if not name or not description or not configuration:
            logger.error("Missing required fields in emulator data.")
            return jsonify({"success": False, "message": "Missing required fields."}), 400

        # Call EmulatorService to save the emulator
        result = EmulatorService.add_blueprint(name=name, description=description, configuration=configuration)
        if result["success"]:
            logger.info(f"Successfully added emulator '{name}'.")
            return jsonify(result), 200
        else:
            logger.error(f"Failed to add emulator: {result['message']}")
            return jsonify(result), 400
    except Exception as e:
        logger.exception("Error while adding emulator.")
        return jsonify({"success": False, "message": "Internal server error."}), 500

@emulator_bp.route('/add-blueprint', methods=['POST'])
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

