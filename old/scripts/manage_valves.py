from Hardware_Tester_App.utils.api_manager import get_api_manager
from Hardware_Tester_App.utils.custom_logger import Logger

# Initialize Logger
logger = Logger(name="ControllerManager", log_file="logs/controller_manager.log", level="INFO")

# Initialize APIManager
api_manager = get_api_manager("https://example.com/api")

def list_controllers():
    """Fetch and display all controllers."""
    logger.info("Fetching list of controllers...")
    response = api_manager.get("controllers")
    if "error" in response:
        logger.error(f"Failed to fetch controllers: {response['error']}")
        return
    controllers = response.get("controllers", [])
    logger.info(f"Retrieved {len(controllers)} controllers.")
    for controller in controllers:
        print(f"ID: {controller['id']}, Name: {controller['name']}, Type: {controller['type']}")

def add_controller(name, controller_type, api_endpoint=None):
    """Add a new controller."""
    logger.info(f"Adding a new controller: {name}, Type: {controller_type}")
    payload = {"name": name, "type": controller_type, "api_endpoint": api_endpoint}
    response = api_manager.post("controllers", payload=payload)
    if "error" in response:
        logger.error(f"Failed to add controller: {response['error']}")
        return
    logger.info(f"Controller added successfully: {response}")
    print(f"Added Controller: {response}")

def update_controller(controller_id, name=None, controller_type=None, api_endpoint=None):
    """Update an existing controller."""
    logger.info(f"Updating controller ID {controller_id}...")
    payload = {key: value for key, value in [("name", name), ("type", controller_type), ("api_endpoint", api_endpoint)] if value}
    response = api_manager.put(f"controllers/{controller_id}", payload=payload)
    if "error" in response:
        logger.error(f"Failed to update controller {controller_id}: {response['error']}")
        return
    logger.info(f"controller updated successfully: {response}")
    print(f"Updated controller: {response}")

def delete_controller(controller_id):
    """Delete a controller."""
    logger.info(f"Deleting controller ID {controller_id}...")
    response = api_manager.delete(f"controllers/{controller_id}")
    if "error" in response:
        logger.error(f"Failed to delete controller {controller_id}: {response['error']}")
        return
    logger.info(f"controller deleted successfully: {response}")
    print(f"Deleted Controller ID {controller_id}")

if __name__ == "__main__":
    list_controllers()
    add_controller("Controller A", "Type 1", "/controllers/1")
    update_controller(1, name="Updated Controller A")
    delete_controller(1)
