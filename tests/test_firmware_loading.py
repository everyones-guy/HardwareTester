import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, Listbox
from HardwareTester.services.mqtt_client import MQTTClient
from HardwareTester.services.serial_service import SerialService
from HardwareTester.utils.firmware_utils import validate_firmware_file
from HardwareTester.services.hardware_service import HardwareService
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester import create_app  # Ensure `create_app` initializes your Flask app
from flask import current_app
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
        self.log_area.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        # Device listbox
        self.device_listbox = Listbox(root, height=20, width=30)
        self.device_listbox.grid(row=0, column=3, padx=10, pady=10)
        self.update_device_list_button = tk.Button(
            root, text="Refresh Devices", command=self.update_device_list
        )
        self.update_device_list_button.grid(row=1, column=3, padx=10, pady=5)

        # Buttons
        self.start_mqtt_button = tk.Button(root, text="Start MQTT Service", command=self.start_mqtt_service)
        self.start_mqtt_button.grid(row=1, column=0, padx=10, pady=5)

        self.discover_device_button = tk.Button(root, text="Discover Device", command=self.discover_device)
        self.discover_device_button.grid(row=1, column=1, padx=10, pady=5)

        self.load_firmware_button = tk.Button(root, text="Load Firmware", command=self.load_firmware)
        self.load_firmware_button.grid(row=1, column=2, padx=10, pady=5)

        self.configure_device_button = tk.Button(root, text="Configure Device", command=self.configure_device)
        self.configure_device_button.grid(row=2, column=0, padx=10, pady=5)

        self.compare_devices_button = tk.Button(root, text="Compare Devices", command=self.compare_devices)
        self.compare_devices_button.grid(row=2, column=1, columnspan=3, padx=10, pady=5)

        # Instances
        self.mqtt_client = None
        self.serial_service = None

    def log(self, message):
        """Log a message to the communication log."""
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        logger.info(message)

    def update_device_list(self):
        """Update the list of devices in the listbox."""
        try:
            with current_app.app_context():
                result = HardwareService.get_device_status()
                if result["success"]:
                    self.device_listbox.delete(0, tk.END)
                    for device in result["status"]:
                        self.device_listbox.insert(
                            tk.END,
                            f"{device['id']}: {device['name']} - Firmware {device['firmware_version']}"
                        )
                else:
                    self.log(f"Failed to fetch devices: {result['error']}")
        except Exception as e:
            self.log(f"Error updating device list: {e}")

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
        """Discover devices via SerialService."""
        try:
            self.serial_service = SerialService()
            device_info = self.serial_service.discover_device()
            if device_info:
                self.log(f"Device discovered: {device_info}")
            else:
                self.log("No devices discovered.")
        except Exception as e:
            self.log(f"Failed to discover devices: {e}")

    def load_firmware(self):
        """Load firmware onto the device."""
        firmware_path = filedialog.askopenfilename(
            title="Select Firmware File", filetypes=[("Firmware Files", "*.txt")]
        )
        if not firmware_path:
            self.log("No firmware file selected.")
            return

        try:
            self.log(f"Validating firmware at {firmware_path}...")
            firmware_hash = validate_firmware_file(firmware_path)
            if not firmware_hash:
                self.log("Firmware validation failed.")
                return

            with open(firmware_path, "r") as f:
                firmware_data = f.read()

            self.log("Uploading firmware to selected devices...")
            with current_app.app_context():
                for device_id in self.get_selected_devices():
                    result = HardwareService.upload_firmware_to_device(device_id, firmware_data)
                    if result["success"]:
                        self.log(f"Firmware uploaded successfully to device {device_id}.")
                    else:
                        self.log(f"Firmware upload failed for device {device_id}: {result['error']}")
        except Exception as e:
            self.log(f"Failed to load firmware: {e}")

    def configure_device(self):
        """Configure a serial device."""
        try:
            if not self.serial_service:
                self.serial_service = SerialService(port="/dev/ttyUSB0", baudrate=9600)

            # Prompt for configuration
            config = {
                "baudrate": messagebox.askstring("Configuration", "Enter Baudrate (e.g., 9600):"),
                "parity": messagebox.askstring("Configuration", "Enter Parity (N, E, O):"),
                "stopbits": messagebox.askstring("Configuration", "Enter Stop Bits (1, 1.5, 2):"),
                "databits": messagebox.askstring("Configuration", "Enter Data Bits (5, 6, 7, 8):")
            }

            if not all(config.values()):
                self.log("Configuration canceled or invalid input.")
                return

            success = self.serial_service.configure_device(
                baudrate=int(config["baudrate"]),
                parity=config["parity"],
                stopbits=float(config["stopbits"]),
                databits=int(config["databits"])
            )

            if success:
                self.log("Device successfully configured.")
            else:
                self.log("Device configuration failed.")
        except Exception as e:
            self.log(f"Error configuring device: {e}")

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
            with current_app.app_context():
                for device_id in machine_ids:
                    device = HardwareService.get_device_by_id(device_id)
                    if device:
                        comparisons.append({
                            "id": device_id,
                            "firmware": device.device_metadata.get("firmware_text", "No firmware uploaded"),
                        })

            differences = [f"Device {c['id']}: {c['firmware']}" for c in comparisons]
            self.log(f"Comparison Results:\n" + "\n".join(differences))
        except Exception as e:
            self.log(f"Device comparison error: {e}")

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    app_context = create_app().app_context()
    app_context.push()

    root = tk.Tk()
    app = FirmwareTestApp(root)
    app.run()
