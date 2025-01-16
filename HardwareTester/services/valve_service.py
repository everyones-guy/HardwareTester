from HardwareTester.extensions import db
from HardwareTester.models.device_models import Valve
from HardwareTester.utils.custom_logger import CustomLogger


logger = CustomLogger.get_logger("ValveService")

def get_all_valves():
    """Retrieve all valves from the database."""
    try:
        valves = Valve.query.all()
        valve_list = [
            {
                "id": valve.id,
                "name": valve.name,
                "type": valve.type,
                "specifications": valve.specifications,
                "state": valve.state,
            }
            for valve in valves
        ]
        return {"success": True, "valves": valve_list}
    except Exception as e:
        logger.error(f"Error retrieving valves: {e}")
        return {"success": False, "error": str(e)}


def add_valve(data):
    """Add a new valve to the database."""
    try:
        valve = Valve(
            name=data.get("name"),
            type=data.get("type"),
            specifications=data.get("specifications"),
            state=data.get("state", "closed"),  # Default state is "closed"
        )
        db.session.add(valve)
        db.session.commit()
        logger.info(f"Added valve: {valve.name}")
        return {"success": True, "message": "Valve added successfully"}
    except Exception as e:
        logger.error(f"Error adding valve: {e}")
        return {"success": False, "error": str(e)}


def delete_valve(valve_id):
    """Delete a valve from the database."""
    try:
        valve = Valve.query.get(valve_id)
        if not valve:
            return {"success": False, "error": "Valve not found"}
        db.session.delete(valve)
        db.session.commit()
        logger.info(f"Deleted valve: {valve.name}")
        return {"success": True, "message": "Valve deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting valve: {e}")
        return {"success": False, "error": str(e)}


def update_valve(valve_id, data):
    """Update valve details."""
    try:
        valve = Valve.query.get(valve_id)
        if not valve:
            return {"success": False, "error": "Valve not found"}
        valve.name = data.get("name", valve.name)
        valve.type = data.get("type", valve.type)
        valve.specifications = data.get("specifications", valve.specifications)
        valve.state = data.get("state", valve.state)
        db.session.commit()
        logger.info(f"Updated valve: {valve.name}")
        return {"success": True, "message": "Valve updated successfully"}
    except Exception as e:
        logger.error(f"Error updating valve: {e}")
        return {"success": False, "error": str(e)}


def get_valve_status(valve_id):
    """Get the status of a specific valve."""
    try:
        valve = Valve.query.get(valve_id)
        if not valve:
            return {"success": False, "error": "Valve not found"}
        status = {"id": valve.id, "status": valve.state}  # Use dynamic state
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Error retrieving valve status: {e}")
        return {"success": False, "error": str(e)}


def change_valve_state(valve_id, new_state):
    """Change the state of a valve."""
    try:
        valve = Valve.query.get(valve_id)
        if not valve:
            return {"success": False, "error": "Valve not found"}
        if new_state not in ["open", "closed", "faulty", "maintenance"]:
            return {"success": False, "error": "Invalid state specified"}
        valve.state = new_state
        db.session.commit()
        logger.info(f"Valve {valve.name} state changed to {new_state}")
        return {"success": True, "message": f"Valve state updated to {new_state}"}
    except Exception as e:
        logger.error(f"Error changing valve state: {e}")
        return {"success": False, "error": str(e)}
