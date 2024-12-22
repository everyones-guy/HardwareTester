import argparse
from HardwareTester import create_app, socketio
from HardwareTester.utils import initialize_database

def main():
    parser = argparse.ArgumentParser(description="Run the Hardware Tester server.")
    parser.add_argument("--config", help="Configuration to use (default: development)", default="development")
    args = parser.parse_args()

    app = create_app(args.config)
    socketio.run(app, host="0.0.0.0", port=5000)
    
    db_manager = initialize_database()
    # Inspect database schema
    db_manager.inspect_database()

if __name__ == "__main__":
    main()
