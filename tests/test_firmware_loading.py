import tkinter as tk
from tkinter import scrolledtext
from HardwareTester.services.mqtt_client import MQTTClient
from HardwareTester.utils.serial_comm import SerialComm
import logging

# Configure logging
logger = logging.getLogger("FirmwareTestGUI")
logging.basicConfig(level=logging.INFO)

class FirmwareTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firmware Test Interface")

        # Communication log
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
        self.log_area.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        # Buttons
        self.start_mqtt_button = tk.Button(root, text="Start MQTT Service", command=self.start_mqtt_service)
        self.start_mqtt_button.grid(row=1, column=0, padx=10, pady=5)

        self.discover_device_button = tk.Button(root, text="Discover Device", command=self.discover_device)
        self.discover_device_button.grid(row=1, column=1, padx=10, pady=5)

        self.load_firmware_button = tk.Button(root, text="Load Firmware", command=self.load_firmware)
        self.load_firmware_button.grid(row=1, column=2, padx=10, pady=5)

        # MQTT and SerialComm instances
        self.mqtt_client = None
        self.serial_comm = None

    def log(self, message):
        """Log a message to the communication log."""
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        logger.info(message)

    def start_mqtt_service(self):
        """Start the MQTT service."""
        try:
            if not self.mqtt_client:
                self.mqtt_client = MQTTClient(broker="localhost", port=1883)
                self.mqtt_client.start()
                self.log("MQTT Service started.")
            else:
                self.log("MQTT Service is already running.")
        except Exception as e:
            self.log(f"Failed to start MQTT service: {e}")

    def discover_device(self):
        """Discover devices via serial communication."""
        try:
            if not self.serial_comm:
                self.serial_comm = SerialComm(port=None, debug=True)

            port = self.serial_comm.find_comm_port()
            if not port:
                self.log("Discovery failed: No suitable COM port found.")
                return

            self.serial_comm.port = port
            self.serial_comm.connect()

            discovery_result = self.serial_comm.discover_device()
            if discovery_result.get("success"):
                self.log(f"Device discovered on {discovery_result['port']}: {discovery_result['device_info']}")
            else:
                self.log(f"Discovery failed: {discovery_result['error']}")
        except Exception as e:
            self.log(f"Failed to discover device: {e}")

    def load_firmware(self):
        """Load firmware onto the device."""
        firmware_path = "path/to/firmware.bin"  # Replace with dynamic file picker if needed
        try:
            if not self.serial_comm:
                self.log("Serial communication is not established.")
                return

            self.log(f"Validating firmware at {firmware_path}...")
            firmware_hash = self.serial_comm.validate_firmware_file(firmware_path)
            if not firmware_hash:
                self.log("Firmware validation failed.")
                return

            if self.mqtt_client:
                self.log(f"Uploading firmware to device...")
                result = self.mqtt_client.upload_firmware("HeroDevice123", firmware_path)  # Replace with device ID
                if result.get("success"):
                    self.log(f"Firmware uploaded successfully.")
                else:
                    self.log(f"Firmware upload failed: {result['error']}")
            else:
                self.log("MQTT Service is not running.")
        except Exception as e:
            self.log(f"Failed to load firmware: {e}")

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = FirmwareTestApp(root)
    app.run()
