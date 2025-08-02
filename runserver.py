import argparse
import os
import platform
from dotenv import load_dotenv
from flask_socketio import SocketIO
from Hardware_Tester_App import create_app
from Hardware_Tester_App.extensions import socketio  # Importing socketio instance

load_dotenv()

def is_wsl_environment():
    """Check if running in Windows Subsystem for Linux (WSL)."""
    try:
        if platform.system() == "Linux":
            with open("/proc/version", "r") as f:
                return "microsoft" in f.read().lower()
    except Exception:
        pass
    return False

def main():
    global socketio  # Explicitly mark it as global to avoid UnboundLocalError

    parser = argparse.ArgumentParser(description="Run the Hardware Tester server.")
    parser.add_argument("--config", help="Configuration to use (default: development)", default="development")
    parser.add_argument("--host", help="Host IP address (default: 0.0.0.0)", default="0.0.0.0")
    parser.add_argument("--port", help="Port number (default: 5000)", type=int, default=5000)
    parser.add_argument("--debug", help="Enable debug mode", action="store_true")

    args = parser.parse_args()
    app = create_app(args.config)

    if socketio is None or not isinstance(socketio, SocketIO):
        print("Warning: `socketio` is not initialized properly. Creating a new instance.")
        socketio = SocketIO(app)

    print(f"Server running at http://{args.host}:{args.port}")

    # Only try to get IP info if in WSL
    if args.host == "0.0.0.0" and is_wsl_environment():
        try:
            wsl_ip = os.popen("hostname -I").read().strip().split()[0]
            print(f"Access from Windows at: http://{wsl_ip}:{args.port}")
        except Exception as e:
            print(f"Could not get WSL IP: {e}")

    socketio.run(app, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
