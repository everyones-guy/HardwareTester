from HardwareTester.utils.api_manager import create_api_manager
from HardwareTester.utils.logger import Logger
from flask_socketio import emit
from HardwareTester.extensions import socketio


# Initialize Logger
logger = Logger(name="ValveService", log_file="logs/valve_service.log", level="INFO")

# Initialize APIManager
api_manager = create_api_manager("https://example.com/api")

def list_valves():
    """Fetch and return all valves."""
    logger.info("Fetching list of valves...")
    response = api_manager.get("valves")
    if "error" in response:
        logger.error(f"Failed to fetch valves: {response['error']}")
        return {"success": False, "error": response["error"]}
    logger.info(f"Retrieved {len(response.get('valves', []))} valves.")
    return {"success": True, "valves": response.get("valves", [])}

def add_valve(name, valve_type, api_endpoint=None):
    """Add a new valve."""
    logger.info(f"Adding a new valve: {name}, Type: {valve_type}")
    payload = {"name": name, "type": valve_type, "api_endpoint": api_endpoint}
    response = api_manager.post("valves", payload=payload)
    if "error" in response:
        logger.error(f"Failed to add valve: {response['error']}")
        return {"success": False, "error": response["error"]}
    logger.info(f"Valve added successfully: {response}")
    return {"success": True, "valve": response}

def delete_valve(valve_id):
    """Delete a valve."""
    logger.info(f"Deleting valve ID {valve_id}...")
    response = api_manager.delete(f"valves/{valve_id}")
    if "error" in response:
        logger.error(f"Failed to delete valve {valve_id}: {response['error']}")
        return {"success": False, "error": response["error"]}
    logger.info(f"Valve deleted successfully.")
    return {"success": True}

def update_valve_state(valve_id, state, value=None):
    """
    Update the valve state and emit the changes.
    """
    # Emit real-time updates
    emit("valve_update", {"id": valve_id, "state": state, "value": value}, broadcast=True)
