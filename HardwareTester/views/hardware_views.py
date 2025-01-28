from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from HardwareTester.services.mqtt_service import MQTTService
from HardwareTester.services.ssh_service import SSHService  # Hypothetical SSH service
from HardwareTester.extensions import db
from sqlalchemy.dialects.postgresql import JSON  # For metadata and settings storage
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("hardware_views")

hardware_bp = Blueprint("hardware", __name__, url_prefix="/hardware")
mqtt_service = MQTTService(broker="test.mosquitto.org", port=1883)
mqtt_service.connect()


@hardware_bp.route("/", methods=["GET"])
@login_required
def hardware_dashboard():
    """Render the hardware dashboard."""
    try:
        return render_template("hardware.html")
    except Exception as e:
        logger.error(f"Error rendering hardware dashboard: {e}")
        return jsonify({"success": False, "error": "Failed to render the hardware dashboard."}), 500


@hardware_bp.route("/list", methods=["GET"])
@login_required
def list_devices():
    """List all registered devices."""
    try:
        devices = db.Device.query.all()
        device_list = [
            {
                "device_id": device.device_id,
                "name": device.name,
                "status": device.metadata.get("status", "Unknown"),
                "type": device.metadata.get("type", "Unknown"),
            }
            for device in devices
        ]
        return jsonify({"success": True, "devices": device_list})
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hardware_bp.route("/discover-device", methods=["POST"])
@login_required  
def discover_device():
    """Discover device metadata and settings."""
    data = request.json
    device_id = data.get("device_id")

    if not device_id:
        return jsonify({"success": False, "error": "Device ID is required"}), 400

    try:
        # Fetch device metadata via MQTT
        response = mqtt_service.send_request(
            topic=f"devices/{device_id}/discover",
            payload={"action": "discover"}
        )

        if response:
            device_data = {
                "device_id": device_id,
                "name": response.get("name", "Unknown Device"),
                "metadata": {
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
                metadata=device_data["metadata"],
                settings=device_data["settings"],
            )
            db.session.add(device)
        else:
            device.metadata = device_data["metadata"]
            device.settings = device_data["settings"]

        db.session.commit()
        return jsonify({"success": True, "device": device_data})

    except Exception as e:
        logger.error(f"Error discovering device {device_id}: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@hardware_bp.route("/device/<string:device_id>", methods=["GET"])
@login_required
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
        logger.error(f"Error retrieving device {device_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hardware_bp.route("/device/<string:device_id>/test-firmware", methods=["POST"])
@login_required
def test_firmware(device_id):
    """Test the firmware on a specified device."""
    try:
        device = db.Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({"success": False, "error": "Device not found"}), 404

        # Mocked firmware testing process
        firmware_results = {
            "status": "success",
            "logs": "Firmware test logs: all systems operational.",
        }

        return jsonify({"success": True, "results": firmware_results})
    except Exception as e:
        logger.error(f"Error testing firmware on device {device_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hardware_bp.route("/device/<string:device_id>/ssh-connect", methods=["POST"])
@login_required
def ssh_connect(device_id):
    """Establish an SSH connection to a device."""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not all([username, password]):
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    try:
        ssh_service = SSHService(device_id=device_id)
        ssh_connected = ssh_service.connect(username=username, password=password)

        if ssh_connected:
            return jsonify({"success": True, "message": "SSH connection established"})
        else:
            return jsonify({"success": False, "error": "Failed to establish SSH connection"}), 500
    except Exception as e:
        logger.error(f"Error connecting to device {device_id} via SSH: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@hardware_bp.route("/device/<string:device_id>/execute-command", methods=["POST"])
@login_required
def execute_command(device_id):
    """Execute a command on a device via SSH."""
    data = request.json
    command = data.get("command")

    if not command:
        return jsonify({"success": False, "error": "Command is required"}), 400

    try:
        ssh_service = SSHService(device_id=device_id)
        command_output = ssh_service.execute_command(command)

        return jsonify({"success": True, "output": command_output})
    except Exception as e:
        logger.error(f"Error executing command on device {device_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
