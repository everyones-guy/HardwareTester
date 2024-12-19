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
        serial_service = SerialService(port, baudrate)
        serial_service.connect()
        return jsonify({"success": True, "message": f"Connected to {port} at {baudrate} baud."})
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
    return jsonify({"success": False, "error": "No active connection."}), 400

@serial_bp.route("/send", methods=["POST"])
def send_data():
    """Send data to the serial device."""
    global serial_service
    if not serial_service:
        return jsonify({"success": False, "error": "No active connection."}), 400

    data = request.json.get("data")
    if not data:
        return jsonify({"success": False, "error": "Data is required"}), 400

    success = serial_service.send_data(data)
    if success:
        return jsonify({"success": True, "message": "Data sent successfully."})
    return jsonify({"success": False, "error": "Failed to send data."})

@serial_bp.route("/read", methods=["GET"])
def read_data():
    """Read data from the serial device."""
    global serial_service
    if not serial_service:
        return jsonify({"success": False, "error": "No active connection."}), 400

    data = serial_service.read_data()
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "error": "Failed to read data."})
