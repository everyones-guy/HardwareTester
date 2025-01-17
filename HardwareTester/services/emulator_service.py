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

    @staticmethod
    def fetch_blueprints() -> Dict[str, Union[bool, Any]]:
        """Fetch available blueprints."""
        try:
            blueprints = Blueprint.query.all()
            blueprint_list = [{"name": b.name, "description": b.description, "created_at": b.created_at} for b in blueprints]
            logger.info("Fetching blueprints.")
            return {"success": True, "blueprints": blueprint_list}
        except Exception as e:
            logger.error(f"Error fetching blueprints: {e}")
            return {"success": False, "error": "Failed to fetch blueprints."}

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

    @staticmethod
    def list_active_emulations() -> Dict[str, Union[bool, Any]]:
        """List all active emulations."""
        try:
            logger.info("Fetching list of active emulations.")
            return {"success": True, "emulations": EmulatorService.emulator_state["active_emulations"]}
        except Exception as e:
            logger.error(f"Error fetching active emulations: {e}")
            return {"success": False, "error": "Failed to fetch active emulations."}
    
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

    @staticmethod
    def load_blueprint(blueprint_name: str) -> Dict[str, Union[bool, Any]]:
        """Load a specific blueprint by name."""
        try:
            # Query the Blueprint model for the blueprint with the given name
            blueprint = Blueprint.query.filter_by(name=blueprint_name).first()
            if not blueprint:
                logger.warning(f"Blueprint '{blueprint_name}' not found.")
                return {"success": False, "message": f"Blueprint '{blueprint_name}' not found."}

            # Return blueprint details
            blueprint_details = {
                "name": blueprint.name,
                "description": blueprint.description,
                "created_at": blueprint.created_at.isoformat(),
                "configuration": blueprint.configuration,  # Assuming 'configuration' is a field in your Blueprint model
            }
            logger.info(f"Loaded blueprint '{blueprint_name}'.")
            return {"success": True, "blueprint": blueprint_details}
        except Exception as e:
            logger.error(f"Error loading blueprint '{blueprint_name}': {e}")
            return {"success": False, "error": "Failed to load blueprint."}

    @staticmethod
    def add_blueprint(name: str, description: str) -> Dict[str, Union[bool, str]]:
        """
        Add a new blueprint to the database.
        
        :param name: The name of the blueprint.
        :param description: A description of the blueprint.
        :return: A dictionary indicating success or failure with a message.
        """
        try:
            # Check if blueprint with the same name already exists
            existing_blueprint = Blueprint.query.filter_by(name=name).first()
            if existing_blueprint:
                return {"success": False, "message": f"Blueprint with name '{name}' already exists."}
            
            # Create and add the new blueprint
            new_blueprint = Blueprint(name=name, description=description)
            db.session.add(new_blueprint)
            db.session.commit()
            
            logger.info(f"Blueprint '{name}' added successfully.")
            return {"success": True, "message": f"Blueprint '{name}' added successfully."}
        except Exception as e:
            logger.error(f"Error adding blueprint '{name}': {e}")
            db.session.rollback()
            return {"success": False, "message": f"Failed to add blueprint '{name}': {str(e)}"}


