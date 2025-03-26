
# utils/testing.py
# using subprocess we run pytest to test the project with the run_pytest 
# function that runs the pytest command and prints the output if the tests pass or fail

import subprocess

def run_pytest():
    """Run PyTest for the project."""
    try:
        result = subprocess.run(["pytest"], capture_output=True, text=True)
        print("PyTest Output:\n", result.stdout)
        if result.returncode != 0:
            print("Tests failed. Check the logs for details.")
        else:
            print("All tests passed successfully!")
    except Exception as e:
        print(f"Error running tests: {e}")

