
import json
from flask import current_app
from HardwareTester.extensions import db
from HardwareTester.models.link_models import Link
from sqlalchemy.exc import SQLAlchemyError

from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.models.device_models import Device, DeviceFirmwareHistory, Firmware, Peripheral, Controller
import hashlib

# Initialize logger
logger = CustomLogger.get_logger("hardware_service", per_module=True)

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
        
    @staticmethod
    def save_link(source_id: int, target_id: int, metadata: dict = None) -> dict:
        """
        Save a link between two devices in the database.

        :param source_id: ID of the source device.
        :param target_id: ID of the target device.
        :param device_metadata: Optional metadata for the link (e.g., connection details).
        :return: A dictionary indicating success or failure.
        """
        try:
            # Create the link object
            new_link = Link(source_id=source_id, target_id=target_id, device_metadata=metadata or {})
        
            # Add and commit to the database
            db.session.add(new_link)
            db.session.commit()

            logger.info(f"Link created between source {source_id} and target {target_id} with metadata {metadata}.")
            return {"success": True, "message": "Link saved successfully.", "link_id": new_link.id}
        except SQLAlchemyError as e:
            logger.error(f"Database error while saving link: {e}")
            db.session.rollback()
            return {"success": False, "error": "Database error occurred while saving the link."}
        except Exception as e:
            logger.error(f"Unexpected error while saving link: {e}")
            return {"success": False, "error": "An unexpected error occurred while saving the link."}

    @staticmethod
    def get_links() -> list:
        """
        Fetch all saved links from the database.
        :return: List of links.
        """
        try:
            links = Link.query.all()
            return [{"id": link.id, "source_id": link.source_id, "target_id": link.target_id, "metadata": link.metadata} for link in links]
        except Exception as e:
            logger.error(f"Error fetching links: {e}")
            return []

    @staticmethod
    def get_device_from_db(device_id):
        """
        Fetch a hardware device from the database by its device_id, including firmware history, controllers, and peripherals.
        :param device_id: The unique identifier of the hardware device.
        :return: JSON response with device details.
        """
        try:
            # Fetch the device from the database
            device = db.session.query(Device).filter_by(device_id=device_id).first()

            if not device:
                logger.warning(f"Device with ID {device_id} not found.")
                return {"success": False, "error": "Device not found."}, 404

            # Fetch firmware history
            firmware_history = db.session.query(DeviceFirmwareHistory).filter_by(device_id=device.id).all()
            firmware_data = [
                {
                    "firmware_id": fh.firmware.id,
                    "hash": fh.firmware.hash,
                    "version": fh.firmware.mdf.get("version") if fh.firmware.mdf else "Unknown",
                    "uploaded_at": fh.uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "uploaded_by": fh.uploaded_by
                } for fh in firmware_history
            ]

            # Fetch associated controllers
            controllers = [
                {
                    "id": ctrl.id,
                    "name": ctrl.name,
                    "firmware_version": ctrl.firmware_version,
                    "available": ctrl.available
                } for ctrl in device.controllers
            ]

            # Fetch associated peripherals
            peripherals = [
                {
                    "id": p.id,
                    "name": p.name,
                    "type": p.type,
                    "properties": p.properties
                } for p in device.peripherals
            ]

            # Construct the device response
            device_data = {
                "id": device.id,
                "device_id": device.device_id,
                "name": device.name,
                "firmware_version": device.firmware_version,
                "device_metadata": device.device_metadata,
                "created_at": device.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": device.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "created_by": device.created_by,
                "modified_by": device.modified_by,
                "firmware_history": firmware_data,
                "controllers": controllers,
                "peripherals": peripherals
            }

            logger.info(f"Fetched device {device_id} from database with full history.")
            return {"success": True, "data": device_data}, 200

        except Exception as e:
            logger.error(f"Error fetching device {device_id}: {e}")
            return {"success": False, "error": str(e)}, 500