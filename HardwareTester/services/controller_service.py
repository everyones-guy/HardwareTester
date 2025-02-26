from HardwareTester.extensions import db
from HardwareTester.models.device_models import Controller
from HardwareTester.utils.custom_logger import CustomLogger


logger = CustomLogger.get_logger("ControllerService")

def get_all_controllers():
    """Retrieve all controllers from the database."""
    try:
        controllers = Controller.query.all()
        controller_list = [
            {
                "id": controller.id,
                "name": controller.name,
                "type": controller.type,
                "specifications": controller.specifications,
                "state": controller.state,
            }
            for controller in controllers
        ]
        return {"success": True, "controllers": controller_list}
    except Exception as e:
        logger.error(f"Error retrieving controllers: {e}")
        return {"success": False, "error": str(e)}


def add_controller(data):
    """Add a new Controller to the database."""
    try:
        controller = Controller(
            name=data.get("name"),
            type=data.get("type"),
            specifications=data.get("specifications"),
            state=data.get("state", "closed"),  # Default state is "closed"
        )
        db.session.add(controller)
        db.session.commit()
        logger.info(f"Added Controller: {controller.name}")
        return {"success": True, "message": "Controller added successfully"}
    except Exception as e:
        logger.error(f"Error adding controller: {e}")
        return {"success": False, "error": str(e)}


def delete_controller(controller_id):
    """Delete a controller from the database."""
    try:
        controller = Controller.query.get(controller_id)
        if not controller:
            return {"success": False, "error": "Controller not found"}
        db.session.delete(controller)
        db.session.commit()
        logger.info(f"Deleted controller: {controller.name}")
        return {"success": True, "message": "Controller deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting controller: {e}")
        return {"success": False, "error": str(e)}


def update_controller(controller_id, data):
    """Update Controller details."""
    try:
        controller = Controller.query.get(controller_id)
        if not controller:
            return {"success": False, "error": "Controller not found"}
        controller.name = data.get("name", controller.name)
        controller.type = data.get("type", controller.type)
        controller.specifications = data.get("specifications", controller.specifications)
        controller.state = data.get("state", controller.state)
        db.session.commit()
        logger.info(f"Updated Controller: {controller.name}")
        return {"success": True, "message": "Controller updated successfully"}
    except Exception as e:
        logger.error(f"Error updating Controller: {e}")
        return {"success": False, "error": str(e)}


def get_controller_status(controller_id):
    """Get the status of a specific controller."""
    try:
        controller = Controller.query.get(controller_id)
        if not controller:
            return {"success": False, "error": "Controller not found"}
        status = {"id": controller.id, "status": controller.state}  # Use dynamic state
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Error retrieving Controller status: {e}")
        return {"success": False, "error": str(e)}


def change_controller_state(controller_id, new_state):
    """Change the state of a controller."""
    try:
        controller = Controller.query.get(controller_id)
        if not controller:
            return {"success": False, "error": "Controller not found"}
        if new_state not in ["open", "closed", "faulty", "maintenance"]:
            return {"success": False, "error": "Invalid state specified"}
        controller.state = new_state
        db.session.commit()
        logger.info(f"Controller {controller.name} state changed to {new_state}")
        return {"success": True, "message": f"Controller state updated to {new_state}"}
    except Exception as e:
        logger.error(f"Error changing Controller state: {e}")
        return {"success": False, "error": str(e)}
