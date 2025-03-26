import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from Hardware_Tester_App.utils.firmware_utils import process_firmware_package
from Hardware_Tester_App.utils.test_generator import TestGenerator
from Hardware_Tester_App.utils.source_code_analyzer import SourceCodeAnalyzer
from Hardware_Tester_App.services.emulator_service import EmulatorService
from Hardware_Tester_App.services.hardware_service import HardwareService
from Hardware_Tester_App.services.mqtt_service import MQTTService
from flask import Flask

# Initialize Flask app
from Hardware_Tester_App import create_app
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

        self.generate_tests_button = tk.Button(root, text="Extract & Generate Tests", command=self.generate_tests)
        self.generate_tests_button.pack(pady=5)

        self.read_commands_button = tk.Button(root, text="Read Commands from Firmware", command=self.read_commands)
        self.read_commands_button.pack(pady=5)

        self.run_tests_button = tk.Button(root, text="Run NUnit Tests", command=self.run_nunit_tests)
        self.run_tests_button.pack(pady=5)

        self.output_label = tk.Label(root, text="", fg="blue")
        self.output_label.pack(pady=5)

        # Scrollable Log Output
        self.log_output = scrolledtext.ScrolledText(root, width=80, height=20)
        self.log_output.pack(pady=10)

    def log(self, message):
        """Updates the log output in the UI."""
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)

    def select_file(self):
        """Allows user to select a firmware package (RPM, IMG, ZIP)."""
        file_path = filedialog.askopenfilename(filetypes=[("Firmware Packages", "*.rpm *.img *.zip")])
        if file_path:
            self.selected_file = file_path
            self.selected_csharp_files = []  # Reset C# selection
            self.output_label.config(text=f"Selected Firmware: {file_path}")

    def select_csharp_files(self):
        """Allows user to select standalone C# files."""
        files = filedialog.askopenfilenames(filetypes=[("C# Source Files", "*.cs")])
        if files:
            self.selected_csharp_files = list(files)
            self.selected_file = None  # Reset Firmware selection
            self.output_label.config(text=f"Selected {len(self.selected_csharp_files)} C# files")

    def generate_tests(self):
        """Extracts firmware if needed, analyzes C# files, and generates tests."""
        if not self.selected_file and not self.selected_csharp_files:
            messagebox.showerror("Error", "Please select a firmware file or C# source files first.")
            return

        extracted_csharp_files = []

        with app.app_context():
            if self.selected_file:
                self.log("Extracting firmware...")
                extracted_csharp_files = process_firmware_package(self.selected_file)

                if not extracted_csharp_files:
                    messagebox.showerror("Error", "No C# files found in extracted firmware.")
                    return

                self.log(f"Found {len(extracted_csharp_files)} C# files in extracted firmware.")

            elif self.selected_csharp_files:
                self.log("Using selected C# files directly.")
                extracted_csharp_files = self.selected_csharp_files

            # Analyze C# files and generate NUnit tests
            self.log("Generating NUnit tests...")
            analyzer = SourceCodeAnalyzer()
            functions = []
            for cs_file in extracted_csharp_files:
                functions.extend(analyzer.parse_file(cs_file, "c_sharp"))

            if not functions:
                messagebox.showerror("Error", "No functions detected in C# files.")
                return

            test_generator = TestGenerator(csharp_files=extracted_csharp_files)
            self.generated_tests = test_generator.generate_test_suite()

            self.log(f"Generated {len(self.generated_tests)} NUnit test files.")
            messagebox.showinfo("Success", f"Tests generated successfully!\nSaved to: {test_generator.output_dir}")

    def read_commands(self):
        """Extracts available commands from firmware."""
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a firmware file first.")
            return

        with app.app_context():
            self.log("Reading commands from firmware...")
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
                self.log(f"Extracted {len(commands)} commands.")
            else:
                messagebox.showerror("Error", "No commands found in detected devices.")

    def run_nunit_tests(self):
        """Runs the generated NUnit tests using `dotnet test`."""
        if not self.generated_tests:
            messagebox.showerror("Error", "Please generate tests first.")
            return

        with app.app_context():
            self.log("Running NUnit tests...")
            test_generator = TestGenerator()
            results = test_generator.run_nunit_tests()

            if results:
                self.log("NUnit Test Results:\n" + results)
            else:
                self.log("NUnit tests failed to execute.")


if __name__ == "__main__":
    with app.app_context():
        root = tk.Tk()
        app_ui = FirmwareTestUI(root)
        root.mainloop()
