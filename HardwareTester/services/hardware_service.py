
#                                                              #
#
#                   Hardware Service                           #
#                      
#                                                              #


import json
from flask import current_app
from HardwareTester.extensions import db, logger
from HardwareTester.models.device_models import Device

class HardwareService:
    """Service for managing hardware-related operations."""

    @staticmethod
    def discover_device(device_id):
        """
        Discover a specific device by its ID.
        :param device_id: Unique identifier for the device.
        :return: Dictionary with device information or error message.
        """
        try:
            logger.info(f"Discovering device with ID: {device_id}")
            device = Device.query.filter_by(id=device_id).first()
            if not device:
                logger.warning(f"Device with ID {device_id} not found.")
                return {"success": False, "error": "Device not found."}

            device_info = {
                "id": device.id,
                "name": device.name,
                "model": device.model,
                "status": device.status,
                "metadata": json.loads(device.metadata) if device.metadata else {},
            }
            logger.info(f"Device discovered: {device_info}")
            return {"success": True, "device": device_info}

        except Exception as e:
            logger.error(f"Error discovering device: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_device_status(device_id, status):
        """
        Update the status of a specific device.
        :param device_id: Unique identifier for the device.
        :param status: New status to set for the device.
        :return: Dictionary indicating success or failure.
        """
        try:
            logger.info(f"Updating status for device ID {device_id} to '{status}'.")
            device = Device.query.filter_by(id=device_id).first()
            if not device:
                logger.warning(f"Device with ID {device_id} not found.")
                return {"success": False, "error": "Device not found."}

            device.status = status
            db.session.commit()
            logger.info(f"Device status updated successfully for ID {device_id}.")
            return {"success": True, "message": "Device status updated successfully."}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating device status: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_devices():
        """
        List all devices in the database.
        :return: List of devices or error message.
        """
        try:
            devices = Device.query.all()
            device_list = [
                {
                    "id": device.id,
                    "name": device.name,
                    "model": device.model,
                    "status": device.status,
                    "metadata": json.loads(device.metadata) if device.metadata else {},
                }
                for device in devices
            ]
            logger.info(f"Retrieved {len(device_list)} devices.")
            return {"success": True, "devices": device_list}

        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_device(device_id):
        """
        Delete a specific device by ID.
        :param device_id: Unique identifier for the device.
        :return: Dictionary indicating success or failure.
        """
        try:
            logger.info(f"Deleting device with ID {device_id}.")
            device = Device.query.filter_by(id=device_id).first()
            if not device:
                logger.warning(f"Device with ID {device_id} not found.")
                return {"success": False, "error": "Device not found."}

            db.session.delete(device)
            db.session.commit()
            logger.info(f"Device with ID {device_id} deleted successfully.")
            return {"success": True, "message": "Device deleted successfully."}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting device: {e}")
            return {"success": False, "error": str(e)}
