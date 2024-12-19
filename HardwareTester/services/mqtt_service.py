import paho.mqtt.client as mqtt
import json
import logging

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self, broker, port=1883, username=None, password=None, tls=False):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls
        self.client = mqtt.Client()
        self._setup_client()
        self.device_responses = {}  # Store responses from devices

    def _setup_client(self):
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        if self.tls:
            self.client.tls_set()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker {self.broker}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")

    def on_message(self, client, userdata, msg):
        logger.info(f"Received message from topic {msg.topic}: {msg.payload.decode()}")
        try:
            payload = json.loads(msg.payload.decode())
            if "device_id" in payload:
                self.device_responses[payload["device_id"]] = payload
        except json.JSONDecodeError:
            logger.warning("Received non-JSON payload.")

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT connection established.")
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")

    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT connection closed.")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")

    def publish(self, topic, payload):
        try:
            self.client.publish(topic, json.dumps(payload))
            logger.info(f"Published to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")

    def subscribe(self, topic):
        try:
            self.client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")

    def discover_device(self, device_id):
        """
        Query device metadata and settings.
        :param device_id: Device ID to discover.
        """
        try:
            topic = f"device/{device_id}/info"
            self.subscribe(topic)
            self.publish(topic, {"action": "get_info"})  # Query the device
            logger.info(f"Sent discovery request to {topic}")
        except Exception as e:
            logger.error(f"Failed to query device: {e}")

    def get_device_response(self, device_id):
        """
        Fetch the response for a discovered device.
        :param device_id: Device ID to fetch the response for.
        :return: Response data or None if no response received.
        """
        return self.device_responses.get(device_id)
