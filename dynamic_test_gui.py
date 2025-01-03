
import os
import importlib.util
from tkinter import Tk, Frame, Listbox, Button, Text, Label, END
from faker import Faker
from flask import Flask, render_template_string
from your_app import create_app

# Initialize Flask app
app = create_app('testing')
fake = Faker()

# GUI Application
class TestRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Test Runner - GUI")

        # Tests folder
        self.tests_folder = os.path.join(os.getcwd(), 'tests')
        self.tests = self.discover_tests()

        # Sidebar
        self.sidebar = Frame(root, width=200, bg='lightgrey')
        self.sidebar.pack(side='left', fill='y')

        self.sidebar_label = Label(self.sidebar, text="Tests", bg='lightgrey', font=("Arial", 14))
        self.sidebar_label.pack(pady=10)

        self.test_list = Listbox(self.sidebar)
        self.test_list.pack(fill='y', expand=True, padx=10, pady=10)

        for test in self.tests:
            self.test_list.insert(END, test)

        self.test_list.bind('<<ListboxSelect>>', self.run_selected_test)

        # Main Area
        self.main_area = Frame(root, bg='white')
        self.main_area.pack(side='right', fill='both', expand=True)

        self.output_label = Label(self.main_area, text="Test Output", font=("Arial", 14), bg='white')
        self.output_label.pack(pady=10)

        self.output_text = Text(self.main_area, wrap='word', bg='lightyellow', fg='black', font=("Arial", 12))
        self.output_text.pack(fill='both', expand=True, padx=10, pady=10)

    def discover_tests(self):
        """Discover all test scripts in the tests folder."""
        if not os.path.exists(self.tests_folder):
            os.makedirs(self.tests_folder)
        return [f for f in os.listdir(self.tests_folder) if f.endswith('.py')]

    def run_selected_test(self, event):
        """Run the selected test."""
        selection = self.test_list.curselection()
        if not selection:
            return

        test_file = self.test_list.get(selection[0])
        test_path = os.path.join(self.tests_folder, test_file)

        with app.app_context():
            try:
                self.output_text.delete(1.0, END)
                self.output_text.insert(END, f"Running test: {test_file}\n")

                # Dynamically import the test module
                spec = importlib.util.spec_from_file_location("test_module", test_path)
                test_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(test_module)

                # Execute the test function
                if hasattr(test_module, "run_test"):
                    output = test_module.run_test(fake)
                    self.output_text.insert(END, f"Test Output:\n{output}\n")
                else:
                    self.output_text.insert(END, "Error: No 'run_test' function found in the test file.\n")
            except Exception as e:
                self.output_text.insert(END, f"Error running test: {e}\n")

# Example Test Template
def generate_test_template():
    """Generate an example test template in the tests folder."""
    test_template = """
from flask import render_template_string

# Mock View Function
def view_function(data):
    return render_template_string('<h1>{{ title }}</h1><p>{{ description }}</p>', **data)

# Test Function
def run_test(fake):
    mock_data = {
        "title": fake.word().title(),
        "description": fake.sentence(),
    }
    return view_function(mock_data)
"""
    test_file = os.path.join(os.getcwd(), 'tests', 'example_test.py')
    if not os.path.exists(test_file):
        with open(test_file, 'w') as f:
            f.write(test_template)

# Run the application
if __name__ == "__main__":
    generate_test_template()
    root = Tk()
    app = TestRunnerApp(root)
    root.geometry("800x600")
    root.mainloop()
