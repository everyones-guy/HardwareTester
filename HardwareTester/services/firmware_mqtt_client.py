import paho.mqtt.client as mqtt
import os
import hashlib
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FirmwareMQTT")

class FirmwareMQTTClient:
    def __init__(self, broker, port=1883, username=None, password=None, tls=False):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls
        self.client = mqtt.Client()
        self._setup_client()

    def _setup_client(self):
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        if self.tls:
            self.client.tls_set()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")

    def on_message(self, client, userdata, msg):
        logger.info(f"Received message on {msg.topic}: {msg.payload.decode()}")

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")

    def publish(self, topic, payload):
        try:
            self.client.publish(topic, payload)
            logger.info(f"Published to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")

    def subscribe(self, topic):
        try:
            self.client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT connection closed.")

    def upload_firmware(self, device_id, firmware_path):
        """Upload firmware to the device."""
        topic = f"device/{device_id}/firmware/update"
        if not Path(firmware_path).is_file():
            logger.error("Firmware file not found.")
            return

        try:
            with open(firmware_path, "rb") as f:
                firmware_data = f.read()
                firmware_hash = hashlib.sha256(firmware_data).hexdigest()
                payload = {
                    "action": "upload",
                    "firmware_hash": firmware_hash,
                    "firmware": firmware_data.hex(),
                }
                self.publish(topic, str(payload))
                logger.info(f"Firmware file {firmware_path} uploaded to {device_id}.")
        except Exception as e:
            logger.error(f"Failed to upload firmware: {e}")

    def validate_firmware(self, device_id):
        """Validate firmware on the device."""
        topic = f"device/{device_id}/firmware/validate"
        payload = {"action": "validate"}
        self.publish(topic, str(payload))
        logger.info(f"Validation request sent for device {device_id}.")

    def check_firmware_status(self, device_id):
        """Check firmware update status."""
        topic = f"device/{device_id}/firmware/status"
        self.subscribe(topic)
        logger.info(f"Subscribed to firmware status updates for {device_id}.")
