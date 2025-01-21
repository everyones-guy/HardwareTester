from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.utils.token_utils import get_token
from HardwareTester.forms import StartEmulationForm, AddEmulatorForm

import json

# Initialize logger
logger = CustomLogger.get_logger("emulator_views")

# Define the Blueprint
emulator_bp = Blueprint("emulators", __name__, url_prefix="/emulators")

# Instantiate EmulatorService
emulator_service = EmulatorService()

@emulator_bp.route("/", methods=["GET", "POST"])
@login_required
def emulator_dashboard():
    """Render the emulator dashboard."""
    try:
        form = StartEmulationForm()
        add_form = AddEmulatorForm()

        # Fetch blueprints using the EmulatorService
        blueprint_response = emulator_service.fetch_blueprints()

        if blueprint_response["success"]:
            blueprints = blueprint_response["blueprints"]
            # Populate blueprint choices dynamically
            form.blueprint.choices = [(bp["name"], bp["name"]) for bp in blueprints]
        else:
            blueprints = []
            logger.warning("Failed to fetch blueprints for dashboard display.")

        return render_template(
            "emulator.html",
            form=form,
            add_form=add_form,
            blueprints=blueprints
        )
    except Exception as e:
        logger.error(f"Error rendering emulator dashboard: {e}")
        return jsonify({"success": False, "error": "Failed to render the emulator dashboard."}), 500


@emulator_bp.route("/blueprints", methods=["GET"])
@login_required
def get_blueprints():
    """Fetch available blueprints."""
    try:
        response = emulator_service.fetch_blueprints()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching blueprints: {e}")
        return jsonify({"success": False, "error": "Failed to fetch blueprints."}), 500


@emulator_bp.route("/load-blueprint", methods=["POST"])
@login_required
def load_blueprint_endpoint():
    """Load a new blueprint."""
    blueprint_file = request.files.get("blueprint_file")
    if not blueprint_file:
        logger.warning("No blueprint file provided.")
        return jsonify({"success": False, "error": "No blueprint file provided."}), 400
    try:
        response = emulator_service.load_blueprint(blueprint_file)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error loading blueprint: {e}")
        return jsonify({"success": False, "error": "Failed to load blueprint."}), 500


@emulator_bp.route("/start", methods=["GET", "POST"])
@login_required
def start_emulation_endpoint():
    """Start a machine emulation."""
    form = StartEmulationForm()

    # Populate the blueprint choices dynamically
    blueprints = emulator_service.fetch_blueprints()
    form.blueprint.choices = [(bp['id'], bp['name']) for bp in blueprints]

    if form.validate_on_submit():
        machine_name = form.machine_name.data
        blueprint = form.blueprint.data
        stress_test = form.stress_test.data

        try:
            # Start the emulation process
            response = emulator_service.start_emulation(machine_name, blueprint, stress_test)
            if response["success"]:
                return jsonify({"success": True, "message": "Emulation started successfully!"})
            else:
                return jsonify({"success": False, "error": response["message"]}), 400
        except Exception as e:
            logger.error(f"Error starting emulation: {e}")
            return jsonify({"success": False, "error": "Failed to start emulation."}), 500

    # Render the form if GET request or validation fails
    return render_template("start_emulation.html", form=form)


@emulator_bp.route("/stop", methods=["POST"])
@login_required
def stop_emulation_endpoint():
    """Stop a machine emulation."""
    try:
        data = request.json or {}
        machine_name = data.get("machine_name")

        if not machine_name:
            logger.warning("Machine name is missing.")
            return jsonify({"success": False, "error": "Machine name is required."}), 400

        response = emulator_service.stop_emulation(machine_name)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error stopping emulation: {e}")
        return jsonify({"success": False, "error": "Failed to stop emulation."}), 500


@emulator_bp.route("/list", methods=["GET"])
@login_required
def list_emulations():
    """List all active emulations."""
    try:
        response = emulator_service.list_active_emulations()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error listing active emulations: {e}")
        return jsonify({"success": False, "error": "Failed to fetch active emulations."}), 500


@emulator_bp.route("/logs", methods=["GET"])
@login_required
def get_logs():
    """Fetch emulator logs."""
    try:
        response = emulator_service.get_emulator_logs()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching emulator logs: {e}")
        return jsonify({"success": False, "error": "Failed to fetch emulator logs."}), 500


@emulator_bp.route("/compare", methods=["POST"])
@login_required
def compare_machines():
    """Compare the operation of machines running different firmware."""
    try:
        data = request.json or {}
        machine_ids = data.get("machine_ids", [])

        if not machine_ids or len(machine_ids) < 2:
            logger.warning("Invalid comparison request: Less than two machines provided.")
            return jsonify({"success": False, "error": "At least two machines are required for comparison."}), 400

        comparisons = [
            {"machine_id": machine_id, "status": emulator_service.get_machine_status(machine_id)}
            for machine_id in machine_ids
        ]
        differences = emulator_service.compare_operations(comparisons)
        return jsonify({"success": True, "differences": differences})
    except Exception as e:
        logger.error(f"Error comparing machines: {e}")
        return jsonify({"success": False, "error": "Failed to compare machines."}), 500


@emulator_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_emulator():
    """Add a new emulator by creating a blueprint."""
    add_form = AddEmulatorForm()

    if add_form.validate_on_submit():
        try:
            file = add_form.file.data
            json_text = add_form.json_text.data

            # Ensure at least one source is provided
            if not file and not json_text:
                logger.warning("No file or JSON text provided.")
                return jsonify({"success": False, "message": "Either a file or JSON text must be provided."}), 400

            # Process uploaded file if available
            configuration = None
            if file:
                configuration = file.read().decode("utf-8")
            else:
                configuration = json_text

            # Add blueprint to the service
            response = emulator_service.add_blueprint(
                name=add_form.name.data,
                description=add_form.description.data,
                configuration=configuration,
            )

            if response["success"]:
                logger.info(f"Successfully added emulator: {response['message']}")
                return jsonify({"success": True, "message": response["message"]}), 201
            else:
                logger.error(f"Failed to add emulator: {response['message']}")
                return jsonify({"success": False, "message": response["message"]}), 400

        except Exception as e:
            logger.error(f"Error adding emulator: {e}")
            return jsonify({"success": False, "message": "Failed to add emulator."}), 500

    # Render the form if GET request or validation fails
    return render_template("add_emulator.html", add_form=add_form)


@emulator_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """Handle file uploads for emulators."""
    try:
        file = request.files.get("file")
        if not file or file.filename == "":
            return jsonify({"error": "No file provided or selected."}), 400

        result = emulator_service.handle_file_upload(file)
        return jsonify({"message": "File uploaded successfully", "result": result}), 200
    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
        return jsonify({"error": str(e)}), 500

@emulator_bp.route("/preview/<string:blueprint_name>", methods=["GET"])
@login_required
def preview_blueprint(blueprint_name):
    """Generate a preview for a blueprint."""
    try:
        # Replace with the actual logic to generate a preview
        blueprint = emulator_service.load_blueprint(blueprint_name)
        if not blueprint["success"]:
            return jsonify({"success": False, "message": blueprint["message"]}), 404

        # Assuming `preview_url` is a field in your blueprint model or logic
        return jsonify({"success": True, "preview_url": blueprint["blueprint"].get("preview_url", "")})
    except Exception as e:
        logger.error(f"Error generating preview for blueprint '{blueprint_name}': {e}")
        return jsonify({"success": False, "error": "Failed to generate blueprint preview."}), 500
