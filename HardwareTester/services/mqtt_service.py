

import paho.mqtt.client as mqtt
import json
import logging
import time
import threading

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
        self.response = None  # Store the response
        self.response_event = threading.Event()  # Event to synchronize request/response

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
        """
        Override the on_message handler to capture responses.
        """
        try:
            logger.info(f"Received message from topic {msg.topic}: {msg.payload.decode()}")
            self.response = json.loads(msg.payload.decode())  # Decode the response
            self.response_event.set()  # Signal that a response was received
        except Exception as e:
            logger.error(f"Failed to process message: {e}")

    def connect(self):
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT connection established.")
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT connection closed.")

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
            
    def send_request(self, topic, payload, response_topic, timeout=5):
        """
        Send an MQTT request and wait for a response.

        :param topic: The topic to publish the request to.
        :param payload: The payload to send as the request.
        :param response_topic: The topic to listen for the response.
        :param timeout: How long to wait for a response (seconds).
        :return: The response payload or None if timed out.
        """
        self.response = None  # Clear the previous response
        self.response_event.clear()  # Reset the event

        # Subscribe to the response topic
        self.subscribe(response_topic)

        # Publish the request
        self.publish(topic, payload)

        # Wait for the response or timeout
        if self.response_event.wait(timeout):
            return self.response
        else:
            logger.warning(f"Timeout waiting for response on {response_topic}")
            return None


    # Firmware Update
    def update_firmware(self, device_id, firmware_url):
        topic = f"device/{device_id}/firmware"
        try:
            logger.info(f"Starting firmware update for device {device_id}")
            self.publish(topic, {"action": "update_firmware", "url": firmware_url})

            # Monitor firmware update status
            update_topic = f"device/{device_id}/firmware/status"
            self.subscribe(update_topic)

            logger.info("Waiting for firmware update to complete...")
            time.sleep(5)  # Simulate waiting for completion
            logger.info("Firmware update completed successfully.")
            return {"success": True, "message": "Firmware updated successfully."}
        except Exception as e:
            logger.error(f"Firmware update failed: {e}")
            return {"success": False, "error": str(e)}

    # Provisioning Process
    def provision_device(self, device_id, firmware_url, test_plan):
        logger.info(f"Starting provisioning for device {device_id}")
        firmware_result = self.update_firmware(device_id, firmware_url)

        if firmware_result["success"]:
            logger.info(f"Firmware update successful for device {device_id}. Running tests...")
            self.run_tests(device_id, test_plan)
        else:
            logger.error(f"Provisioning failed during firmware update: {firmware_result['error']}")

    # Run Tests
    def run_tests(self, device_id, test_plan):
        topic = f"device/{device_id}/tests"
        try:
            self.publish(topic, {"action": "run_tests", "test_plan": test_plan})
            logger.info(f"Test plan {test_plan} sent to device {device_id}")
        except Exception as e:
            logger.error(f"Failed to send test plan: {e}")

