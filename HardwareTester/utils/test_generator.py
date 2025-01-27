import json
import os
from datetime import datetime

class TestGenerator:
    def __init__(self, blueprints, commands, output_dir="generated_tests"):
        """
        Initialize the test generator.
        :param blueprints: List of blueprints containing configurations and hardware metadata.
        :param commands: List of supported commands and their parameters.
        :param output_dir: Directory to save generated test files.
        """
        self.blueprints = blueprints
        self.commands = commands
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_test_suite(self):
        """
        Generate test suites for all blueprints.
        :return: List of paths to generated test files.
        """
        test_files = []
        for blueprint in self.blueprints:
            test_file = self._generate_test_file(blueprint)
            test_files.append(test_file)
        return test_files

    def _generate_test_file(self, blueprint):
        """
        Generate a test file for a specific blueprint.
        :param blueprint: Blueprint data.
        :return: Path to the generated test file.
        """
        test_name = blueprint["name"].replace(" ", "_").lower()
        file_path = os.path.join(self.output_dir, f"{test_name}_test.py")

        test_code = self._generate_test_code(blueprint)
        with open(file_path, "w") as test_file:
            test_file.write(test_code)

        print(f"Generated test for {blueprint['name']}: {file_path}")
        return file_path

    def _generate_test_code(self, blueprint):
        """
        Generate Python code for the test file.
        :param blueprint: Blueprint data.
        :return: Python test code as a string.
        """
        test_code = [
            "import unittest",
            "import requests",
            "",
            f"# Test suite for {blueprint['name']}",
            f"class Test{blueprint['name'].replace(' ', '')}(unittest.TestCase):",
            "    BASE_URL = 'http://localhost:5000'",  # Example API URL
            "",
            "    def setUp(self):",
            "        \"\"\"Set up the test environment.\"\"\"",
            f"        self.blueprint = {json.dumps(blueprint, indent=8)}",
            "",
        ]

        for command in self.commands:
            method_name = command["name"].lower()
            test_code.extend(self._generate_test_method(blueprint, command, method_name))

        test_code.append("")
        test_code.append("if __name__ == '__main__':")
        test_code.append("    unittest.main()")
        return "\n".join(test_code)

    def _generate_test_method(self, blueprint, command, method_name):
        """
        Generate a test method for a specific command.
        :param blueprint: Blueprint data.
        :param command: Command metadata.
        :param method_name: Name of the test method.
        :return: List of lines for the test method code.
        """
        method = [
            f"    def test_{method_name}(self):",
            "        \"\"\"Automatically generated test.\"\"\"",
            f"        url = f\"{{self.BASE_URL}}/api/{blueprint['name'].replace(' ', '_').lower()}/{command['name'].lower()}\"",
        ]

        if "parameters" in command:
            params = ", ".join([f"{param['name']}={param['type']}" for param in command["parameters"]])
            method.append(f"        data = {{{params}}}")
            method.append("        response = requests.post(url, json=data)")
        else:
            method.append("        response = requests.post(url)")

        method.extend([
            "        self.assertEqual(response.status_code, 200)",
            "        self.assertIn('success', response.json())",
            "        print(f\"Test passed for command: {command['name']}\")",
            "",
        ])
        return method

    def _generate_test_content(self, blueprint_name):
        test_cases = []
        for command in self.commands:
            if command["type"] == "clickable":
                test_cases.append(self._generate_click_test(command))
            elif command["type"] == "input":
                test_cases.append(self._generate_input_test(command))
        return "\n".join(test_cases)

    def _generate_click_test(self, command):
        return f"""
def test_{command['name'].lower()}(self):
    response = self.emulator.send_command("{command['name']}")
    self.assertEqual(response.status_code, 200)
    self.assertIn("{command['expected_output']}", response.json()["message"])
"""

    def _generate_input_test(self, command):
        return f"""
def test_{command['name'].lower()}_input(self):
    response = self.emulator.send_command("{command['name']}", payload={{"value": "test_input"}})
    self.assertEqual(response.status_code, 200)
    self.assertIn("{command['expected_output']}", response.json()["message"])
"""

###
#
#flask generate-tests --method=firmware --output-dir="tests/firmware"
#
#flask generate-tests --method=mqtt --mqtt-topic="hardware/commands" --output-dir="tests/mqtt"
###    