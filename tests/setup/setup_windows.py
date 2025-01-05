import os
import sqlite3
import subprocess

def ensure_dependencies():
    """Ensure all dependencies are installed."""
    try:
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully.")
    except Exception as e:
        print(f"Error installing dependencies: {e}")

def initialize_database():
    """Initialize the SQLite database if it doesn't exist."""
    db_path = os.path.join(os.getcwd(), "app.db")
    if not os.path.exists(db_path):
        print("Database not found. Creating a new one...")
        conn = sqlite3.connect(db_path)
        conn.close()
        print("Database initialized successfully.")

def create_directories():
    """Create required directories for uploads."""
    upload_dirs = ["uploads/spec_sheets", "uploads/test_plans"]
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

if __name__ == "__main__":
    print("Setting up application for Windows...")
    ensure_dependencies()
    initialize_database()
    create_directories()
    print("Setup complete!")
