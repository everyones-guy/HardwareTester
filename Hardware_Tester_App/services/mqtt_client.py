import json
import time
import threading
import hashlib
import os
from pathlib import Path
from dotenv import load_dotenv
from Hardware_Tester_App.services.mqtt_service import MQTTService
from Hardware_Tester_App.utils.custom_logger import CustomLogger
from Hardware_Tester_App.extensions import socketio

# Load environment variables from .env
load_dotenv()

# Initialize logger
logger = CustomLogger.get_logger("mqtt_client")

# Constants
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # Seconds between retries
CHUNK_SIZE = 4096  # 4KB for firmware chunking

class MQTTClient:
    """Enhanced MQTT Client for managing firmware updates and device interactions."""

    def __init__(self):
        """
        Initialize the MQTT client for firmware updates and device management.
        Uses `MQTTService` for MQTT connection.
        """
        self.mqtt_service = MQTTService()
        self.response = None  # Store the response
        self.response_event = threading.Event()  # Synchronize request/response

    def _setup_client(self):
        """Set up MQTT client with optional authentication and TLS."""
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        if self.tls:
            self.client.tls_set()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection events."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection events."""
        if rc != 0:
            logger.warning(f"Unexpected disconnection (code {rc}). Attempting to reconnect...")
            self.connect()

    def on_message(self, client, userdata, msg):
        """Handle received MQTT messages."""
        logger.info(f"Received message on {msg.topic}: {msg.payload.decode()}")
        try:
            self.response = json.loads(msg.payload.decode())
            self.response_event.set()  # Signal that a response was received
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding MQTT message payload: {e}")

    def connect(self):
        """Connect to the MQTT broker and start the client loop."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT connection closed.")

    def publish(self, topic: str, payload: str, retries=DEFAULT_RETRY_COUNT):
        """Publish a message to a specific topic with retry mechanism."""
        self.mqtt_service.publish(topic, payload, retries)

    def subscribe(self, topic: str, retries=DEFAULT_RETRY_COUNT):
        """Subscribe to a specific topic with retry mechanism."""
        self.mqtt_service.subscribe(topic, retries)

    def upload_firmware(self, device_id: str, firmware_path: str):
        """Upload firmware to a device in chunks."""
        topic = f"device/{device_id}/firmware/update"
        firmware_hash = self.validate_firmware_file(firmware_path)
        if not firmware_hash:
            logger.error("Firmware validation failed. Upload aborted.")
            return {"success": False, "error": "Firmware validation failed."}

        try:
            with open(firmware_path, "rb") as f:
                chunk_number = 1
                while chunk := f.read(CHUNK_SIZE):
                    payload = {
                        "action": "upload_chunk",
                        "firmware_hash": firmware_hash,
                        "chunk_number": chunk_number,
                        "chunk": chunk.hex(),
                    }
                    self.publish(topic, json.dumps(payload))
                    logger.info(f"Chunk {chunk_number} uploaded for {firmware_path}")
                    chunk_number += 1

            # Finalize the upload
            self.publish(topic, json.dumps({"action": "finalize_upload", "firmware_hash": firmware_hash}))
            logger.info(f"Firmware file {firmware_path} uploaded to {device_id}.")
            return {"success": True, "message": "Firmware uploaded successfully."}
        except Exception as e:
            logger.error(f"Failed to upload firmware: {e}")
            return {"success": False, "error": str(e)}

    def validate_firmware(self, device_id: str):
        """Send a firmware validation request to a device."""
        topic = f"device/{device_id}/firmware/validate"
        payload = {"action": "validate"}
        self.publish(topic, json.dumps(payload))
        logger.info(f"Firmware validation request sent for device {device_id}.")

    def check_firmware_status(self, device_id: str):
        """Subscribe to firmware update status topic."""
        topic = f"device/{device_id}/firmware/status"
        self.subscribe(topic)
        logger.info(f"Subscribed to firmware status updates for {device_id}.")

    def validate_firmware_file(self, firmware_path: str) -> str:
        """
        Validate firmware file for supported formats and return its hash.

        :param firmware_path: Path to the firmware file.
        :return: SHA-256 hash of the firmware file if valid, None otherwise.
        """
        try:
            with open(firmware_path, "rb") as f:
                firmware_data = f.read()

            file_extension = Path(firmware_path).suffix.lower()
            if file_extension in [".bin", ".hex", ".txt"]:
                logger.info(f"Validating {file_extension} firmware file.")
                return hashlib.sha256(firmware_data).hexdigest()

            logger.error("Unsupported firmware format.")
            return None
        except FileNotFoundError:
            logger.error(f"Firmware file not found: {firmware_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to validate firmware file: {e}")
            return None

    @socketio.on("start_mirror")
    def start_mirror(self, data):
        device_topic = data.get("topic")

        def on_message(client, userdata, message):
            command = message.payload.decode()
            socketio.emit("mirror_update", {"command": command, "topic": message.topic})

        self.subscribe(device_topic)
        self.mqtt_service.client.on_message = on_message  # Use the `MQTTService` client instance
        