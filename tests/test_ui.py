import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from HardwareTester.utils.firmware_utils import process_firmware_package
from HardwareTester.utils.test_generator import TestGenerator
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.services.hardware_service import HardwareService
from HardwareTester.services.mqtt_service import MQTTService
from flask import Flask
from HardwareTester import create_app  # Ensure this exists in your project

app = create_app()


class FirmwareTestUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Firmware & C# Testing UI")

        self.selected_file = None
        self.selected_csharp_file = None
        self.generated_tests = []

        # UI Components
        self.create_widgets()

    def create_widgets(self):
        """Set up UI components."""
        self.file_label = tk.Label(self.root, text="Select Firmware File or C# File:")
        self.file_label.pack(pady=5)

        self.file_button = tk.Button(self.root, text="Browse Firmware", command=self.select_file)
        self.file_button.pack(pady=5)

        self.cs_file_button = tk.Button(self.root, text="Browse C# File", command=self.select_csharp_file)
        self.cs_file_button.pack(pady=5)

        self.generate_tests_button = tk.Button(self.root, text="Generate Tests", command=self.generate_tests)
        self.generate_tests_button.pack(pady=5)

        self.read_commands_button = tk.Button(self.root, text="Read Commands from Firmware", command=self.read_commands)
        self.read_commands_button.pack(pady=5)

        self.run_tests_button = tk.Button(self.root, text="Run Tests", command=self.run_tests)
        self.run_tests_button.pack(pady=5)

        self.output_label = tk.Label(self.root, text="", fg="blue")
        self.output_label.pack(pady=5)

    def select_file(self):
        """Select a firmware package (.rpm, .img, .zip)."""
        file_path = filedialog.askopenfilename(filetypes=[("Firmware Packages", "*.rpm *.img *.zip")])
        if file_path:
            self.selected_file = file_path
            self.output_label.config(text=f"Selected Firmware: {file_path}")

    def select_csharp_file(self):
        """Select a C# source file (.cs) for test generation."""
        file_path = filedialog.askopenfilename(filetypes=[("C# Source Files", "*.cs")])
        if file_path:
            self.selected_csharp_file = file_path
            self.output_label.config(text=f"Selected C# File: {file_path}")

    def generate_tests(self):
        """Generate tests for the selected firmware or C# source file."""
        if not self.selected_file and not self.selected_csharp_file:
            messagebox.showerror("Error", "Please select a firmware or C# file first.")
            return

        with app.app_context():
            # Process firmware files
            extracted_files = process_firmware_package(self.selected_file) if self.selected_file else []
            
            # Extract test data for firmware
            emulator = EmulatorService()
            blueprints = emulator.fetch_blueprints().get("blueprints", []) if extracted_files else []
            commands = emulator.fetch_commands_from_firmware(self.selected_file) if extracted_files else []

            # Generate tests
            test_generator = TestGenerator(blueprints=blueprints, commands=commands, csharp_files=[self.selected_csharp_file] if self.selected_csharp_file else [])
            self.generated_tests = test_generator.generate_test_suite()

            if self.generated_tests:
                messagebox.showinfo("Success", f"Tests generated successfully!\nSaved to: {test_generator.output_dir}")
            else:
                messagebox.showerror("Error", "No tests were generated.")

    def read_commands(self):
        """Read commands from firmware devices."""
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
        """Run generated tests by publishing them to MQTT."""
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
