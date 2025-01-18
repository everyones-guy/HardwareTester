import os
import shutil
import subprocess
import time
from pathlib import Path

def archive_migrations():
    """Archive the current migrations folder."""
    timestamp = time.strftime("%Y%m%d")
    backup_dir = f"migrations_backup/{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    if os.path.exists("migrations"):
        shutil.copytree("migrations", os.path.join(backup_dir, "migrations"))
        print(f"Backed up migrations to {backup_dir}/migrations")

def run_migrations():
    """Run migration and upgrade commands."""
    migration_message = input("Enter migration message: ").strip()
    
    try:
        # Generate new migration
        print("Generating new migration...")
        subprocess.run(["flask", "db", "migrate", "-m", migration_message], check=True)

        # Apply the migration
        print("Applying migration...")
        subprocess.run(["flask", "db", "upgrade"], check=True)
        print("Migration process completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during the process: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")

if __name__ == "__main__":
    archive_migrations()
    run_migrations()
