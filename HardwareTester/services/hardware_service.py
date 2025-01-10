
#                                                              #
#
#                   Hardware Service                           #
#                      
#                                                              #


import json
from flask import current_app
from HardwareTester.extensions import db, logger
from HardwareTester.models.device_models import Device
from HardwareTester.models.device_models import DeviceFirmwareHistory
import hashlib

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

    @staticmethod
    def upload_firmware_to_device(device_id, firmware_data):
        """
        Upload text-based firmware to a specific device.
        :param device_id: ID of the target device.
        :param firmware_data: Text content of the firmware.
        :return: Result of the upload operation.
        """
        try:
            logger.info(f"Uploading firmware to device {device_id}...")
            device = Device.query.filter_by(id=device_id).first()
            if not device:
                logger.warning(f"Device with ID {device_id} not found.")
                return {"success": False, "error": "Device not found."}

            # Assuming the firmware is stored in device_metadata or similar
            device.device_metadata["firmware_text"] = firmware_data
            db.session.commit()
            logger.info(f"Firmware uploaded successfully to device {device_id}.")
            return {"success": True}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading firmware to device {device_id}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def store_firmware(firmware_hash, firmware_data):
        """
        Store firmware in the database if it doesn't already exist.
        :param firmware_hash: SHA-256 hash of the firmware.
        :param firmware_data: Content of the firmware.
        :return: Result of the operation.
        """
        try:
            from HardwareTester.models.device_models import Firmware  # Ensure a Firmware model exists
            existing_firmware = Firmware.query.filter_by(hash=firmware_hash).first()
            if existing_firmware:
                logger.info(f"Firmware with hash {firmware_hash} already exists in the database.")
                return {"success": True, "existing": True, "firmware_id": existing_firmware.id}

            new_firmware = Firmware(hash=firmware_hash, content=firmware_data)
            db.session.add(new_firmware)
            db.session.commit()
            logger.info(f"Firmware stored with ID {new_firmware.id}.")
            return {"success": True, "existing": False, "firmware_id": new_firmware.id}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error storing firmware: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def track_firmware_version(device_id, firmware_id):
        """
        Track the firmware version uploaded to a device.
        :param device_id: Device ID.
        :param firmware_id: Firmware ID.
        :return: Result of the operation.
        """
        try:
            history = DeviceFirmwareHistory(device_id=device_id, firmware_id=firmware_id)
            db.session.add(history)
            db.session.commit()
            logger.info(f"Tracked firmware ID {firmware_id} for device ID {device_id}.")
            return {"success": True}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error tracking firmware version: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def generate_mdf(firmware_data):
        """
        Generate a Master Data File (MDF) for quick comparisons.
        :param firmware_data: Firmware content.
        :return: MDF metadata.
        """
        metadata = {
            "length": len(firmware_data),
            "lines": firmware_data.count("\n"),
            "checksum": hashlib.md5(firmware_data.encode()).hexdigest(),
        }
        logger.info(f"Generated MDF: {metadata}")
        return metadata
    
    @staticmethod
    def get_device_status(device_id=None):
        """
        Get the status of a specific device or all devices.
        :param device_id: (Optional) The ID of the device to get the status for.
        :return: Dictionary containing device status or an error message.
        """
        try:
            if device_id:
                # Fetch a single device's status
                device = Device.query.filter_by(id=device_id).first()
                if not device:
                    return {"success": False, "error": f"Device with ID {device_id} not found."}

                return {
                    "success": True,
                    "status": {
                        "id": device.id,
                        "name": device.name,
                        "firmware_version": device.firmware_version,
                        "metadata": device.device_metadata,
                    }
                }
            else:
                # Fetch status for all devices
                devices = Device.query.all()
                device_status_list = [
                    {
                        "id": device.id,
                        "name": device.name,
                        "firmware_version": device.firmware_version,
                        "metadata": device.device_metadata,
                    }
                    for device in devices
                ]
                return {"success": True, "status": device_status_list}

        except Exception as e:
            logger.error(f"Error fetching device status: {e}")
            return {"success": False, "error": str(e)}
