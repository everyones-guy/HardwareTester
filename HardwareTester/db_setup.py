
import os
import subprocess

def run_command(command):
    """Run a shell command."""
    try:
        print(f"Running: {' '.join(command)}")
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def initialize_db():
    """Initialize the database."""
    # Set FLASK_APP environment variable
    os.environ["FLASK_APP"] = "runserver.py"

    print("Initializing database...")
    # Initialize migrations folder
    if not run_command(["flask", "db", "init"]):
        print("Failed to initialize migrations folder. It may already exist.")

    # Perform migrations
    if not run_command(["flask", "db", "migrate", "-m", "Initial migration"]):
        print("Failed to create migrations.")

    # Apply migrations to the database
    if not run_command(["flask", "db", "upgrade"]):
        print("Failed to apply migrations.")

def setup_fallback():
    """Setup SQLite as fallback if no DATABASE_URL is provided."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("No DATABASE_URL provided. Falling back to SQLite.")
        os.environ["DATABASE_URL"] = "sqlite:///fallback.db"

    initialize_db()

def setup_azure():
    """Setup Azure SQL if DATABASE_URL is provided."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("Using Azure SQL database.")
        initialize_db()
    else:
        print("DATABASE_URL is not set. Skipping Azure SQL setup.")

def main():
    """Main setup function."""
    print("Starting database setup...")
    setup_fallback()  # Always setup SQLite as fallback
    setup_azure()     # Optionally setup Azure SQL if DATABASE_URL is set
    print("Database setup complete.")

if __name__ == "__main__":
    main()
