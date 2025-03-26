import json
import os
from dotenv import load_dotenv
from datetime import datetime
from HardwareTester.utils.source_code_analyzer import SourceCodeAnalyzer

load_dotenv()

base_url = os.getenv("BASE_URL", "http://localhost:5000/api")

class TestGenerator:
    def __init__(self, blueprints=None, commands=None, csharp_files=None, output_dir="generated_tests"):
        """
        Initialize the test generator.
        :param blueprints: List of blueprints containing configurations and hardware metadata.
        :param commands: List of supported API commands.
        :param csharp_files: List of C# source files to analyze.
        :param output_dir: Directory to save generated test files.
        """
        self.blueprints = blueprints or []
        self.commands = commands or []
        self.csharp_files = csharp_files or []
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_test_suite(self):
        """
        Generate test suites for all blueprints and C# files.
        :return: List of paths to generated test files.
        """
        test_files = []

        # Generate Python tests for API blueprints
        for blueprint in self.blueprints:
            test_files.append(self._generate_python_test_file(blueprint))

        # Generate C# tests for extracted functions
        for cs_file in self.csharp_files:
            test_files.append(self._generate_csharp_test_file(cs_file))

        return test_files

    def _generate_python_test_file(self, blueprint):
        """
        Generate a Python test file for API testing.
        :param blueprint: Blueprint data.
        :return: Path to the generated test file.
        """
        test_name = blueprint["name"].replace(" ", "_").lower()
        file_path = os.path.join(self.output_dir, f"{test_name}_test.py")

        test_code = self._generate_python_test_code(blueprint)
        with open(file_path, "w") as test_file:
            test_file.write(test_code)

        print(f"Generated Python test for {blueprint['name']}: {file_path}")
        return file_path

    def _generate_python_test_code(self, blueprint):
        """
        Generate Python unit test code for API testing.
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
            test_code.extend(self._generate_python_test_method(blueprint, command, method_name))

        test_code.append("if __name__ == '__main__':")
        test_code.append("    unittest.main()")
        return "\n".join(test_code)

    def _generate_python_test_method(self, blueprint, command, method_name):
        """
        Generate a test method for a specific API command.
        :param blueprint: API blueprint data.
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
            params = ", ".join([f"'{param['name']}': 'test_value'" for param in command["parameters"]])
            method.append(f"        data = {{{params}}}")
            method.append("        response = requests.post(url, json=data)")
        else:
            method.append("        response = requests.post(url)")

        method.extend([
            "        self.assertEqual(response.status_code, 200)",
            "        self.assertIn('success', response.json())",
            f"        print(\"Test passed for {command['name']}\")",
            "",
        ])
        return method

    def _generate_csharp_test_file(self, cs_file):
        """
        Generate a C# NUnit test file for the given C# source file.
        :param cs_file: Path to the C# source file.
        :return: Path to the generated C# test file.
        """
        test_name = os.path.basename(cs_file).replace(".cs", "_Test")
        file_path = os.path.join(self.output_dir, f"{test_name}.cs")

        analyzer = SourceCodeAnalyzer()
        functions = analyzer.parse_file(cs_file, "c_sharp")

        if not functions:
            print(f"Skipping {cs_file}: No functions found.")
            return None

        test_code = self._generate_csharp_test_code(test_name, functions)

        with open(file_path, "w") as test_file:
            test_file.write(test_code)

        print(f"Generated C# test for {cs_file}: {file_path}")
        return file_path

    def _generate_csharp_test_code(self, test_class_name, functions):
        """
        Generate C# NUnit test class code.
        :param test_class_name: Name of the test class.
        :param functions: Extracted C# functions.
        :return: C# test code as a string.
        """
        test_code = [
            "using NUnit.Framework;",
            "namespace GeneratedTests {",
            f"    [TestFixture]",
            f"    public class {test_class_name} {{",
        ]

        for function in functions:
            method_name = function["name"]
            parameters = ", ".join([p.split()[-1] for p in function["parameters"]]) if function["parameters"] else ""

            test_code.append(f"        [Test]")
            test_code.append(f"        public void {method_name}_Test() {{")
            test_code.append(f"            // Arrange")
            test_code.append(f"            var obj = new YourClass();")

            if function["parameters"]:
                test_code.append(f"            var result = obj.{method_name}({parameters});")
            else:
                test_code.append(f"            var result = obj.{method_name}();")

            test_code.append(f"            // Act & Assert")
            test_code.append(f"            Assert.NotNull(result);")
            test_code.append("        }\n")

        test_code.append("    }\n}")
        return "\n".join(test_code)


# Example Usage
if __name__ == "__main__":
    # Example data
    api_blueprints = [
        {"name": "UserAPI"},
        {"name": "DeviceAPI"},
    ]
    
    api_commands = [
        {"name": "createUser", "parameters": [{"name": "username", "type": "string"}]},
        {"name": "getDeviceStatus", "parameters": []},
    ]

    csharp_files = ["example.cs"]  # Replace with actual C# files

    test_gen = TestGenerator(blueprints=api_blueprints, commands=api_commands, csharp_files=csharp_files)
    test_files = test_gen.generate_test_suite()

    print("Generated Test Files:", test_files)
