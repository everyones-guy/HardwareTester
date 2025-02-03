import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from HardwareTester.utils.firmware_utils import process_firmware_package
from HardwareTester.utils.test_generator import TestGenerator
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.services.hardware_service import HardwareService
from HardwareTester.services.mqtt_service import MQTTService
from HardwareTester.utils.source_code_analyzer import SourceCodeAnalyzer
from flask import Flask

# Initialize Flask app
from HardwareTester import create_app  # Ensure this exists in your project
app = create_app()


class FirmwareTestUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Firmware & C# Test Generator")

        self.selected_file = None
        self.selected_csharp_files = []
        self.generated_tests = []

        # UI Components
        self.file_label = tk.Label(root, text="Select Firmware or C# Files:")
        self.file_label.pack(pady=5)

        self.file_button = tk.Button(root, text="Browse Firmware", command=self.select_file)  
        self.file_button.pack(pady=5)

        self.csharp_button = tk.Button(root, text="Browse C# Files", command=self.select_csharp_files)  
        self.csharp_button.pack(pady=5)

        self.generate_tests_button = tk.Button(root, text="Generate Tests", command=self.generate_tests)
        self.generate_tests_button.pack(pady=5)

        self.read_commands_button = tk.Button(root, text="Read Commands from Firmware", command=self.read_commands)
        self.read_commands_button.pack(pady=5)

        self.run_tests_button = tk.Button(root, text="Run Tests", command=self.run_tests)
        self.run_tests_button.pack(pady=5)

        self.output_label = tk.Label(root, text="", fg="blue")
        self.output_label.pack(pady=5)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Firmware Packages", "*.rpm *.img *.zip")])
        if file_path:
            self.selected_file = file_path
            self.output_label.config(text=f"Selected file: {file_path}")

    def select_csharp_files(self):
        files = filedialog.askopenfilenames(filetypes=[("C# Source Files", "*.cs")])
        if files:
            self.selected_csharp_files = list(files)
            self.output_label.config(text=f"Selected C# Files: {len(self.selected_csharp_files)} files")

    def generate_tests(self):
        if not self.selected_file and not self.selected_csharp_files:
            messagebox.showerror("Error", "Please select a firmware file or C# source files first.")
            return

        with app.app_context():
            blueprints, commands = [], []

            if self.selected_file:
                extracted_files = process_firmware_package(self.selected_file)
                if not extracted_files:
                    messagebox.showerror("Error", "Failed to extract firmware files.")
                    return

                emulator = EmulatorService()
                blueprints = emulator.fetch_blueprints().get("blueprints", [])
                commands = emulator.fetch_commands_from_firmware(self.selected_file)

                if not commands:
                    messagebox.showerror("Error", "No commands found in firmware.")
                    return

            test_generator = TestGenerator(blueprints=blueprints, commands=commands, csharp_files=self.selected_csharp_files)
            self.generated_tests = test_generator.generate_test_suite()
            messagebox.showinfo("Success", f"Tests generated successfully!\nSaved to: {test_generator.output_dir}")

    def read_commands(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a firmware file first.")
            return

        with app.app_context():
            hardware_service = HardwareService()
            device_list = hardware_service.list_devices().get("devices", [])

            if not device_list:
                messagebox.showerror("Error", "No devices detected.")
                return

            commands = []
            for device in device_list:
                device_id = device["id"]
                commands.extend(hardware_service.get_device_status(device_id).get("status", {}).get("metadata", {}).get("commands", []))

            if commands:
                messagebox.showinfo("Commands Found", f"Commands Extracted: {json.dumps(commands, indent=2)}")
            else:
                messagebox.showerror("Error", "No commands found in detected devices.")

    def run_tests(self):
        if not self.generated_tests:
            messagebox.showerror("Error", "Please generate tests first.")
            return

        with app.app_context():
            mqtt_service = MQTTService("localhost")
            mqtt_service.connect()

            for test_file in self.generated_tests:
                with open(test_file, "r") as file:
                    test_content = file.read()
                    topic = "hardware/tests"
                    payload = {"test_file": os.path.basename(test_file), "test_content": test_content}
                    mqtt_service.publish(topic, payload)

            messagebox.showinfo("Tests Sent", "Tests have been published to the hardware for execution.")


if __name__ == "__main__":
    with app.app_context():
        root = tk.Tk()
        app_ui = FirmwareTestUI(root)
        root.mainloop()
