
from HardwareTester.extensions import db, logger
from HardwareTester.models.device_models import Peripheral
from sqlalchemy.exc import SQLAlchemyError

class PeripheralsService:
    """Service for managing peripherals."""

    @staticmethod
    def list_peripherals() -> dict:
        """List all available peripherals."""
        try:
            peripherals = Peripheral.query.all()
            result = [
                {
                    "id": p.id,
                    "name": p.name,
                    "type": p.type,
                    "properties": p.properties,
                    "device_id": p.device_id,
                }
                for p in peripherals
            ]
            logger.info(f"Fetched {len(result)} peripherals.")
            return {"success": True, "peripherals": result}
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching peripherals: {e}")
            return {"success": False, "error": "Failed to fetch peripherals."}
        except Exception as e:
            logger.error(f"Unexpected error fetching peripherals: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def add_peripheral(name: str, type: str, properties: dict, device_id: int) -> dict:
        """
        Add a new peripheral.
        :param name: Name of the peripheral.
        :param type: Type of the peripheral.
        :param properties: Properties of the peripheral.
        :param device_id: ID of the associated device.
        :return: Success or error message.
        """
        try:
            new_peripheral = Peripheral(name=name, type=type, properties=properties, device_id=device_id)
            db.session.add(new_peripheral)
            db.session.commit()
            logger.info(f"Added new peripheral: {new_peripheral}")
            return {"success": True, "message": f"Peripheral '{name}' added successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error adding peripheral '{name}': {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to add peripheral."}
        except Exception as e:
            logger.error(f"Unexpected error adding peripheral '{name}': {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def delete_peripheral(peripheral_id: int) -> dict:
        """
        Delete a peripheral by ID.
        :param peripheral_id: ID of the peripheral to delete.
        :return: Success or error message.
        """
        try:
            peripheral = Peripheral.query.get(peripheral_id)
            if not peripheral:
                logger.warning(f"Peripheral ID {peripheral_id} not found.")
                return {"success": False, "error": "Peripheral not found."}

            db.session.delete(peripheral)
            db.session.commit()
            logger.info(f"Deleted peripheral with ID: {peripheral_id}")
            return {"success": True, "message": f"Peripheral with ID {peripheral_id} deleted successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting peripheral {peripheral_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to delete peripheral."}
        except Exception as e:
            logger.error(f"Unexpected error deleting peripheral {peripheral_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}

    @staticmethod
    def update_peripheral(peripheral_id: int, properties: dict) -> dict:
        """
        Update the properties of a peripheral.
        :param peripheral_id: ID of the peripheral to update.
        :param properties: Updated properties for the peripheral.
        :return: Success or error message.
        """
        try:
            peripheral = Peripheral.query.get(peripheral_id)
            if not peripheral:
                logger.warning(f"Peripheral ID {peripheral_id} not found.")
                return {"success": False, "error": "Peripheral not found."}

            peripheral.properties.update(properties)
            db.session.commit()
            logger.info(f"Updated peripheral {peripheral_id} with properties: {properties}")
            return {"success": True, "message": f"Peripheral {peripheral_id} updated successfully."}
        except SQLAlchemyError as e:
            logger.error(f"Database error updating peripheral {peripheral_id}: {e}")
            db.session.rollback()
            return {"success": False, "error": "Failed to update peripheral."}
        except Exception as e:
            logger.error(f"Unexpected error updating peripheral {peripheral_id}: {e}")
            return {"success": False, "error": "An unexpected error occurred."}
