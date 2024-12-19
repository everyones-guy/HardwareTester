from HardwareTester import create_app, socketio
from HardwareTester.extensions import db
import logging
import argparse
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run the HardwareTester application.")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="The host IP to bind the server (default: 127.0.0.1)."
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="The port to bind the server (default: 5000)."
    )
    parser.add_argument(
        "--config", type=str, default="development", help="The configuration to use (default: development)."
    )
    args = parser.parse_args()

    # Create the Flask app
    app = create_app(args.config)

    # Initialize the database
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully.")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            sys.exit(1)

    # Start the server
    try:
        logger.info(f"Starting the server at {args.host}:{args.port} using {args.config} configuration.")
        socketio.run(app, host=args.host, port=args.port)
    except Exception as e:
        logger.error(f"Error starting the server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
