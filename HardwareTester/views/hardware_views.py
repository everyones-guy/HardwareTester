
from flask import Blueprint, jsonify, request
from HardwareTester.services.mqtt_service import MQTTService
from HardwareTester.extensions import db, logger
from sqlalchemy.dialects.postgresql import JSON  # Use JSON for metadata and settings storage


hardware_bp = Blueprint("hardware", __name__)
mqtt_service = MQTTService(broker="test.mosquitto.org", port=1883)
mqtt_service.connect()

@hardware_bp.route("/discover-device", methods=["POST"])
@hardware_bp.route("/discover-device", methods=["POST"])
def discover_device():
    """Discover device metadata and settings."""
    data = request.json
    device_id = data.get("device_id")

    if not device_id:
        return jsonify({"success": False, "error": "Device ID is required"}), 400

    try:
        # Fetch device response
        response = mqtt_service.send_request(
            topic=f"devices/{device_id}/discover",
            payload={"action": "discover"}
        )

        if response:
            device_data = {
                "device_id": device_id,
                "name": response.get("name", "Unknown Device"),
                "device_metadata": {
                    "firmware": response.get("firmware", "Unknown"),
                    "model": response.get("model", "Unknown"),
                    "serial_number": response.get("serial_number", "Unknown"),
                },
                "settings": response.get("settings", {}),
            }
        else:
            return jsonify({"success": False, "error": "No response from device"}), 500

        # Save or update the device in the database
        device = db.Device.query.filter_by(device_id=device_id).first()
        if not device:
            device = db.Device(
                device_id=device_id,
                name=device_data["name"],
                metadata=device_data["device_metadata"],
                settings=device_data["settings"],
            )
            db.session.add(device)
        else:
            device.metadata = device_data["device_metadata"]
            device.settings = device_data["settings"]

        db.session.commit()
        return jsonify({"success": True, "device": device_data})

    except Exception as e:
        logger.error(f"Error discovering device {device_id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500



@hardware_bp.route("/device/<string:device_id>", methods=["GET"])
def get_device(device_id):
    """Retrieve device information and settings."""
    try:
        device = db.Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({"success": False, "error": "Device not found"}), 404

        return jsonify(
            {
                "success": True,
                "device": {
                    "device_id": device.device_id,
                    "name": device.name,
                    "metadata": device.metadata,
                    "settings": device.settings,
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
