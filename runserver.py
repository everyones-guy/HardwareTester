import argparse
import os
from flask_socketio import SocketIO
from HardwareTester import create_app
from HardwareTester.extensions import socketio  # Importing socketio instance

def main():
    global socketio  # Explicitly mark it as global to avoid UnboundLocalError

    parser = argparse.ArgumentParser(description="Run the Hardware Tester server.")
    parser.add_argument("--config", help="Configuration to use (default: development)", default="development")
    parser.add_argument("--host", help="Host IP address (default: 0.0.0.0)", default="0.0.0.0")
    parser.add_argument("--port", help="Port number (default: 5000)", type=int, default=5000)
    parser.add_argument("--debug", help="Enable debug mode", action="store_true")

    args = parser.parse_args()

    app = create_app(args.config)

    # Ensure `socketio` is properly initialized
    if socketio is None or not isinstance(socketio, SocketIO):
        print(" Warning: `socketio` is not initialized properly. Creating a new instance.")
        socketio = SocketIO(app)  # Reinitialize `socketio`

    print(f" Server running at http://{args.host}:{args.port}")

    # WSL-specific handling
    if args.host == "0.0.0.0" and "WSL" in os.uname().release:
        wsl_ip = os.popen("hostname -I").read().strip().split()[0]
        print(f" Access from Windows at: http://{wsl_ip}:{args.port}")

    socketio.run(app, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
