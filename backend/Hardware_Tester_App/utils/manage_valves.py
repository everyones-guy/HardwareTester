from Hardware_Tester_App.utils.api_manager import get_api_manager
from Hardware_Tester_App.utils.custom_logger import CustomLogger

import os
from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()

# Initialize Logger
logger = CustomLogger.get_logger("ValveManager")

# Initialize APIManager
api_manager = get_api_manager()

def list_valves():
    """Fetch and display all valves."""
    logger.info("Fetching list of valves...")
    response = api_manager.get("valves")
    if "error" in response:
        logger.error(f"Failed to fetch valves: {response['error']}")
        return
    valves = response.get("valves", [])
    logger.info(f"Retrieved {len(valves)} valves.")
    for valve in valves:
        print(f"ID: {valve['id']}, Name: {valve['name']}, Type: {valve['type']}")

def add_valve(name, valve_type, api_endpoint=None):
    """Add a new valve."""
    logger.info(f"Adding a new valve: {name}, Type: {valve_type}")
    payload = {"name": name, "type": valve_type, "api_endpoint": api_endpoint}
    response = api_manager.post("valves", payload=payload)
    if "error" in response:
        logger.error(f"Failed to add valve: {response['error']}")
        return
    logger.info(f"Valve added successfully: {response}")
    print(f"Added Valve: {response}")

def update_valve(valve_id, name=None, valve_type=None, api_endpoint=None):
    """Update an existing valve."""
    logger.info(f"Updating valve ID {valve_id}...")
    payload = {key: value for key, value in [("name", name), ("type", valve_type), ("api_endpoint", api_endpoint)] if value}
    response = api_manager.put(f"valves/{valve_id}", payload=payload)
    if "error" in response:
        logger.error(f"Failed to update valve {valve_id}: {response['error']}")
        return
    logger.info(f"Valve updated successfully: {response}")
    print(f"Updated Valve: {response}")

def delete_valve(valve_id):
    """Delete a valve."""
    logger.info(f"Deleting valve ID {valve_id}...")
    response = api_manager.delete(f"valves/{valve_id}")
    if "error" in response:
        logger.error(f"Failed to delete valve {valve_id}: {response['error']}")
        return
    logger.info(f"Valve deleted successfully: {response}")
    print(f"Deleted Valve ID {valve_id}")

if __name__ == "__main__":
    list_valves()
    add_valve("Valve A", "Type 1", "/valves/1")
    update_valve(1, name="Updated Valve A")
    delete_valve(1)
