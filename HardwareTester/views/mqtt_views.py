from flask import Blueprint, render_template, request, jsonify
from HardwareTester.services.mqtt_service import connect_mqtt, publish_message, subscribe_topic

mqtt_bp = Blueprint("mqtt", __name__)

@mqtt_bp.route("/", methods=["GET"])
def mqtt_management():
    """Render the MQTT Management page."""
    return render_template("mqtt_management.html")

@mqtt_bp.route("/connect", methods=["POST"])
def connect_to_broker():
    """Connect to an MQTT broker."""
    data = request.json
    result = connect_mqtt(data)
    if result["success"]:
        return jsonify({"success": True, "message": "Connected to MQTT broker successfully."})
    return jsonify({"success": False, "error": result["error"]}), 500

@mqtt_bp.route("/publish", methods=["POST"])
def publish():
    """Publish a message to an MQTT topic."""
    data = request.json
    result = publish_message(data["topic"], data["message"])
    if result["success"]:
        return jsonify({"success": True, "message": "Message published successfully."})
    return jsonify({"success": False, "error": result["error"]}), 500

@mqtt_bp.route("/subscribe", methods=["POST"])
def subscribe():
    """Subscribe to an MQTT topic."""
    data = request.json
    result = subscribe_topic(data["topic"])
    if result["success"]:
        return jsonify({"success": True, "message": "Subscribed to topic successfully."})
    return jsonify({"success": False, "error": result["error"]}), 500

