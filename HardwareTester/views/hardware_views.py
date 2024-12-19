from flask import Blueprint, jsonify, request
from HardwareTester.services.mqtt_service import MQTTService
from HardwareTester.models import Device, db

hardware_bp = Blueprint("hardware", __name__)
mqtt_service = MQTTService(broker="test.mosquitto.org", port=1883)
mqtt_service.connect()

@hardware_bp.route("/discover-device", methods=["POST"])
def discover_device():
    """Discover device metadata and settings."""
    data = request.json
    device_id = data.get("device_id")

    if not device_id:
        return jsonify({"success": False, "error": "Device ID is required"}), 400

    mqtt_service.discover_device(device_id)

    # Simulate fetching device response (replace with actual MQTT response handling)
    device_data = {
        "device_id": device_id,
        "name": "EcoLab Hero",
        "metadata": {"firmware": "1.2.3", "model": "Hero", "serial_number": "123456"},
        "settings": {
            "menu": [
                {"name": "Network", "options": ["WiFi", "Ethernet"]},
                {"name": "Sensors", "options": ["Temperature", "Flow Rate"]},
            ]
        },
    }

    # Save to database
    device = Device.query.filter_by(device_id=device_id).first()
    if not device:
        device = Device(
            device_id=device_id,
            name=device_data["name"],
            metadata=device_data["metadata"],
            settings=device_data["settings"],
        )
        db.session.add(device)
    else:
        device.metadata = device_data["metadata"]
        device.settings = device_data["settings"]
    db.session.commit()

    return jsonify({"success": True, "device": device_data})


@hardware_bp.route("/device/<string:device_id>", methods=["GET"])
def get_device(device_id):
    """Retrieve device information and settings."""
    device = Device.query.filter_by(device_id=device_id).first()
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
