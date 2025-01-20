import os
import subprocess
import sys
from HardwareTester.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("db_setup")

def run_command(command):
    """Run a shell command."""
    try:
        logger.info(f"Running: {' '.join(command)}")
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: {e.stderr}")
        return False

def initialize_db():
    """Initialize the database."""
    migrations_dir = os.path.join(os.getcwd(), "migrations")
    if not os.path.exists(migrations_dir):
        if not run_command(["flask", "db", "init"]):
            logger.warning("Failed to initialize migrations folder. It may already exist.")
    else:
        logger.info("Migrations folder already exists. Skipping initialization.")

    # Perform migrations
    if not run_command(["flask", "db", "migrate", "-m", "Initial migration"]):
        logger.error("Failed to create migrations.")
        sys.exit(1)

    # Apply migrations to the database
    if not run_command(["flask", "db", "upgrade"]):
        logger.error("Failed to apply migrations.")
        sys.exit(1)

def setup_database():
    """Setup database based on environment."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///C:/Users/Gary/source/repos/HardwareTester/HardwareTester/instance/app.db")
    os.environ["DATABASE_URL"] = database_url
    logger.info(f"Using database: {database_url}")
    initialize_db()

def main():
    """Main setup function."""
    logger.info("Starting database setup...")
    setup_database()
    logger.info("Database setup complete.")

if __name__ == "__main__":
    main()
