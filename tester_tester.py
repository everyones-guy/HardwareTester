import os
from tkinter import Tk, Frame, Listbox, Button, Text, Label, Scrollbar, END, VERTICAL
from tkinter.ttk import Notebook
from flask import Flask, render_template_string
from faker import Faker
from HardwareTester import create_app

# Initialize Flask app
app = create_app('testing')
fake = Faker()


class TestRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Tester GUI")

        # Configure root window for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main Notebook (Tabs)
        self.notebook = Notebook(root)
        self.notebook.grid(sticky="nsew")

        # Tabs
        self.tabs = {
            "Configurations": self.create_tab("Configurations"),
            "Emulation": self.create_tab("Emulation"),
            "Services": self.create_tab("Services"),
            "Views": self.create_tab("Views"),
            "Tests": self.create_tab("Tests"),
            "Firmware": self.create_tab("Firmware"),
            "HTML Templates": self.create_tab("HTML Templates"),
        }

        # Populate tabs dynamically
        self.populate_tab("Configurations", self.discover_configurations())
        self.populate_tab("Emulation", self.discover_emulations())
        self.populate_tab("Services", self.discover_services())
        self.populate_tab("Views", self.discover_views())
        self.populate_tab("Tests", self.discover_tests())
        self.populate_tab("Firmware", self.discover_firmware())
        self.populate_tab("HTML Templates", self.discover_html_templates())

    def create_tab(self, name):
        """Create a new tab with a list and output section."""
        tab_frame = Frame(self.notebook)
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(1, weight=1)

        self.notebook.add(tab_frame, text=name)

        # Sidebar for list
        list_frame = Frame(tab_frame, width=200, bg='lightgrey')
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)

        list_label = Label(list_frame, text=name, bg='lightgrey', font=("Arial", 14))
        list_label.pack(pady=5)

        scrollbar = Scrollbar(list_frame, orient=VERTICAL)
        scrollbar.pack(side="right", fill="y")

        listbox = Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=listbox.yview)

        listbox.bind('<<ListboxSelect>>', lambda event, tab=name: self.handle_selection(tab, event))

        # Main output area
        output_frame = Frame(tab_frame, bg='white')
        output_frame.grid(row=0, column=1, sticky="nsew")
        output_frame.grid_rowconfigure(1, weight=1)

        output_label = Label(output_frame, text=f"{name} Output", bg='white', font=("Arial", 14))
        output_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        output_text = Text(output_frame, wrap='word', bg='lightyellow', fg='black', font=("Arial", 12))
        output_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        return {"listbox": listbox, "output_text": output_text}

    def populate_tab(self, tab_name, items):
        """Populate a tab with items."""
        if tab_name not in self.tabs:
            return
        listbox = self.tabs[tab_name]["listbox"]
        listbox.delete(0, END)
        for item in items:
            listbox.insert(END, item)

    def handle_selection(self, tab_name, event):
        """Handle item selection in a tab."""
        selection = self.tabs[tab_name]["listbox"].curselection()
        output_text = self.tabs[tab_name]["output_text"]

        if not selection:
            return

        selected_item = self.tabs[tab_name]["listbox"].get(selection[0])
        output_text.delete(1.0, END)
        output_text.insert(END, f"Selected: {selected_item} in {tab_name}\n")

        # Handle specific actions based on tab and item
        if tab_name == "Configurations":
            self.load_configuration(selected_item, output_text)
        elif tab_name == "Emulation":
            self.add_emulation(selected_item, output_text)
        elif tab_name == "Firmware":
            self.check_firmware(selected_item, output_text)
        elif tab_name == "HTML Templates":
            self.preview_html(selected_item, output_text)
        else:
            output_text.insert(END, f"Processing {selected_item} in {tab_name}\n")

    def load_configuration(self, configuration, output_text):
        """Load the selected configuration."""
        # Placeholder: Replace with actual configuration loading logic
        output_text.insert(END, f"Loading configuration: {configuration}\n")

    def add_emulation(self, emulation, output_text):
        """Add a new emulation."""
        # Placeholder: Replace with actual emulation logic
        if not emulation:
            emulation = "Default Emulation"
        output_text.insert(END, f"Adding emulation: {emulation}\n")

    def check_firmware(self, firmware, output_text):
        """Check the selected firmware."""
        # Placeholder: Replace with actual firmware loading logic
        output_text.insert(END, f"Loading firmware: {firmware} for validation\n")

    def preview_html(self, template_name, output_text):
        """Preview the selected HTML template."""
        try:
            template_dir = os.path.join(os.path.dirname(__file__), "HardwareTester/templates")
            template_path = os.path.join(template_dir, template_name)
            if not os.path.exists(template_path):
                output_text.insert(END, f"Error: Template {template_name} not found in {template_dir}.\n")
                return

            with open(template_path, "r") as f:
                html_content = f.read()

            with app.app_context():
                rendered_html = render_template_string(html_content)
                output_text.insert(END, f"Rendered HTML for {template_name}:\n{rendered_html}\n")
        except Exception as e:
            output_text.insert(END, f"Error rendering HTML: {e}\n")

    def discover_configurations(self):
        """Discover all available configurations."""
        return ["Configuration 1", "Configuration 2", "Default Configuration"]

    def discover_emulations(self):
        """Discover all available emulations."""
        return ["Emulation 1", "Emulation 2", "Default Emulation"]

    def discover_tests(self):
        """Discover all test scripts in subfolders of the tests directory."""
        return self._discover_files("                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   tests", ".py")

    def discover_services(self):
        """Discover all services in the services directory."""
        return self._discover_files("HardwareTester/services", ".py")

    def discover_views(self):
        """Discover all views in the views directory."""
        return self._discover_files("HardwareTester/views", ".py")

    def discover_firmware(self):
        """Discover all firmware in the firmware directory."""
        return self._discover_files("firmware", ".bin")

    def discover_html_templates(self):
        """Discover all HTML templates in the templates directory."""
        return self._discover_files("HardwareTester/templates", ".html")

    def _discover_files(self, directory, extension):
        """Helper to discover files with a specific extension in a directory."""
        directory_path = os.path.join(os.path.dirname(__file__), directory)
        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return []
        return [f for f in os.listdir(directory_path) if f.endswith(extension)]
    
    def discover_tests(self):
        """Discover all test scripts in subfolders of the tests directory."""
        test_files = []
        test_dir = "tests"
        for root, _, files in os.walk(test_dir):
            for file in files:
                if file.endswith(".py") and file not in ["__init__.py"]:
                    relative_path = os.path.join(root, file)
                    test_files.append(os.path.relpath(relative_path, start=test_dir))
        return test_files

    def discover_services(self):
        """Discover all services in the services directory."""
        service_dir = os.path.join("your_app", "services")
        return self._discover_py_files(service_dir)

    def discover_views(self):
        """Discover all views in the views directory."""
        view_dir = os.path.join("your_app", "views")
        return self._discover_py_files(view_dir)

    def discover_html_templates(self):
        """Discover all HTML templates in the templates directory."""
        template_dir = "templates"
        return [f for f in os.listdir(template_dir) if f.endswith(".html")]

    def _discover_py_files(self, directory):
        """Helper to discover Python files in a directory."""
        py_files = []
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith(".py") and file != "__init__.py":
                    py_files.append(file)
        else:
            print(f"Directory not found: {directory}")
        return py_files


# Run the application
if __name__ == "__main__":
    root = Tk()
    app = TestRunnerApp(root)
    root.geometry("1000x700")
    root.mainloop()
