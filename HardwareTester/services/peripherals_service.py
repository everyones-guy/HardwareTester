
from HardwareTester.utils.logger import Logger

logger = Logger(name="PeripheralsService", log_file="logs/peripherals_service.log", level="INFO")

# Mocked database for peripherals
PERIPHERALS_DB = []

class PeripheralsService:
    """Service for managing peripherals."""

    @staticmethod
    def list_peripherals():
        """List all available peripherals."""
        try:
            logger.info(f"Listing {len(PERIPHERALS_DB)} peripherals.")
            return {"success": True, "peripherals": PERIPHERALS_DB}
        except Exception as e:
            logger.error(f"Error listing peripherals: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def add_peripheral(name, properties):
        """Add a new peripheral."""
        try:
            peripheral = {"id": len(PERIPHERALS_DB) + 1, "name": name, "properties": properties}
            PERIPHERALS_DB.append(peripheral)
            logger.info(f"Added new peripheral: {peripheral}")
            return {"success": True, "message": f"Peripheral '{name}' added successfully."}
        except Exception as e:
            logger.error(f"Error adding peripheral: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_peripheral(peripheral_id):
        """Delete a peripheral by ID."""
        try:
            global PERIPHERALS_DB
            PERIPHERALS_DB = [p for p in PERIPHERALS_DB if p["id"] != peripheral_id]
            logger.info(f"Deleted peripheral with ID: {peripheral_id}")
            return {"success": True, "message": f"Peripheral with ID {peripheral_id} deleted successfully."}
        except Exception as e:
            logger.error(f"Error deleting peripheral: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_peripheral(peripheral_id, properties):
        """Update the properties of a peripheral."""
        try:
            for peripheral in PERIPHERALS_DB:
                if peripheral["id"] == peripheral_id:
                    peripheral["properties"].update(properties)
                    logger.info(f"Updated peripheral {peripheral_id} with properties: {properties}")
                    return {"success": True, "message": f"Peripheral {peripheral_id} updated successfully."}
            return {"success": False, "error": "Peripheral not found."}
        except Exception as e:
            logger.error(f"Error updating peripheral: {e}")
            return {"success": False, "error": str(e)}

