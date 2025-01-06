import paho.mqtt.client as mqtt
import hashlib
import os
from pathlib import Path
from HardwareTester.extensions import logger

class FirmwareMQTTClient:
    """MQTT Client for managing firmware updates."""

    def __init__(self, broker: str, port: int = 1883, username: str = None, password: str = None, tls: bool = False):
        """
        Initialize the MQTT client for firmware updates.

        :param broker: MQTT broker address.
        :param port: MQTT broker port (default: 1883).
        :param username: Username for authentication (optional).
        :param password: Password for authentication (optional).
        :param tls: Enable TLS/SSL (default: False).
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls
        self.client = mqtt.Client()
        self._setup_client()

    def _setup_client(self):
        """Set up MQTT client with optional authentication and TLS."""
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        if self.tls:
            self.client.tls_set()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection events."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")

    def on_message(self, client, userdata, msg):
        """Handle received MQTT messages."""
        logger.info(f"Received message on {msg.topic}: {msg.payload.decode()}")

    def connect(self):
        """Connect to the MQTT broker and start the client loop."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")

    def publish(self, topic: str, payload: str):
        """Publish a message to a specific topic."""
        try:
            self.client.publish(topic, payload)
            logger.info(f"Published to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")

    def subscribe(self, topic: str):
        """Subscribe to a specific topic."""
        try:
            self.client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT connection closed.")

    def upload_firmware(self, device_id: str, firmware_path: str):
        """Upload firmware to a device."""
        topic = f"device/{device_id}/firmware/update"
        firmware_hash = self.validate_firmware_file(firmware_path)
        if not firmware_hash:
            logger.error("Firmware validation failed. Upload aborted.")
            return {"success": False, "error": "Firmware validation failed."}

        try:
            with open(firmware_path, "rb") as f:
                firmware_data = f.read()
                payload = {
                    "action": "upload",
                    "firmware_hash": firmware_hash,
                    "firmware": firmware_data.hex(),
                }
                self.publish(topic, str(payload))
                logger.info(f"Firmware file {firmware_path} uploaded to {device_id}.")
                return {"success": True, "message": "Firmware uploaded successfully."}
        except Exception as e:
            logger.error(f"Failed to upload firmware: {e}")
            return {"success": False, "error": str(e)}

    def validate_firmware(self, device_id: str):
        """Send a firmware validation request to a device."""
        topic = f"device/{device_id}/firmware/validate"
        payload = {"action": "validate"}
        self.publish(topic, str(payload))
        logger.info(f"Firmware validation request sent for device {device_id}.")

    def check_firmware_status(self, device_id: str):
        """Subscribe to firmware update status topic."""
        topic = f"device/{device_id}/firmware/status"
        self.subscribe(topic)
        logger.info(f"Subscribed to firmware status updates for {device_id}.")

    @staticmethod
    def validate_firmware_file(firmware_path: str) -> str:
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
