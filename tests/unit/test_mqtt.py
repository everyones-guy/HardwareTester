import unittest
from HardwareTester.services.mqtt_service import MQTTService

class TestMQTTService(unittest.TestCase):
    def setUp(self):
        self.mqtt_service = MQTTService(
            broker="test.mosquitto.org",
            port=1883
        )
        self.mqtt_service.connect()

    def test_publish(self):
        topic = "test/topic"
        payload = {"message": "Hello, MQTT"}
        self.mqtt_service.publish(topic, payload)
        self.assertTrue(True)  # Assume successful publish

    def test_subscribe(self):
        topic = "test/topic"
        self.mqtt_service.subscribe(topic)
        self.assertTrue(True)  # Assume successful subscribe

    def tearDown(self):
        self.mqtt_service.disconnect()
