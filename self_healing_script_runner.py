# self healing script to run a python script and fix any missing libraries
# # This script will:
# 1. Run a specified Python script.
# 2. If the script fails due to a missing library, it will attempt to install the library using pip.
# 3. If the installation is successful, it will rerun the script.
# 4. If the script runs successfully, it will launch a final script in WSL.
# 5. If the script fails for any other reason, it will print the error and exit.
# 6. The script is designed to be run in a WSL environment.
# 7. The script will print the output and errors to the console for debugging.
# 8. The script will use subprocess to run commands and capture output.
# 9. The script will use regex to detect missing libraries in the error output.
# 10. The script will use time.sleep to wait before retrying the script after installing a library.
# 11. The script will use sys.exit to exit with an error code if it encounters an unfixable error.
# 12. The script will use os to check if the script is running in WSL.
# 13. The script will use argparse to allow the user to specify the script to test and the final script path.

import subprocess
import sys
import re
import time
import os

# === CONFIG ===
SCRIPT_TO_TEST = "runserver.py"
FINAL_SCRIPT_PATH = "/your/final/script.sh"
   # Change this to the script you want to test/fix first
FINAL_SCRIPT_PATH = "/path/to/your/final/script.sh"  # Change this to your final production script
WSL_TERMINAL_COMMAND = f"wsl bash -c '{FINAL_SCRIPT_PATH}'"

# === FUNCTIONS ===

def run_script(script_path):
    """Runs a script and returns (success, output, error)."""
    try:
        completed = subprocess.run(
            [sys.executable, script_path], 
            capture_output=True, text=True, check=True
        )
        return True, completed.stdout, completed.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def detect_missing_library(stderr_output):
    """Detects if the error was due to a missing library."""
    missing_module_match = re.search(r"No module named '(.*?)'", stderr_output)
    if missing_module_match:
        return missing_module_match.group(1)
    return None

def install_library(library_name):
    """Attempts to pip install the missing library."""
    print(f"Attempting to install missing library: {library_name}")
    result = subprocess.run([sys.executable, "-m", "pip", "install", library_name])
    return result.returncode == 0

def run_final_script():
    """Launch the final intended script inside WSL."""
    print("Launching final script in WSL...")
    subprocess.run(WSL_TERMINAL_COMMAND, shell=True)

# === MAIN ===

def main():
    print(f"Testing script: {SCRIPT_TO_TEST}")
    success, stdout, stderr = run_script(SCRIPT_TO_TEST)

    if success:
        print("Test script ran successfully!")
        run_final_script()
    else:
        print("Test script failed. Checking for fixable errors...")
        print(stderr)
        
        missing_library = detect_missing_library(stderr)
        
        if missing_library:
            print(f"Missing library detected: {missing_library}")
            if install_library(missing_library):
                print(f"Library {missing_library} installed successfully! Retrying script...\n")
                time.sleep(1)
                success_retry, stdout_retry, stderr_retry = run_script(SCRIPT_TO_TEST)

                if success_retry:
                    print("Script ran successfully after installing missing libraries!")
                    run_final_script()
                else:
                    print("Script still failed after installing libraries.")
                    print(stderr_retry)
                    sys.exit(1)
            else:
                print(f"Failed to install library {missing_library}. Exiting.")
                sys.exit(1)
        else:
            print("Encountered an error that is not auto-fixable:")
            print(stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
