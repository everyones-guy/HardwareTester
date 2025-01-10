import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from HardwareTester.services.mqtt_client import MQTTClient
from HardwareTester.utils.serial_comm import SerialComm
from HardwareTester.utils.firmware_utils import validate_firmware_file, process_uploaded_firmware
from HardwareTester.services.hardware_service import HardwareService
from HardwareTester.services.emulator_service import EmulatorService
import logging
import time

# Configure logging
logger = logging.getLogger("FirmwareTestGUI")
logging.basicConfig(level=logging.INFO, filename="firmware_test.log", filemode="w")

class FirmwareTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firmware Test Interface")

        # Communication log
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
        self.log_area.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        # Buttons
        self.start_mqtt_button = tk.Button(root, text="Start MQTT Service", command=self.start_mqtt_service)
        self.start_mqtt_button.grid(row=1, column=0, padx=10, pady=5)

        self.discover_device_button = tk.Button(root, text="Discover Device", command=self.discover_device)
        self.discover_device_button.grid(row=1, column=1, padx=10, pady=5)

        self.load_firmware_button = tk.Button(root, text="Load Firmware", command=self.load_firmware)
        self.load_firmware_button.grid(row=1, column=2, padx=10, pady=5)

        self.monitor_device_button = tk.Button(root, text="Monitor Device", command=self.monitor_device)
        self.monitor_device_button.grid(row=1, column=3, padx=10, pady=5)

        self.compare_devices_button = tk.Button(root, text="Compare Devices", command=self.compare_devices)
        self.compare_devices_button.grid(row=2, column=0, columnspan=4, padx=10, pady=5)

        # MQTT and SerialComm instances
        self.mqtt_client = None
        self.serial_comm = None
        self.firmware_path = None
        self.stop_monitoring = False

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
        """Discover devices via MQTT."""
        try:
            device_list = HardwareService.list_devices()
            if device_list["success"]:
                self.log(f"Devices discovered: {device_list['devices']}")
            else:
                self.log(f"Device discovery failed: {device_list['error']}")
        except Exception as e:
            self.log(f"Failed to discover devices: {e}")

    def load_firmware(self):
        """Load firmware onto the device."""
        self.firmware_path = filedialog.askopenfilename(title="Select Firmware File",
                                                        filetypes=[("Firmware Files", "*.txt")])
        if not self.firmware_path:
            self.log("No firmware file selected.")
            return

        try:
            self.log(f"Validating firmware at {self.firmware_path}...")
            firmware_hash = validate_firmware_file(self.firmware_path)
            if not firmware_hash:
                self.log("Firmware validation failed.")
                return

            with open(self.firmware_path, "r") as f:
                firmware_data = f.read()

            self.log("Uploading text-based firmware to selected devices...")
            for device_id in self.get_selected_devices():
                result = HardwareService.upload_firmware_to_device(device_id, firmware_data)
                if result["success"]:
                    self.log(f"Firmware uploaded successfully to device {device_id}.")
                else:
                    self.log(f"Firmware upload failed for device {device_id}: {result['error']}")
        except Exception as e:
            self.log(f"Failed to load firmware: {e}")


    def monitor_device(self):
        """Monitor device status in real-time."""
        try:
            self.stop_monitoring = False
            self.log("Monitoring device status...")
            while not self.stop_monitoring:
                device_status = HardwareService.get_device_status()
                if device_status["success"]:
                    self.log(f"Device Status: {device_status['status']}")
                else:
                    self.log(f"Monitoring failed: {device_status['error']}")
                time.sleep(1)
        except Exception as e:
            self.log(f"Device monitoring error: {e}")

    def compare_devices(self):
        """Compare the operation of multiple devices."""
        try:
            machine_ids = messagebox.askstring("Compare Devices", "Enter machine IDs separated by commas:")
            if not machine_ids:
                self.log("No machine IDs provided.")
                return

            machine_ids = [id.strip() for id in machine_ids.split(",")]
            self.log(f"Comparing devices: {machine_ids}")

            comparisons = []
            for device_id in machine_ids:
                device = HardwareService.get_device_by_id(device_id)
                if device:
                    comparisons.append({
                        "id": device_id,
                        "firmware": device.device_metadata.get("firmware_text", "No firmware uploaded"),
                    })

            # Highlight differences
            differences = [
                f"Device {c['id']}: {c['firmware']}" for c in comparisons
            ]
            self.log(f"Comparison Results:\n" + "\n".join(differences))
        except Exception as e:
            self.log(f"Device comparison error: {e}")


    def stop_monitoring_device(self):
        """Stop real-time monitoring."""
        self.stop_monitoring = True
        self.log("Stopped real-time firmware monitoring.")
        
    def monitor_firmware(self):
        """Monitor firmware status in real-time."""
        try:
            self.stop_monitoring = False
            self.log("Starting real-time firmware monitoring...")
            while not self.stop_monitoring:
                devices = HardwareService.list_devices()
                for device in devices.get("devices", []):
                    firmware_version = device["metadata"].get("firmware_version", "Unknown")
                    self.log(f"Device {device['name']} is running firmware version: {firmware_version}")
                time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            self.log(f"Firmware monitoring error: {e}")



    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = FirmwareTestApp(root)
    app.run()
