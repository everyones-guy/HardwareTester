import argparse
from HardwareTester import create_app
from HardwareTester.extensions import socketio
from cli import register_commands

def main():
    parser = argparse.ArgumentParser(description="Run the Hardware Tester server.")
    parser.add_argument("--config", help="Configuration to use (default: development)", default="development")
    args = parser.parse_args()

    app = create_app(args.config)
    register_commands(app)  # Register custom commands
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
