import logging
import time
from HardwareTester.services.mqtt_client import MqttClient
from HardwareTester.utils.firmware_utils import validate_firmware_file

# Configure logging
logger = logging.getLogger("FirmwareTest")
logging.basicConfig(level=logging.INFO)

# MQTT Configuration
MQTT_BROKER = "localhost"  # Replace with your broker address
MQTT_PORT = 1883
DEVICE_ID = "HeroDevice123"  # Replace with your device ID
FIRMWARE_PATH = "path/to/firmware.bin"  # Replace with your firmware path


def start_mqtt_service():
    """Start the MQTT service and connect to the broker."""
    logger.info("Starting MQTT service...")
    mqtt_client = MqttClient(broker=MQTT_BROKER, port=MQTT_PORT)
    mqtt_client.start()
    logger.info("MQTT service started.")
    return mqtt_client


def listen_to_hero(mqtt_client):
    """Subscribe to the Hero device firmware status."""
    topic = f"device/{DEVICE_ID}/firmware/status"

    def on_message(client, userdata, message):
        logger.info(f"Message received on {message.topic}: {message.payload.decode()}")

    logger.info(f"Subscribing to topic: {topic}")
    mqtt_client.subscribe(topic)
    mqtt_client.set_message_callback(on_message)


def load_firmware(mqtt_client, firmware_path):
    """Validate and upload firmware to the device."""
    logger.info(f"Validating firmware at {firmware_path}...")
    firmware_hash = validate_firmware_file(firmware_path)
    if not firmware_hash:
        logger.error("Firmware validation failed.")
        return

    logger.info(f"Uploading firmware to device {DEVICE_ID}...")
    result = mqtt_client.upload_firmware(DEVICE_ID, firmware_path)
    if result.get("success"):
        logger.info(f"Firmware successfully uploaded to device {DEVICE_ID}.")
    else:
        logger.error(f"Firmware upload failed: {result.get('error')}")


def main():
    # Start the MQTT service
    mqtt_client = start_mqtt_service()

    try:
        # Listen for Hero device messages
        listen_to_hero(mqtt_client)

        # Load firmware onto the device
        load_firmware(mqtt_client, FIRMWARE_PATH)

        # Keep the service running for testing
        logger.info("Listening for device responses...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping test script...")
    finally:
        mqtt_client.stop()


if __name__ == "__main__":
    main()

