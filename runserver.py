import argparse
from HardwareTester import create_app
from HardwareTester.extensions import socketio, migrate
from cli import register_commands

def main():
    parser = argparse.ArgumentParser(description="Run the Hardware Tester server.")
    parser.add_argument("--config", help="Configuration to use (default: development)", default="development")
    args = parser.parse_args()

    app = create_app(args.config)
    migrate.init_app(app, db)  # Ensure migration is set up

    register_commands(app)  # Register custom commands
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
