
import json
import random
from datetime import datetime
from HardwareTester.utils.logger import Logger

logger = Logger(name="EmulatorService", log_file="logs/emulator_service.log", level="INFO")

# Mock data
blueprints = [
    {"name": "Blueprint A", "description": "Test blueprint A", "created_at": str(datetime.now())},
    {"name": "Blueprint B", "description": "Test blueprint B", "created_at": str(datetime.now())},
    {"name": "Blueprint C", "description": "Test blueprint C", "created_at": str(datetime.now())},
]
active_emulations = []
emulator_logs = []


def fetch_blueprints():
    """Fetch available blueprints."""
    try:
        logger.info("Fetching blueprints.")
        return {"success": True, "blueprints": blueprints}
    except Exception as e:
        logger.error(f"Error fetching blueprints: {e}")
        return {"success": False, "error": str(e)}


def load_blueprint(file):
    """Load a new blueprint."""
    try:
        blueprint_name = file.filename
        blueprint_data = json.load(file)
        blueprints.append({"name": blueprint_name, "data": blueprint_data, "created_at": str(datetime.now())})
        logger.info(f"Loaded blueprint: {blueprint_name}")
        emulator_logs.append(f"[{datetime.now()}] Loaded blueprint: {blueprint_name}")
        return {"success": True, "message": f"Blueprint '{blueprint_name}' loaded successfully."}
    except Exception as e:
        logger.error(f"Error loading blueprint: {e}")
        return {"success": False, "error": str(e)}


def start_emulation(machine_name, blueprint, stress_test=False):
    """Start a new emulation."""
    try:
        emulation = {
            "machine_name": machine_name,
            "blueprint": blueprint,
            "stress_test": stress_test,
            "start_time": datetime.now().isoformat(),
        }
        active_emulations.append(emulation)
        emulator_logs.append(f"[{datetime.now()}] Started emulation for {machine_name} using {blueprint}")
        logger.info(f"Started emulation for {machine_name} using {blueprint}")
        return {"success": True, "message": f"Emulation started for machine '{machine_name}'."}
    except Exception as e:
        logger.error(f"Error starting emulation: {e}")
        return {"success": False, "error": str(e)}


def stop_emulation(machine_name):
    """Stop an active emulation."""
    try:
        global active_emulations
        active_emulations = [e for e in active_emulations if e["machine_name"] != machine_name]
        emulator_logs.append(f"[{datetime.now()}] Stopped emulation for {machine_name}")
        logger.info(f"Stopped emulation for {machine_name}")
        return {"success": True, "message": f"Emulation stopped for machine '{machine_name}'."}
    except Exception as e:
        logger.error(f"Error stopping emulation: {e}")
        return {"success": False, "error": str(e)}


def list_active_emulations():
    """List all active emulations."""
    try:
        logger.info("Fetching list of active emulations.")
        return {"success": True, "emulations": active_emulations}
    except Exception as e:
        logger.error(f"Error fetching active emulations: {e}")
        return {"success": False, "error": str(e)}


def get_emulator_logs():
    """Get logs for the emulator."""
    try:
        logger.info("Fetching emulator logs.")
        return {"success": True, "logs": emulator_logs}
    except Exception as e:
        logger.error(f"Error fetching emulator logs: {e}")
        return {"success": False, "error": str(e)}



