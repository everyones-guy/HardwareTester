import json
from typing import Dict, Any, Union
from werkzeug.utils import secure_filename
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime

from HardwareTester.extensions import db
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.services.mqtt_client import MQTTClient
from HardwareTester.models.device_models import Emulation, Blueprint  # Replace with actual path to your model
from HardwareTester.models.upload_files import UploadedFile
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

    def __init__(self):
        self.mqtt_client = MQTTClient(broker="localhost")
        self.serial_service = SerialService()
        self.peripherals_service = PeripheralsService()

    def initialize_state(self):
        """Load the emulator state from the database."""
        try:
            emulations = Emulation.query.all()
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
            logger.info("Emulator state initialized from the database.")
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
            logger.info("Fetching blueprints.")
            return {"success": True, "blueprints": blueprint_list}
        except Exception as e:
            logger.error(f"Error fetching blueprints: {e}")
            return {"success": False, "error": "Failed to fetch blueprints."}

    def start_emulation(self, machine_name: str, blueprint: str, stress_test: bool = False) -> Dict[str, Union[bool, str]]:
        """Start a new emulation."""
        try:
            if self.emulator_state["running"]:
                return {"success": False, "message": "An emulation is already running."}

            emulation = Emulation(
                machine_name=machine_name,
                blueprint=blueprint,
                stress_test=stress_test,
                start_time=datetime.utcnow(),
            )
            db.session.add(emulation)
            db.session.commit()

            # Update in-memory state
            self.emulator_state["active_emulations"].append(
                {
                    "machine_name": machine_name,
                    "blueprint": blueprint,
                    "stress_test": stress_test,
                    "start_time": emulation.start_time.isoformat(),
                }
            )
            self.emulator_state["running"] = True

            self._log_action(f"Started emulation for {machine_name} using blueprint '{blueprint}'")
            return {"success": True, "message": f"Emulation started for machine '{machine_name}'."}
        except Exception as e:
            logger.error(f"Error starting emulation: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to start emulation."}

    def stop_emulation(self, machine_name: str) -> Dict[str, Union[bool, str]]:
        """Stop an active emulation."""
        try:
            emulation = Emulation.query.filter_by(machine_name=machine_name).first()
            if not emulation:
                return {"success": False, "message": f"No emulation found for machine '{machine_name}'."}

            db.session.delete(emulation)
            db.session.commit()

            # Update in-memory state
            self.emulator_state["active_emulations"] = [
                e for e in self.emulator_state["active_emulations"] if e["machine_name"] != machine_name
            ]
            self.emulator_state["running"] = len(self.emulator_state["active_emulations"]) > 0

            self._log_action(f"Stopped emulation for machine '{machine_name}'")
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
        """Add a new blueprint to the database."""
        try:
            existing_blueprint = Blueprint.query.filter_by(name=name).first()
            if existing_blueprint:
                logger.warning(f"Blueprint '{name}' already exists.")
                return {"success": False, "message": f"Blueprint with name '{name}' already exists."}

            new_blueprint = Blueprint(
                name=name,
                description=description,
                configuration=configuration,
                created_at=datetime.utcnow(),
            )
            db.session.add(new_blueprint)
            db.session.commit()

            logger.info(f"Blueprint '{name}' added successfully.")
            return {"success": True, "message": f"Blueprint '{name}' added successfully."}
        except Exception as e:
            logger.error(f"Error adding blueprint '{name}': {e}")
            db.session.rollback()
            return {"success": False, "error": f"Failed to add blueprint: {e}"}

    def handle_file_upload(self, file) -> Dict[str, Union[str, int]]:
        """Handle file upload for blueprints."""
        try:
            filename = secure_filename(file.filename)
            save_path = os.path.join("uploads/blueprints", filename)
            file.save(save_path)

            new_file = UploadedFile(filename=filename, path=save_path)
            db.session.add(new_file)
            db.session.commit()

            logger.info(f"File '{filename}' uploaded successfully.")
            return {"id": new_file.id, "filename": filename}
        except SQLAlchemyError as e:
            logger.error(f"Database error while uploading file: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to upload file."}
        

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
 
    def _log_action(message: str):
        """Log an action to the emulator logs."""
        EmulatorService.emulator_state["logs"].append(f"[{datetime.now()}] {message}")
        logger.info(message)