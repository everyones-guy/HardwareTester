import argparse
import os
import platform
import socket
from dotenv import load_dotenv
from flask_socketio import SocketIO
from Hardware_Tester_App import create_app
from Hardware_Tester_App.extensions import socketio  # Shared SocketIO instance

# Load .env early
load_dotenv()

def is_wsl_environment():
    """Detect if running inside Windows Subsystem for Linux."""
    try:
        return "microsoft" in platform.uname().release.lower()
    except Exception:
        return False

def get_wsl_ip():
    try:
        return os.popen("hostname -I").read().strip().split()[0]
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description="Run the Universal Hardware Tester backend server.")
    parser.add_argument("--config", default="development", help="Flask config to use.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to.")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")

    args = parser.parse_args()

    app = create_app(args.config)

    # Confirm socketio is still valid
    if socketio is None or not isinstance(socketio, SocketIO):
        print("Reinitializing SocketIO for fallback.")
        local_socketio = SocketIO(app)
    else:
        local_socketio = socketio

    print(f"Server running at http://{args.host}:{args.port}")

    if is_wsl_environment() and args.host == "0.0.0.0":
        wsl_ip = get_wsl_ip()
        if wsl_ip:
            print(f"Access from Windows browser: http://{wsl_ip}:{args.port}")
        else:
            print("Could not determine WSL IP for host access.")

    local_socketio.run(app, host=args.host, port=args.port, debug=args.debug, use_reloader=False)

if __name__ == "__main__":
    main()
