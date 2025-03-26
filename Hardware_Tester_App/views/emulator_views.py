from flask import Blueprint, jsonify, request, render_template, current_app
from flask_login import login_required, current_user
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.utils.token_utils import get_token
from HardwareTester.utils.source_code_analyzer import SourceCodeAnalyzer
from HardwareTester.forms import StartEmulationForm, AddEmulatorForm
from datetime import datetime
from HardwareTester.utils.api_manager import APIManager
from werkzeug.utils import secure_filename
import json
import os
from dotenv import load_dotenv

# Load up the env file
load_dotenv()

# Fetch MQTT broker from .env with a fallback to "localhost"
BASE_URL = os.getenv("BASE_URL", "localhost")

# Initialize logger
#logger = CustomLogger.get_logger("emulator_views")

logger = CustomLogger.get_logger("Emulator_Views", per_module=True)

# Create an API Manager instance
api_manager = APIManager(base_url=BASE_URL)

# Define the Blueprint
emulator_bp = Blueprint("emulators", __name__)

# Instantiate EmulatorService
emulator_service = EmulatorService

@emulator_bp.route("/emulators", methods=["GET", "POST"])
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


@emulator_bp.route("/api/emulators/blueprints", methods=["GET"])
@login_required
def get_blueprints():
    """Fetch available blueprints."""
    try:
        response = emulator_service.fetch_blueprints()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching blueprints: {e}")
        return jsonify({"success": False, "error": "Failed to fetch blueprints."}), 500


@emulator_bp.route("/api/emulators/load-blueprint", methods=["POST"])
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

   

@emulator_bp.route("/api/emulators/stop", methods=["POST"])
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


@emulator_bp.route("/api/emulators/list", methods=["GET"])
@login_required
def list_emulations():
    """List all active emulations."""
    try:
        response = emulator_service.list_active_emulations()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error listing active emulations: {e}")
        return jsonify({"success": False, "error": "Failed to fetch active emulations."}), 500


@emulator_bp.route("/api/emulators/logs", methods=["GET"])
@login_required
def get_logs():
    """Fetch emulator logs."""
    try:
        response = emulator_service.get_emulator_logs()
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching emulator logs: {e}")
        return jsonify({"success": False, "error": "Failed to fetch emulator logs."}), 500


@emulator_bp.route("/api/emulators/compare", methods=["POST"])
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
    

@emulator_bp.route("/api/emulators/add", methods=["POST"])
@login_required
def add_device():
    """
    Add a new device (emulator, peripheral, etc.) with minimal JSON input.
    Each device is treated as a record that defines its capabilities and behavior.
    """
    try:
        # Ensure the content type is JSON
        if request.content_type != "application/json":
            return jsonify({"success": False, "message": "Content-type must be application/json."}), 415

        # Get the JSON payload
        data = request.get_json()
        if not data:
            logger.warning("No data provided for adding device.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        # Treat the JSON as a flat, quick record for defining a device
        device_record = {
            "name": data.get("name", f"Device-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "type": data.get("type", "generic"),
            "capabilities": data.get("capabilities", {}),
            "metadata": {k: v for k, v in data.items() if k not in ["name", "type", "capabilities"]},
        }

        # Save the record to the database
        response = emulator_service.add_device(device_record)

        # Log and return the result
        if response["success"]:
            logger.info(f"Device '{device_record['name']}' added successfully.")
            return jsonify({
                "success": True,
                "message": f"Device '{device_record['name']}' added successfully.",
                "device": device_record
            }), 201
        else:
            logger.error(f"Failed to add device: {response['message']}")
            return jsonify({"success": False, "message": response["message"]}), 400

    except Exception as e:
        logger.error(f"Error adding device: {e}")
        return jsonify({"success": False, "message": "Failed to add device due to an internal error."}), 500



@emulator_bp.route("/api/emulators/add-emulator", methods=["POST"])
@login_required
def add_emulator():
    """
    Add a new emulator by creating a blueprint and committing all fields to the database.
    Handles unstructured JSON data gracefully, attempts to organize it, 
    and provides a preview for user confirmation or modification.
    """
    try:
        if request.content_type != "application/json":
            return jsonify({"success": False, "message": "Content-type must be application/json."}), 415

        data = request.get_json()
        if not data:
            logger.warning("No data provided for adding emulator.")
            return jsonify({"success": False, "message": "No data provided."}), 400

        # Base fields to look for
        required_fields = ["name", "description", "configuration"]
        missing_fields = [field for field in required_fields if field not in data]

        # Try to identify missing or additional fields dynamically
        organized_data = {
            "name": data.get("name", "Unnamed Emulator"),
            "description": data.get("description", "No description provided."),
            "configuration": data.get("configuration", {}),
            "additional_fields": {k: v for k, v in data.items() if k not in required_fields}
        }

        if missing_fields:
            logger.warning(f"Missing fields detected: {missing_fields}")

        # Attempt to auto-map disorganized or nested data into structured configuration
        if not isinstance(organized_data["configuration"], dict):
            try:
                organized_data["configuration"] = json.loads(organized_data["configuration"])
                logger.info("Configuration field auto-parsed from JSON string.")
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse configuration field into a JSON object.")
                organized_data["configuration"] = {"raw_data": data.get("configuration", "Unstructured input")}

        # Flatten nested or complex data into editable chunks
        flattened_layout = flatten_json(organized_data["configuration"])

        # Display organized data in a JSON editor-friendly format
        proposed_layout = {
            "base": {
                "name": organized_data["name"],
                "description": organized_data["description"]
            },
            "configuration": flattened_layout,
            "additional": organized_data["additional_fields"]
        }

        # Save to database after confirmation
        response = emulator_service.add_blueprint(
            name=organized_data["name"],
            description=organized_data["description"],
            configuration=organized_data["configuration"]
        )

        if response["success"]:
            logger.info(f"Emulator added successfully: {organized_data['name']}")
            return jsonify({
                "success": True,
                "message": response["message"],
                "proposed_layout": proposed_layout
            }), 201
        else:
            logger.error(f"Failed to add emulator: {response['message']}")
            return jsonify({"success": False, "message": response["message"], "proposed_layout": proposed_layout}), 400

    except Exception as e:
        logger.error(f"Error adding emulator: {e}")
        return jsonify({"success": False, "message": "Failed to add emulator due to an internal error."}), 500


def flatten_json(data, parent_key='', sep='.'):
    """
    Flatten nested JSON data into a single level with dot notation keys.
    """
    items = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for idx, item in enumerate(v):
                    items.extend(flatten_json(item, f"{new_key}[{idx}]", sep=sep).items())
            else:
                items.append((new_key, v))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            items.extend(flatten_json(item, f"{parent_key}[{idx}]", sep=sep).items())
    else:
        items.append((parent_key, data))
    return dict(items)



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
    
@emulator_bp.route("/api/emulators/emulate", methods=["POST"])
@login_required
def start_emulator():
    try:
        device_id = request.json.get("device_id")
        device_data = api_manager.get_device_from_db(device_id)

        # Parse source code
        analyzer = SourceCodeAnalyzer()
        metadata = analyzer.parse_file(device_data["source_path"], device_data["language"])

        # Start MQTT communication
        api_manager.start_mqtt_communication(device_id)

        return jsonify({
            "success": True,
            "message": f"Emulation started for {device_data['name']}",
            "metadata": metadata
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@emulator_bp.route("/api/emulators/start", methods=["GET", "POST"])
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


@emulator_bp.route("/api/emulators/save-emulator-json", methods=["POST"])
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