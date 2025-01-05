import json
import random
from datetime import datetime
from HardwareTester.utils.logger import Logger

logger = Logger(name="EmulatorService", log_file="logs/emulator_service.log", level="INFO")



class EmulatorService:

    # Emulator state
    emulator_state = {
        "running": False,
        "config": {
            "default_machine_name": "Machine1",
            "stress_test_mode": False,
        },
        "blueprints": [
            {"name": "Blueprint A", "description": "Test blueprint A", "created_at": str(datetime.now())},
            {"name": "Blueprint B", "description": "Test blueprint B", "created_at": str(datetime.now())},
            {"name": "Blueprint C", "description": "Test blueprint C", "created_at": str(datetime.now())},
        ],
        "active_emulations": [],
        "logs": [],
    }
    
    @staticmethod
    def fetch_blueprints():
        """Fetch available blueprints."""
        try:
            logger.info("Fetching blueprints.")
            return {"success": True, "blueprints": emulator_state["blueprints"]}
        except Exception as e:
            logger.error(f"Error fetching blueprints: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def load_blueprint(file):
        """Load a new blueprint."""
        try:
            blueprint_name = file.filename
            blueprint_data = json.load(file)
            EmulatorService.emulator_state["blueprints"].append({
                "name": blueprint_name,
                "data": blueprint_data,
                "created_at": str(datetime.now())
            })
            logger.info(f"Loaded blueprint: {blueprint_name}")
            EmulatorService.emulator_state["logs"].append(f"[{datetime.now()}] Loaded blueprint: {blueprint_name}")
            return {"success": True, "message": f"Blueprint '{blueprint_name}' loaded successfully."}
        except Exception as e:
            logger.error(f"Error loading blueprint: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def start_emulation(machine_name, blueprint, stress_test=False):
        """Start a new emulation."""
        try:
            if EmulatorService.emulator_state["running"]:
                return {"success": False, "message": "Emulator is already running an emulation."}
        
            emulation = {
                "machine_name": machine_name,
                "blueprint": blueprint,
                "stress_test": stress_test,
                "start_time": datetime.now().isoformat(),
            }
            EmulatorService.emulator_state["active_emulations"].append(emulation)
            EmulatorService.emulator_state["running"] = True
            EmulatorService.emulator_state["logs"].append(f"[{datetime.now()}] Started emulation for {machine_name} using {blueprint}")
            logger.info(f"Started emulation for {machine_name} using {blueprint}")
            return {"success": True, "message": f"Emulation started for machine '{machine_name}'."}
        except Exception as e:
            logger.error(f"Error starting emulation: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def stop_emulation(machine_name):
        """Stop an active emulation."""
        try:
            if not EmulatorService.emulator_state["running"]:
                return {"success": False, "message": "No emulation is currently running."}
        
            EmulatorService.emulator_state["active_emulations"] = [
                e for e in EmulatorService.emulator_state["active_emulations"] if e["machine_name"] != machine_name
            ]
            EmulatorService.emulator_state["running"] = len(EmulatorService.emulator_state["active_emulations"]) > 0
            EmulatorService.emulator_state["logs"].append(f"[{datetime.now()}] Stopped emulation for {machine_name}")
            logger.info(f"Stopped emulation for {machine_name}")
            return {"success": True, "message": f"Emulation stopped for machine '{machine_name}'."}
        except Exception as e:
            logger.error(f"Error stopping emulation: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_active_emulations():
        """List all active emulations."""
        try:
            logger.info("Fetching list of active emulations.")
            return {"success": True, "emulations": EmulatorService.emulator_state["active_emulations"]}
        except Exception as e:
            logger.error(f"Error fetching active emulations: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_emulator_logs():
        """Get logs for the emulator."""
        try:
            logger.info("Fetching emulator logs.")
            return {"success": True, "logs": EmulatorService.emulator_state["logs"]}
        except Exception as e:
            logger.error(f"Error fetching emulator logs: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_config(key, value):
        """Update emulator configuration."""
        try:
            if key in EmulatorService.emulator_state["config"]:
                EmulatorService.emulator_state["config"][key] = value
                EmulatorService.emulator_state["logs"].append(f"[{datetime.now()}] Config updated: {key} = {value}")
                logger.info(f"Config updated: {key} = {value}")
                return {"success": True, "message": f"Configuration '{key}' updated to '{value}'."}
            else:
                return {"success": False, "message": f"Invalid configuration key: {key}"}
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_emulator_status():
        """Get the current state of the emulator."""
        try:
            logger.info("Fetching emulator status.")
            return {
                "success": True,
                "status": {
                    "running": EmulatorService.emulator_state["running"],
                    "config": EmulatorService.emulator_state["config"],
                    "active_emulations": EmulatorService.emulator_state["active_emulations"],
                    "logs": EmulatorService.emulator_state["logs"][-10:],  # Return the last 10 logs
                }
            }
        except Exception as e:
            logger.error(f"Error fetching emulator status: {e}")
            return {"success": False, "error": str(e)}
