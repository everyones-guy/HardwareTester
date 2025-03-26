
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from Hardware_Tester_App.extensions import logger
from Hardware_Tester_App.services.mqtt_service import MQTTService
from Hardware_Tester_App.services.hardware_service import HardwareService

mqtt_bp = Blueprint("mqtt", __name__)

# Initialize MQTT service (update with your broker details)
mqtt_service = MQTTService(broker="mqtt.example.com", port=1883)


@mqtt_bp.route("/mqtt", methods=["GET"])
@login_required
def hardware_dashboard():
    """Render the emulator dashboard."""
    try:
        return render_template("mqtt_management.html")
    except Exception as e:
        logger.error(f"Error rendering emulator dashboard: {e}")
        return jsonify({"success": False, "error": "Failed to render the emulator dashboard."}), 500

@mqtt_bp.route("/api/mqtt/connect", methods=["POST"])
@login_required
def connect_mqtt():
    """
    Connect to the MQTT broker.
    """
    try:
        mqtt_service.connect()
        return jsonify({"success": True, "message": "Connected to MQTT broker."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@mqtt_bp.route("/api/mqtt/disconnect", methods=["POST"])
@login_required
def disconnect_mqtt():
    """
    Disconnect from the MQTT broker.
    """
    try:
        mqtt_service.disconnect()
        return jsonify({"success": True, "message": "Disconnected from MQTT broker."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@mqtt_bp.route("/api/mqtt/publish", methods=["POST"])
@login_required
def publish_message():
    """
    Publish a message to an MQTT topic.
    Request Body:
        {
            "topic": "device/123/status",
            "payload": {"key": "value"}
        }
    """
    data = request.json
    topic = data.get("topic")
    payload = data.get("payload")

    if not topic or not payload:
        return jsonify({"success": False, "error": "Topic and payload are required"}), 400

    try:
        mqtt_service.publish(topic, payload)
        return jsonify({"success": True, "message": f"Message published to {topic}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@mqtt_bp.route("/api/mqtt/subscribe", methods=["POST"])
@login_required
def subscribe_topic():
    """
    Subscribe to an MQTT topic.
    Request Body:
        {
            "topic": "device/123/#"
        }
    """
    data = request.json
    topic = data.get("topic")

    if not topic:
        return jsonify({"success": False, "error": "Topic is required"}), 400

    try:
        mqtt_service.subscribe(topic)
        return jsonify({"success": True, "message": f"Subscribed to topic {topic}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@mqtt_bp.route("/api/mqtt/discover-device", methods=["POST"])
@login_required
def discover_device():
    """
    Discover a device via MQTT.
    Request Body:
        {
            "device_id": "123"
        }
    """
    data = request.json
    device_id = data.get("device_id")

    if not device_id:
        return jsonify({"success": False, "error": "Device ID is required"}), 400

    try:
        mqtt_service.discover_device(device_id)
        return jsonify({"success": True, "message": f"Discovery request sent for device {device_id}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@mqtt_bp.route("/api/mqtt/link", methods=["POST"])
@login_required
def create_link():
    data = request.json
    source = data["source"]
    target = data["target"]
    settings = data["settings"]

    # Save link to database or configuration file
    HardwareService.save_link(source, target, settings)
    return jsonify({"success": True, "message": "Link created successfully."})

