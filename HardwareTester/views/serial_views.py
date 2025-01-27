from flask import Blueprint, jsonify, request
from flask_login import login_required
from HardwareTester.extensions import logger
from HardwareTester.services.serial_service import SerialService
from HardwareTester.views.auth_views import login

serial_bp = Blueprint("serial", __name__, url_prefix="/serial")

# Global instance of the SerialService
serial_service = None

logger.info("Serial views loaded.")

@serial_bp.route("/connect", methods=["POST"])
@login_required
def connect():
    """Connect to a serial device."""
    global serial_service
    data = request.json
    port = data.get("port")
    baudrate = data.get("baudrate", 9600)

    if not port:
        return jsonify({"success": False, "error": "Port is required"}), 400

    try:
        # Initialize and connect the serial service
        serial_service = SerialService(port, baudrate)
        logger.info(f"Connecting to {port} at {baudrate} baud.")
        if serial_service.connect():
            return jsonify({"success": True, "message": f"Connected to {port} at {baudrate} baud."})
        return jsonify({"success": False, "error": "Failed to connect to the serial port."}), 500
    except Exception as e:
        logger.error("Error connecting to serial device: {e}")"
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/disconnect", methods=["POST"])
@login_required
def disconnect():
    """Disconnect from the serial device."""
    global serial_service
    if serial_service:
        serial_service.disconnect()
        serial_service = None
        return jsonify({"success": True, "message": "Disconnected successfully."})
    return jsonify({"success": False, "error": "No active connection to disconnect."}), 400


@serial_bp.route("/send", methods=["POST"])
@login_required
def send_data():
    """Send data to the serial device."""
    global serial_service
    if not serial_service:
        return jsonify({"success": False, "error": "No active connection."}), 400

    data = request.json.get("data")
    if not data:
        return jsonify({"success": False, "error": "Data to send is required."}), 400

    try:
        if serial_service.send_data(data):
            return jsonify({"success": True, "message": "Data sent successfully."})
        return jsonify({"success": False, "error": "Failed to send data to the device."}), 500
    except Exception as e:
        logger.error(f"Error sending data to serial device: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/read", methods=["GET"])
@login_required
def read_data():
    """Read data from the serial device."""
    global serial_service
    if not serial_service:
        return jsonify({"success": False, "error": "No active connection."}), 400

    try:
        data = serial_service.read_data()
        if data and data.get("success", False):
            return jsonify({"success": True, "data": data["data"]})
        logger.error(f"Failed to read data: {data.get('error', 'Failed to read data.')}")
        return jsonify({"success": False, "error": data.get("error", "Failed to read data.")}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/discover", methods=["GET"])
@login_required
def discover_device():
    """Discover available serial devices."""
    try:
        comm = SerialService()
        device_info = comm.discover_device()
        if device_info.get("success", False):
            return jsonify({"success": True, "device_info": device_info["device_info"]})
        logger.error(f"Failed to discover devices: {device_info.get('error', 'No devices found.')}")
        return jsonify({"success": False, "error": device_info.get("error", "No devices found.")}), 404
    except Exception as e:
        logger.error(f"Error discovering devices: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/configure", methods=["POST"])
@login_required
def configure_device():
    """Set device configurations."""
    global serial_service
    data = request.json
    port = data.get("port")
    baudrate = data.get("baudrate", 115200)
    parity = data.get("parity", "N")
    stopbits = data.get("stopbits", 1)
    databits = data.get("databits", 8)

    if not port:
        logger.error("Port is required.")
        return jsonify({"success": False, "error": "Port is required"}), 400

    try:
        serial_service = SerialService(port, baudrate)
        # `configure_device` is part of the SerialService class
        if serial_service.connect():
            serial_service.connection.parity = parity
            serial_service.connection.stopbits = stopbits
            serial_service.connection.bytesize = databits
            return jsonify({"success": True, "message": f"Device configured and connected at {baudrate} baud."})
        logger.error("Failed to configure the device.")
        return jsonify({"success": False, "error": "Failed to configure the device."}), 500
    except Exception as e:
        logger.error(f"Error configuring device: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
