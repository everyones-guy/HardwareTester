import argparse
from dotenv import load_dotenv
from HardwareTester import create_app, socketio
import os

def main():
    # Load environment variables from the .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the Hardware Tester Flask App")
    parser.add_argument("--config", default=os.getenv("FLASK_CONFIG", "default"), help="Specify the configuration to use")
    args = parser.parse_args()

    app = create_app(args.config)
    socketio.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))

if __name__ == "__main__":
    main()
