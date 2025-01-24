import json
from typing import Dict, Any, Union
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime
from threading import Lock
from sqlalchemy.sql import func
from flask import current_app

from HardwareTester.extensions import db
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.services.mqtt_client import MQTTClient
from HardwareTester.models.device_models import Emulation, Blueprint, Controller, Peripheral  # Replace with actual path to your model
from HardwareTester.models.upload_models import UploadedFile
from HardwareTester.services.peripherals_service import PeripheralsService
from HardwareTester.services.serial_service import SerialService


# Initialize logger
logger = CustomLogger.get_logger("emulator_service")

class EmulatorService:
    # Emulator state
    emulator_state = {
        "running": False,
        "config": {"default_machine_name": "Machine1", "stress_test_mode": False},
        "active_emulations": [],
        "logs": [],
    }
    
    emulator_state_lock = Lock()

    def __init__(self):
        self.mqtt_client = MQTTClient(broker=os.getenv("MQTT_BROKER", "localhost"))
        self.serial_service = SerialService()
        self.peripherals_service = PeripheralsService()

    def initialize_state(self):
        """Load the emulator state from the database."""
        try:
            emulations = Emulation.query.all()
            with self.emulator_state_lock:
                self.emulator_state["active_emulations"] = [
                    {
                        "machine_name": e.machine_name,
                        "blueprint": e.blueprint,
                        "stress_test": e.stress_test,
                        "start_time": e.start_time.isoformat(),
                    }
                    for e in emulations
                ]
                self.emulator_state["running"] = bool(emulations)
            logger.info("Emulator state initialized.")
        except Exception as e:
            logger.error(f"Error initializing emulator state: {e}")

    def fetch_blueprints(self) -> Dict[str, Union[bool, Any]]:
        """Fetch available blueprints."""
        try:
            blueprints = Blueprint.query.all()
            blueprint_list = [
                {
                    "name": b.name,
                    "description": b.description,
                    "created_at": b.created_at.isoformat(),
                }
                for b in blueprints
            ]
            logger.info("Blueprints fetched successfully.")
            return {"success": True, "blueprints": blueprint_list}
        except Exception as e:
            logger.error(f"Error fetching blueprints: {e}")
            return {"success": False, "error": "Failed to fetch blueprints due to database issues."}


    def start_emulation(self, machine_name: str, blueprint: str, stress_test: bool = False) -> Dict[str, Union[bool, str]]:
        """Start a new emulation."""
        if not machine_name or not blueprint:
            return {"success": False, "message": "Machine name and blueprint are required."}

        try:
            if self.emulator_state["running"]:
                logger.warning("An emulation is already running.")
                return {"success": False, "message": "An emulation is already running."}

            controller_id = self.get_available_controller_id()
            if not controller_id:
                logger.warning("No available controller found.")
                return {"success": False, "message": "No available controller."}

            emulation = Emulation(
                controller_id=controller_id,
                machine_name=machine_name,
                blueprint=blueprint,
                stress_test=stress_test,
                start_time=datetime.utcnow(),
            )
            db.session.add(emulation)
            db.session.commit()

            with self.emulator_state_lock:
                self.emulator_state["active_emulations"].append(
                    {
                        "machine_name": machine_name,
                        "blueprint": blueprint,
                        "stress_test": stress_test,
                        "start_time": emulation.start_time.isoformat(),
                    }
                )
                self.emulator_state["running"] = True

            self._log_action(f"Started emulation for {machine_name} using blueprint '{blueprint}'.")
            return {"success": True, "message": f"Emulation started for machine '{machine_name}'."}
        except SQLAlchemyError as e:
            logger.error(f"Database error starting emulation: {e}")
            db.session.rollback()
            return {"success": False, "error": "Database error while starting emulation."}
        except Exception as e:
            logger.error(f"Unexpected error starting emulation: {e}")
            db.session.rollback()
            return {"success": False, "error": "Unexpected error while starting emulation."}


    def stop_emulation(self, machine_name: str) -> Dict[str, Union[bool, str]]:
        """Stop an active emulation."""
        if not machine_name:
            return {"success": False, "message": "Machine name is required."}

        try:
            emulation = Emulation.query.filter_by(machine_name=machine_name).first()
            if not emulation:
                return {"success": False, "message": f"No emulation found for machine '{machine_name}'."}

            db.session.delete(emulation)
            db.session.commit()

            with self.emulator_state_lock:
                self.emulator_state["active_emulations"] = [
                    e for e in self.emulator_state["active_emulations"] if e["machine_name"] != machine_name
                ]
                self.emulator_state["running"] = len(self.emulator_state["active_emulations"]) > 0

            self._log_action(f"Stopped emulation for machine '{machine_name}'.")
            return {"success": True, "message": f"Emulation stopped for machine '{machine_name}'."}
        except Exception as e:
            logger.error(f"Error stopping emulation: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to stop emulation."}

    def list_active_emulations(self) -> Dict[str, Union[bool, Any]]:
        """List all active emulations."""
        try:
            logger.info("Fetching list of active emulations.")
            return {"success": True, "emulations": self.emulator_state["active_emulations"]}
        except Exception as e:
            logger.error(f"Error fetching active emulations: {e}")
            return {"success": False, "error": "Failed to fetch active emulations."}

    def get_emulator_logs(self) -> Dict[str, Union[bool, Any]]:
        """Retrieve logs from the emulator."""
        try:
            logger.info("Fetching emulator logs.")
            return {"success": True, "logs": self.emulator_state["logs"]}
        except Exception as e:
            logger.error(f"Error fetching emulator logs: {e}")
            return {"success": False, "error": "Failed to fetch emulator logs."}

    def load_blueprint(self, blueprint_name: str) -> Dict[str, Union[bool, Any]]:
        """Load a specific blueprint by name."""
        try:
            blueprint = Blueprint.query.filter_by(name=blueprint_name).first()
            if not blueprint:
                logger.warning(f"Blueprint '{blueprint_name}' not found.")
                return {"success": False, "message": f"Blueprint '{blueprint_name}' not found."}

            blueprint_details = {
                "name": blueprint.name,
                "description": blueprint.description,
                "created_at": blueprint.created_at.isoformat(),
                "configuration": blueprint.configuration,
            }
            logger.info(f"Loaded blueprint '{blueprint_name}'.")
            return {"success": True, "blueprint": blueprint_details}
        except Exception as e:
            logger.error(f"Error loading blueprint '{blueprint_name}': {e}")
            return {"success": False, "error": "Failed to load blueprint."}

    def add_blueprint(self, name: str, description: str, configuration: Dict) -> Dict[str, Union[bool, str]]:
        """
        Add a blueprint by file or JSON text. One of them must be provided.
        """
        try:

            existing_blueprint = Blueprint.query.filter_by(name=name).first()
            if existing_blueprint:
                logger.warning(f"Blueprint '{name}' already exists.")
                return {"success": False, "message": f"Blueprint with name '{name}' already exists."}

            new_blueprint = Blueprint(
                name=name,
                description=description,
                configuration=json.dumps(configuration),
                created_at=datetime.utcnow(),
            )
            db.session.add(new_blueprint)
            db.session.commit()

            logger.info(f"Blueprint '{name}' added successfully.")
            return {"success": True, "message": f"Blueprint '{name}' added successfully."}
        except Exception as e:
            logger.error(f"Error adding blueprint '{name}': {str(e)}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to add blueprint: {str(e)}"}

    def handle_file_upload(self, file) -> Dict[str, Union[str, int]]:
        """Handle file upload for blueprints."""
        try:
            # Get the upload folder path from configuration
            upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER_ROOT'), 'blueprints')
        
            # Ensure the folder exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Save the file securely
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # Add to database (optional, depends on your UploadedFile model)
            new_file = UploadedFile(filename=filename, path=file_path)
            db.session.add(new_file)
            db.session.commit()

            logger.info(f"File '{filename}' uploaded successfully to '{file_path}'.")
            return {"id": new_file.id, "filename": filename}
        except SQLAlchemyError as e:
            logger.error(f"Database error while uploading file: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to upload file."}
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            return {"success": False, "error": "Unexpected error occurred during file upload."}

    def fetch_commands_from_firmware(self, blueprint_name: str) -> list:
        """
        Fetch all commands for the given blueprint directly from the firmware.
        :param blueprint_name: Name of the blueprint or hardware configuration.
        :return: List of commands, each as a dictionary with details.
        """
        try:
            # Example API interaction to retrieve commands
            response = self.api_call(
                f"/firmware/{blueprint_name}/full-command-list",
                method="GET"
            )
            
            if response.get("success"):
                return response.get("commands", [])
            else:
                logger.warning(f"Failed to fetch commands from firmware for {blueprint_name}: {response.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error fetching commands for {blueprint_name}: {e}")
            return []

    def fetch_commands_via_mqtt(self, topic: str, broker: str = "localhost", port: int = 1883) -> list:
        """Fetch command listing via MQTT by subscribing to a specific topic."""
        commands = []

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                commands.extend(payload.get("commands", []))
            except Exception as e:
                logger.error(f"Error parsing MQTT message: {e}")

        self.mqtt_client.client.on_message = on_message

        try:
            logger.info(f"Connecting to MQTT broker at {broker}:{port}...")
            self.mqtt_client.client.connect(broker, port, 60)
            self.mqtt_client.client.subscribe(topic)
            self.mqtt_client.client.loop_start()

            # Wait for the message (adjust timeout as needed)
            import time
            time.sleep(5)

            self.mqtt_client.client.loop_stop()
            self.mqtt_client.client.disconnect()
            logger.info("MQTT command listing fetched successfully.")
        except Exception as e:
            logger.error(f"Error fetching commands via MQTT: {e}")

        return commands
 
    def _log_action(self, message: str):
        """Log an action with rotation to limit memory growth."""
        timestamp = datetime.now().isoformat()
        with self.emulator_state_lock:
            self.emulator_state["logs"].append(f"[{timestamp}] {message}")
            if len(self.emulator_state["logs"]) > 1000:
                self.emulator_state["logs"] = self.emulator_state["logs"][-1000:]
        logger.info(message)

        
    def get_available_controller_id(self) -> Union[int, None]:
        """Get an available controller ID."""
        try:
            controllers = Controller.query.all()
            for ctrl in controllers:
                logger.info(f"Controller {ctrl.id}: available={ctrl.available}, name={ctrl.name}")
        
            controller = Controller.query.filter_by(available=True).first()
            if controller:
                logger.info(f"Available controller found: {controller.id}")
                return controller.id
            else:
                logger.warning("No available controllers found.")
                return None
        except Exception as e:
            logger.error(f"Error fetching available controller: {e}")
            return None


    def load_blueprint_from_file(self, file_path: str) -> Dict[str, Union[bool, str]]:
        """
        Load a blueprint from a JSON file and store it in the database.
        :param file_path: Path to the JSON file containing the blueprint configuration.
        :return: A dictionary indicating success or failure with a message.
        """
        try:
            # Read the JSON file
            with open(file_path, "r") as file:
                blueprint_data = json.load(file)

            # Validate required fields in JSON
            required_fields = ["controller", "controller.name", "controller.connection", "controller.peripherals"]
            for field in required_fields:
                keys = field.split(".")
                data = blueprint_data
                for key in keys:
                    if key not in data:
                        raise ValueError(f"Missing required field in JSON: {field}")
                    data = data[key]

            # Extract controller details
            controller_name = blueprint_data["controller"]["name"]
            controller_connection = blueprint_data["controller"]["connection"]
            peripherals = blueprint_data["controller"]["peripherals"]

            # Add or update the controller in the database
            controller = Controller.query.filter_by(name=controller_name).first()
            if not controller:
                controller = Controller(
                    name=controller_name,
                    device_metadata=controller_connection,
                )
                db.session.add(controller)
                db.session.flush()  # Ensure `controller.id` is available

            # Handle peripherals
            self._add_or_update_peripherals(controller.id, peripherals)

            # Add blueprint to the database
            blueprint_name = blueprint_data["controller"]["name"]
            blueprint_description = f"Blueprint for {controller_name}"
            blueprint_configuration = blueprint_data

            existing_blueprint = Blueprint.query.filter_by(name=blueprint_name).first()
            if existing_blueprint:
                return {"success": False, "message": f"Blueprint '{blueprint_name}' already exists."}

            new_blueprint = Blueprint(
                name=blueprint_name,
                description=blueprint_description,
                configuration=blueprint_configuration,
            )
            db.session.add(new_blueprint)

            # Commit all changes to the database
            db.session.commit()

            logger.info(f"Blueprint '{blueprint_name}' loaded successfully.")
            return {"success": True, "message": f"Blueprint '{blueprint_name}' loaded successfully."}

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {"success": False, "message": f"File not found: {file_path}"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in file: {file_path}")
            return {"success": False, "message": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            logger.error(f"Error loading blueprint from file: {e}")
            db.session.rollback()
            return {"success": False, "message": f"Error loading blueprint: {str(e)}"}

    def _add_or_update_peripherals(self, controller_id: int, peripherals: list):
        """
        Add or update peripherals for a given controller.
        :param controller_id: ID of the associated controller.
        :param peripherals: List of peripheral dictionaries.
        """
        try:
            for peripheral in peripherals:
                if "name" not in peripheral or "type" not in peripheral:
                    raise ValueError("Peripheral must include 'name' and 'type'.")

                existing_peripheral = Peripheral.query.filter_by(name=peripheral["name"], device_id=controller_id).first()
                if existing_peripheral:
                    existing_peripheral.type = peripheral["type"]
                    existing_peripheral.properties = peripheral
                else:
                    new_peripheral = Peripheral(
                        name=peripheral["name"],
                        type=peripheral["type"],
                        properties=peripheral,
                        device_id=controller_id,
                    )
                    db.session.add(new_peripheral)
            db.session.commit()

        except Exception as e:
            logger.error(f"Error adding/updating peripherals: {e}")
            raise
        
    def save_uploaded_file(self, file, subfolder=''):
        """
        Save an uploaded file to the specified subfolder.
        :param file: File object from the request.
        :param subfolder: Subfolder under UPLOAD_FOLDER_ROOT.
        :return: Full path to the saved file.
        """
        try:
            # Get the upload folder root from the app configuration
            upload_folder_root = current_app.config.get('UPLOAD_FOLDER_ROOT', 'uploads')
            upload_folder = os.path.join(upload_folder_root, subfolder) if subfolder else upload_folder_root

            # Ensure the subfolder exists
            os.makedirs(upload_folder, exist_ok=True)

            # Secure the filename and save the file
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            logger.info(f"File '{filename}' saved successfully in '{file_path}'.")
            return file_path
        except Exception as e:
            logger.error(f"Error saving file '{file.filename}': {e}")
            raise ValueError(f"Failed to save file: {e}")
