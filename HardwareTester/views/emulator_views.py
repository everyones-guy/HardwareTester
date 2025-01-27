from flask import Blueprint, jsonify, request, render_template, current_app
from flask_login import login_required, current_user
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.utils.token_utils import get_token
from HardwareTester.forms import StartEmulationForm, AddEmulatorForm
from werkzeug.utils import secure_filename
import json
import os

# Initialize logger
#logger = CustomLogger.get_logger("emulator_views")

logger = CustomLogger.get_logger("Emulator_Views", per_module=True)


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
    """Load a new blueprint and commit all fields to the database."""
    blueprint_file = request.files.get("blueprint_file")
    if not blueprint_file:
        logger.warning("No blueprint file provided.")
        return jsonify({"success": False, "error": "No blueprint file provided."}), 400

    try:
        # Save the file temporarily and load it into the database
        temp_path = f"/tmp/{secure_filename(blueprint_file.filename)}"
        blueprint_file.save(temp_path)

        response = emulator_service.load_blueprint_from_file(temp_path)

        # Commit the loaded blueprint to the database
        if response["success"]:
            commit_response = emulator_service.commit_blueprint_to_database(response["blueprint"])
            if not commit_response["success"]:
                logger.warning(f"Failed to commit blueprint: {commit_response['message']}")
                return jsonify({"success": False, "message": commit_response["message"]}), 400

        # Remove the temporary file after processing
        os.remove(temp_path)
        return jsonify(response)
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in blueprint file.")
        return jsonify({"success": False, "message": "Invalid JSON format."}), 400
    except FileNotFoundError:
        logger.error("Temporary file not found during processing.")
        return jsonify({"success": False, "message": "Temporary file handling error."}), 500
    except Exception as e:
        logger.error(f"Error loading blueprint: {e}")
        return jsonify({"success": False, "error": "Failed to load blueprint."}), 500

   

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


@emulator_bp.route("/add", methods=["POST"])
@login_required
def add_emulator():
    """Add a new emulator by creating a blueprint and committing all fields to the database."""
    try:
        if request.content_type != "application/json":
            return jsonify({"success": False, "message": "Content-type must be application/json."}), 415
        
        data = request.get_json()
        if not data:
            logger.warning("No data provided for adding emulator.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        # Ensure all required fields are present
        required_fields = ["name", "description", "configuration"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing field: {field}")
                return jsonify({"success": False, "message": f"Missing field: {field}"}), 400

        # Save the emulator blueprint to the database
        response = emulator_service.add_blueprint(
            name=data["name"],
            description=data["description"],
            configuration=data["configuration"]
        )
        
        # Log success or error based on the response
        if response["success"]:
            logger.info(f"Emulator added successfully: {data['name']}")
            return jsonify({"success": True, "message": response["message"]}), 201
        else:
            logger.error(f"Failed to add emulator: {response['message']}")
            return jsonify({"success": False, "message": response["message"]}), 400
    except Exception as e:
        logger.error(f"Error adding emulator: {e}")
        return jsonify({"success": False, "message": "Failed to add emulator due to an internal error."}), 500


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
    
@emulator_bp.route("/start", methods=["GET", "POST"])
@login_required
def start_emulation():
    """
    Handle both rendering the start emulation page (GET) and starting emulation (POST).
    """
    form = StartEmulationForm()

    # Fetch blueprints and populate choices for the dropdown
    blueprint_response = emulator_service.fetch_blueprints()
    if blueprint_response["success"]:
        blueprints = blueprint_response["blueprints"]
        form.blueprint.choices = [(bp["name"], bp["name"]) for bp in blueprints]
    else:
        blueprints = []
        logger.warning("Failed to fetch blueprints for the start emulation page.")

    if request.method == "POST" and form.validate_on_submit():
        # Extract data from the form
        machine_name = form.machine_name.data
        blueprint = form.blueprint.data
        stress_test = form.stress_test.data

        try:
            # Attempt to start the emulation
            response = emulator_service.start_emulation(machine_name, blueprint, stress_test)
            if response["success"]:
                # Successful emulation start
                logger.info(f"Successfully started emulation: {response['message']}")
                return jsonify({"success": True, "message": response["message"]}), 200
            else:
                # Emulation start failed
                logger.warning(f"Emulation start failed: {response['message']}")
                return jsonify({"success": False, "message": response["message"]}), 400
        except Exception as e:
            # Handle any unexpected errors
            logger.error(f"Error starting emulation: {e}")
            return jsonify({"success": False, "error": "Failed to start emulation due to an internal error."}), 500

    # If GET request or invalid form submission, render the HTML page
    if request.method == "GET":
        return render_template("start_emulation.html", form=form)

    # Handle form validation errors
    logger.warning("Form validation failed while starting emulation.")
    return jsonify({"success": False, "error": "Invalid form submission."}), 400


@emulator_bp.route("/save-emulator-json", methods=["POST"])
@login_required
def save_emulator_json():
    """Save JSON data to the database and a file."""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No JSON data provided."}), 400

        filename = data.get('filename', 'default.json')
        json_data = data.get('data')

        if not json_data:
            return jsonify({"success": False, "message": "JSON data is missing."}), 400

        # Get the upload folder from the app configuration
        saved_json_folder = current_app.config["UPLOAD_MODIFIED_JSON_FILES"]

        # Ensure the folder exists
        os.makedirs(saved_json_folder, exist_ok=True)

        # Secure the filename
        filename = secure_filename(filename)
        file_path = os.path.join(saved_json_folder, filename)

        # Save the JSON data to the file
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=4)

        # Commit the JSON data to the database
        commit_response = emulator_service.save_json_to_database(filename, json_data)
        if not commit_response["success"]:
            logger.error(f"Failed to save JSON to database: {commit_response['message']}")
            return jsonify({"success": False, "message": commit_response["message"]}), 400

        return jsonify({"success": True, "message": f"JSON saved as {filename} and committed to the database."})
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")
        return jsonify({"success": False, "message": str(e)}), 500