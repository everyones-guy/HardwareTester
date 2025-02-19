import os
import json
import time
import threading
from dotenv import load_dotenv
from paho.mqtt.client import Client
from HardwareTester.utils.custom_logger import CustomLogger

# Load environment variables from .env
load_dotenv()

# Fetch MQTT broker details from .env
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", None)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", None)
MQTT_TLS = os.getenv("MQTT_TLS", "False").lower() in ("true", "1")

# Initialize logger
logger = CustomLogger.get_logger("mqtt_service")

DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # Seconds between retries


class MQTTService:
    """Enhanced MQTT Service for interacting with devices."""

    def __init__(self, broker=MQTT_BROKER, port=MQTT_PORT, username=MQTT_USERNAME, password=MQTT_PASSWORD, tls=MQTT_TLS):
        """
        Initialize the MQTT client.

        :param broker: MQTT broker address.
        :param port: MQTT broker port.
        :param username: Username for authentication (optional).
        :param password: Password for authentication (optional).
        :param tls: Enable TLS/SSL (default: False).
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls
        self.client = Client()
        self._setup_client()
        self.response = None  # Store the response
        self.response_event = threading.Event()  # Event to synchronize request/response

    def _setup_client(self):
        """Configure the MQTT client with optional authentication and TLS."""
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
            logger.warning(f"Unexpected disconnection from MQTT broker (code {rc}). Attempting to reconnect...")
            self.connect()

    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            logger.info(f"Received message on {msg.topic}: {msg.payload.decode()}")
            self.response = json.loads(msg.payload.decode())
            self.response_event.set()  # Signal that a response was received
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON payload on topic {msg.topic}")
        except Exception as e:
            logger.error(f"Failed to process message: {e}")

    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT connection closed.")

    def publish(self, topic: str, payload: dict, retries=DEFAULT_RETRY_COUNT):
        """Publish a message to a specific MQTT topic."""
        for attempt in range(retries):
            try:
                self.client.publish(topic, json.dumps(payload))
                logger.info(f"Published to {topic}: {payload}")
                return
            except Exception as e:
                logger.error(f"Failed to publish to {topic} on attempt {attempt + 1}: {e}")
                time.sleep(DEFAULT_RETRY_DELAY)
        logger.error(f"All attempts to publish to {topic} failed.")

    def subscribe(self, topic: str, retries=DEFAULT_RETRY_COUNT):
        """Subscribe to a specific MQTT topic."""
        for attempt in range(retries):
            try:
                self.client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
                return
            except Exception as e:
                logger.error(f"Failed to subscribe to {topic} on attempt {attempt + 1}: {e}")
                time.sleep(DEFAULT_RETRY_DELAY)
        logger.error(f"All attempts to subscribe to {topic} failed.")

    def send_request(self, topic: str, payload: dict, response_topic: str, timeout: int = 5) -> dict:
        """
        Send an MQTT request and wait for a response.

        :param topic: Topic to publish the request to.
        :param payload: Payload to send in the request.
        :param response_topic: Topic to listen for the response.
        :param timeout: Timeout for waiting for a response (in seconds).
        :return: The response payload or an error message if timed out.
        """
        self.response = None
        self.response_event.clear()

        self.subscribe(response_topic)
        self.publish(topic, payload)

        if self.response_event.wait(timeout):
            return {"success": True, "response": self.response}
        else:
            logger.warning(f"Timeout waiting for response on {response_topic}")
            return {"success": False, "error": "Timeout waiting for response"}

    def list_topics(self):
        """List all topics the client is subscribed to."""
        logger.info("Subscribed topics:")
        for topic in self.client._userdata:
            logger.info(f" - {topic}")

    def update_firmware(self, device_id: str, firmware_url: str) -> dict:
        """Start a firmware update for a device."""
        topic = f"device/{device_id}/firmware"
        try:
            logger.info(f"Starting firmware update for device {device_id}")
            self.publish(topic, {"action": "update_firmware", "url": firmware_url})

            # Wait for firmware update status
            update_topic = f"device/{device_id}/firmware/status"
            return self.send_request(update_topic, {}, update_topic)
        except Exception as e:
            logger.error(f"Firmware update failed: {e}")
            return {"success": False, "error": str(e)}

    def provision_device(self, device_id: str, firmware_url: str, test_plan: dict) -> dict:
        """Provision a device by updating firmware and running tests."""
        logger.info(f"Starting provisioning for device {device_id}")
        firmware_result = self.update_firmware(device_id, firmware_url)

        if not firmware_result["success"]:
            logger.error(f"Provisioning failed during firmware update: {firmware_result['error']}")
            return {"success": False, "error": firmware_result["error"]}

        logger.info(f"Firmware update successful for device {device_id}. Running tests...")
        return self.run_tests(device_id, test_plan)

    def run_tests(self, device_id: str, test_plan: dict) -> dict:
        """Run a test plan on a device."""
        topic = f"device/{device_id}/tests"
        try:
            self.publish(topic, {"action": "run_tests", "test_plan": test_plan})
            logger.info(f"Test plan sent to device {device_id}")
            return {"success": True, "message": "Test plan sent successfully."}
        except Exception as e:
            logger.error(f"Failed to send test plan: {e}")
            return {"success": False, "error": str(e)}

