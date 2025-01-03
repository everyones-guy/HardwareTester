import os
import importlib.util
from tkinter import Tk, Frame, Listbox, Text, Label, Entry, Button, END, PanedWindow
from faker import Faker
from flask import render_template_string
from flask.cli import with_appcontext
from HardwareTester import create_app, db

# Initialize Flask app
app = create_app('testing')
fake = Faker()

# Paths
TESTS_FOLDER = os.path.join(os.getcwd(), 'tests')
SERVICES_FOLDER = os.path.join(os.getcwd(), 'HardwareTester', 'services')
VIEWS_FOLDER = os.path.join(os.getcwd(), 'HardwareTester', 'views')

# Ensure the tests folder exists
os.makedirs(TESTS_FOLDER, exist_ok=True)


class TestRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Test Runner - GUI")

        # Discover tests
        self.all_tests = self.discover_tests()
        self.filtered_tests = self.all_tests.copy()

        # PanedWindow for resizable sidebar
        self.paned_window = PanedWindow(root, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True)

        # Sidebar
        self.sidebar = Frame(self.paned_window, width=200, bg='lightgrey')
        self.paned_window.add(self.sidebar)

        # Search Bar and Button
        self.search_label = Label(self.sidebar, text="Search Tests:", bg='lightgrey', font=("Arial", 12))
        self.search_label.pack(pady=5)

        self.search_entry = Entry(self.sidebar, width=25)
        self.search_entry.pack(pady=5)

        self.search_button = Button(self.sidebar, text="Search", command=self.search_tests)
        self.search_button.pack(pady=5)

        self.reset_button = Button(self.sidebar, text="Reset", command=self.reset_search)
        self.reset_button.pack(pady=5)

        # Test List
        self.sidebar_label = Label(self.sidebar, text="Tests", bg='lightgrey', font=("Arial", 14))
        self.sidebar_label.pack(pady=10)

        self.test_list = Listbox(self.sidebar)
        self.test_list.pack(fill='both', expand=True, padx=10, pady=10)
        self.populate_test_list()

        self.test_list.bind('<<ListboxSelect>>', self.run_selected_test)

        # Main Area
        self.main_area = Frame(self.paned_window, bg='white')
        self.paned_window.add(self.main_area)

        self.output_label = Label(self.main_area, text="Test Output", font=("Arial", 14), bg='white')
        self.output_label.pack(pady=10)

        self.output_text = Text(self.main_area, wrap='word', bg='lightyellow', fg='black', font=("Arial", 12))
        self.output_text.pack(fill='both', expand=True, padx=10, pady=10)

        # Initialize the database
        self.init_db()

    def discover_tests(self):
        """Discover all test scripts in the tests folder, and mock missing ones."""
        tests = []

        # Check for service and view test files
        for folder, prefix in [(SERVICES_FOLDER, 'service'), (VIEWS_FOLDER, 'view')]:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    if file.endswith('.py'):
                        base_name = os.path.splitext(file)[0]
                        test_file = os.path.join(TESTS_FOLDER, f'test_{base_name}.py')
                        if not os.path.exists(test_file):
                            self.mock_test_file(test_file, prefix, base_name)
                        tests.append(f'test_{base_name}.py')

        # Include existing test files in the tests folder
        for test in os.listdir(TESTS_FOLDER):
            if test.endswith('.py') and test not in tests:
                tests.append(test)

        return tests

    def mock_test_file(self, test_file, test_type, base_name):
        """Mock a test file dynamically if missing."""
        mock_test_content = f"""
from flask import render_template_string

# Mock {test_type.capitalize()} Function
def {test_type}_function(data):
    return render_template_string('<h1>{{{{ title }}}}</h1><p>{{{{ description }}}}</p>', **data)

# Test Function
def run_test(fake):
    mock_data = {{
        "title": fake.word().title(),
        "description": fake.sentence(),
    }}
    return {test_type}_function(mock_data)
"""
        with open(test_file, 'w') as f:
            f.write(mock_test_content)

    def init_db(self):
        """Initialize the database."""
        with app.app_context():
            try:
                db.create_all()
                self.output_text.insert(END, "Database initialized successfully.\n")
            except Exception as e:
                self.output_text.insert(END, f"Error initializing database: {e}\n")

    def populate_test_list(self):
        """Populate the test list with filtered tests."""
        self.test_list.delete(0, END)
        for test in self.filtered_tests:
            self.test_list.insert(END, test)

    def search_tests(self):
        """Filter the tests based on the search query."""
        query = self.search_entry.get().lower()
        self.filtered_tests = [test for test in self.all_tests if query in test.lower()]
        self.populate_test_list()

    def reset_search(self):
        """Reset the test list to show all tests."""
        self.search_entry.delete(0, END)
        self.filtered_tests = self.all_tests.copy()
        self.populate_test_list()

    def run_selected_test(self, event):
        """Run the selected test."""
        selection = self.test_list.curselection()
        if not selection:
            return

        test_file = self.test_list.get(selection[0])
        test_path = os.path.join(TESTS_FOLDER, test_file)

        try:
            self.output_text.delete(1.0, END)
            self.output_text.insert(END, f"Running test: {test_file}\n")

            # Dynamically import the test module
            spec = importlib.util.spec_from_file_location("test_module", test_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)

            # Execute the test function within app.app_context()
            with app.app_context():
                if hasattr(test_module, "run_test"):
                    output = test_module.run_test(fake)
                    self.output_text.insert(END, f"Test Output:\n{output}\n")
                else:
                    self.output_text.insert(END, "Error: No 'run_test' function found in the test file.\n")
        except Exception as e:
            self.output_text.insert(END, f"Error running test: {e}\n")


# Run the application
if __name__ == "__main__":
    root = Tk()
    app = TestRunnerApp(root)
    root.geometry("800x600")
    root.mainloop()