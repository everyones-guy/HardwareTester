from flask import Blueprint, jsonify, request
from HardwareTester.services.serial_service import SerialService

serial_bp = Blueprint("serial", __name__)

# Global instance of the SerialService
serial_service = None


@serial_bp.route("/connect", methods=["POST"])
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
        if serial_service.connect():
            return jsonify({"success": True, "message": f"Connected to {port} at {baudrate} baud."})
        return jsonify({"success": False, "error": "Failed to connect to the serial port."}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/disconnect", methods=["POST"])
def disconnect():
    """Disconnect from the serial device."""
    global serial_service
    if serial_service:
        serial_service.disconnect()
        serial_service = None
        return jsonify({"success": True, "message": "Disconnected successfully."})
    return jsonify({"success": False, "error": "No active connection to disconnect."}), 400


@serial_bp.route("/send", methods=["POST"])
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
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/read", methods=["GET"])
def read_data():
    """Read data from the serial device."""
    global serial_service
    if not serial_service:
        return jsonify({"success": False, "error": "No active connection."}), 400

    try:
        data = serial_service.read_data()
        if data and data.get("success", False):
            return jsonify({"success": True, "data": data["data"]})
        return jsonify({"success": False, "error": data.get("error", "Failed to read data.")}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/discover", methods=["GET"])
def discover_device():
    """Discover available serial devices."""
    try:
        comm = SerialService()
        device_info = comm.discover_device()
        if device_info.get("success", False):
            return jsonify({"success": True, "device_info": device_info["device_info"]})
        return jsonify({"success": False, "error": device_info.get("error", "No devices found.")}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@serial_bp.route("/configure", methods=["POST"])
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
        return jsonify({"success": False, "error": "Port is required"}), 400

    try:
        serial_service = SerialService(port, baudrate)
        # `configure_device` is part of the SerialService class
        if serial_service.connect():
            serial_service.connection.parity = parity
            serial_service.connection.stopbits = stopbits
            serial_service.connection.bytesize = databits
            return jsonify({"success": True, "message": f"Device configured and connected at {baudrate} baud."})
        return jsonify({"success": False, "error": "Failed to configure the device."}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
