import json
from datetime import datetime
from HardwareTester.extensions import db
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.models.device_models import Emulation, Blueprint  # Replace with actual path to your model
from typing import Dict, Any, Union

# Initialize logger
logger = CustomLogger.get_logger("emulator_service")

class EmulatorService:
    # Emulator state
    emulator_state = {
        "running": False,
        "config": {
            "default_machine_name": "Machine1",
            "stress_test_mode": False,
        },
        "active_emulations": [],
        "logs": [],
    }

    @staticmethod
    def initialize_state():
        """Load the emulator state from the database."""
        try:
            emulations = Emulation.query.all()
            EmulatorService.emulator_state["active_emulations"] = [
                {
                    "machine_name": e.machine_name,
                    "blueprint": e.blueprint,
                    "stress_test": e.stress_test,
                    "start_time": e.start_time.isoformat(),
                }
                for e in emulations
            ]
            EmulatorService.emulator_state["running"] = bool(emulations)
            logger.info("Emulator state initialized from the database.")
        except Exception as e:
            logger.error(f"Error initializing emulator state: {e}")

    # Fetch blueprint data
    @staticmethod
    def fetch_blueprints() -> Dict[str, Union[bool, Any]]:
        """Fetch available blueprints."""
        try:
            blueprints = Blueprint.query.all()
            blueprint_list = [
                {
                    "name": b.name,
                    "description": b.description,
                    "created_at": b.created_at,
                    "updated_at": b.updated_at,
                    "version": b.version,
                    "author": b.author,
                    "configuration": b.configuration,
                }
                for b in blueprints
            ]
            logger.info("Fetching blueprints.")
            return {"success": True, "blueprints": blueprint_list}
        except Exception as e:
            logger.error(f"Error fetching blueprints: {e}")
            return {"success": False, "error": "Failed to fetch blueprints."}

    # Start an emulation
    @staticmethod
    def start_emulation(machine_name: str, blueprint: str, stress_test: bool = False) -> Dict[str, Union[bool, str]]:
        """Start a new emulation."""
        try:
            if EmulatorService.emulator_state["running"]:
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
            EmulatorService.emulator_state["active_emulations"].append({
                "machine_name": machine_name,
                "blueprint": blueprint,
                "stress_test": stress_test,
                "start_time": emulation.start_time.isoformat(),
            })
            EmulatorService.emulator_state["running"] = True

            log_message = f"Started emulation for {machine_name} using blueprint '{blueprint}'"
            EmulatorService._log_action(log_message)
            return {"success": True, "message": f"Emulation started for machine '{machine_name}'."}
        except Exception as e:
            logger.error(f"Error starting emulation: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to start emulation."}

    # Stop an emulation by name
    @staticmethod
    def stop_emulation(machine_name: str) -> Dict[str, Union[bool, str]]:
        """Stop an active emulation."""
        try:
            emulation = Emulation.query.filter_by(machine_name=machine_name).first()
            if not emulation:
                return {"success": False, "message": f"No emulation found for machine '{machine_name}'."}

            db.session.delete(emulation)
            db.session.commit()

            # Update in-memory state
            EmulatorService.emulator_state["active_emulations"] = [
                e for e in EmulatorService.emulator_state["active_emulations"] if e["machine_name"] != machine_name
            ]
            EmulatorService.emulator_state["running"] = len(EmulatorService.emulator_state["active_emulations"]) > 0

            log_message = f"Stopped emulation for machine '{machine_name}'"
            EmulatorService._log_action(log_message)
            return {"success": True, "message": f"Emulation stopped for machine '{machine_name}'."}
        except Exception as e:
            logger.error(f"Error stopping emulation: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to stop emulation."}

    # List all active emulations
    @staticmethod
    def list_active_emulations() -> Dict[str, Union[bool, Any]]:
        """List all active emulations."""
        try:
            logger.info("Fetching list of active emulations.")
            return {"success": True, "emulations": EmulatorService.emulator_state["active_emulations"]}
        except Exception as e:
            logger.error(f"Error fetching active emulations: {e}")
            return {"success": False, "error": "Failed to fetch active emulations."}
    
    # Fetch emulator logs
    @staticmethod
    def get_emulator_logs() -> Dict[str, Union[bool, Any]]:
        """Retrieve logs from the emulator."""
        try:
            logger.info("Fetching emulator logs.")
            return {"success": True, "logs": EmulatorService.emulator_state["logs"]}
        except Exception as e:
            logger.error(f"Error fetching emulator logs: {e}")
            return {"success": False, "error": "Failed to fetch emulator logs."}

    @staticmethod
    def _log_action(message: str):
        """Log an action to the emulator logs."""
        EmulatorService.emulator_state["logs"].append(f"[{datetime.now()}] {message}")
        logger.info(message)

    # Load Blueprint by name
    @staticmethod
    def load_blueprint(blueprint_name: str) -> Dict[str, Union[bool, Any]]:
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
                "updated_at": blueprint.updated_at.isoformat() if blueprint.updated_at else None,
                "version": blueprint.version,
                "author": blueprint.author,
                "configuration": blueprint.configuration,
            }
            logger.info(f"Loaded blueprint '{blueprint_name}'.")
            return {"success": True, "blueprint": blueprint_details}
        except Exception as e:
            logger.error(f"Error loading blueprint '{blueprint_name}': {e}")
            return {"success": False, "error": "Failed to load blueprint."}

    # Add a new blueprint to the database
    @staticmethod
    def add_blueprint(name: str, description: str, configuration: dict = None, version: str = None, author: str = None) -> Dict[str, Union[bool, str]]:
        """
        Add a new blueprint to the database.

        :param name: The name of the blueprint.
        :param description: A description of the blueprint.
        :param configuration: Optional configuration details as a dictionary.
        :param version: Optional version of the blueprint.
        :param author: Optional author of the blueprint.
        :return: A dictionary indicating success or failure with a message.
        """
        try:
            # Check if a blueprint with the same name already exists
            existing_blueprint = Blueprint.query.filter_by(name=name).first()
            if existing_blueprint:
                return {"success": False, "message": f"Blueprint with name '{name}' already exists."}

            # Create and add the new blueprint
            new_blueprint = Blueprint(
                name=name,
                description=description,
                configuration=configuration,
                version=version,
                author=author,
            )
            db.session.add(new_blueprint)
            db.session.commit()

            logger.info(f"Blueprint '{name}' added successfully.")
            return {"success": True, "message": f"Blueprint '{name}' added successfully."}
        except Exception as e:
            logger.error(f"Error adding blueprint '{name}': {e}")
            db.session.rollback()
            return {"success": False, "message": f"Failed to add blueprint '{name}': {str(e)}"}

    # Compare different machines
    @staticmethod
    def get_machine_status(machine_id: int) -> Dict[str, Union[bool, Any]]:
        """Fetch the status of a specific machine."""
        try:
            machine = Emulation.query.filter_by(id=machine_id).first()
            if not machine:
                return {"success": False, "message": f"Machine with ID {machine_id} not found."}

            return {
                "success": True,
                "status": {
                    "machine_id": machine.id,
                    "machine_name": machine.machine_name,
                    "blueprint": machine.blueprint,
                    "status": machine.status,
                    "logs": machine.logs,
                },
            }
        except Exception as e:
            logger.error(f"Error fetching status for machine ID {machine_id}: {e}")
            return {"success": False, "message": "Failed to fetch machine status."}
    
    @staticmethod
    def compare_operations(machine_statuses: list) -> list:
        """Compare operations across all pairs of machines."""
        try:
            differences = []

            # Compare every machine with every other machine
            for i, baseline in enumerate(machine_statuses):
                for j, machine in enumerate(machine_statuses):
                    if i >= j:  # Skip self-comparison and already compared pairs
                        continue
                
                    diff = {
                        "baseline_machine_id": baseline["machine_id"],
                        "compared_machine_id": machine["machine_id"],
                        "differences": {},
                    }
                    for key in baseline["status"].keys():
                        if machine["status"].get(key) != baseline["status"].get(key):
                            diff["differences"][key] = {
                                "baseline": baseline["status"].get(key),
                                "current": machine["status"].get(key),
                            }
                    if diff["differences"]:
                        differences.append(diff)

            return differences
        except Exception as e:
            logger.error(f"Error comparing operations: {e}")
            return []

