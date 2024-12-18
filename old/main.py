from HardwareTester import app, socketio
from HardwareTester.utils.testing import run_pytest
from HardwareTester.utils.hardware_manager import print_system_info
from HardwareTester.utils.auto_deploy import build_project, deploy_project
from HardwareTester.utils.utils import confirm_action

def start_web_app():
    """Start the Flask web application."""
    print("Starting the Hardware Tester Web Application...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

def start_cli_tool():
    """Start the CLI interface."""
    print("Welcome to the Hardware Tester CLI Tool!")

    while True:
        print("\nMenu:")
        print("1. Run Tests")
        print("2. View System Info")
        print("3. Build Project")
        print("4. Deploy Project")
        print("5. Exit")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            output = run_pytest()
            print(f"Test Output:\n{output}")
        elif choice == "2":
            print_system_info()
        elif choice == "3":
            if confirm_action("Are you sure you want to build the project?"):
                build_project()
        elif choice == "4":
            if confirm_action("Are you sure you want to deploy the project?"):
                deploy_project()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    print("Hardware Tester Tool")
    print("1. Start Web Application")
    print("2. Start CLI Tool")
    choice = input("Enter your choice: ").strip()

    if choice == "1":
        start_web_app()
    elif choice == "2":
        start_cli_tool()
    else:
        print("Invalid choice. Exiting...")

if __name__ == "__main__":
    main()
