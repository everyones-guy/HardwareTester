import os

def create_dummy_files():
    """Create dummy spec sheets and test plans for testing."""
    files = {
        "uploads/spec_sheets/test_spec.pdf": "Dummy spec sheet content.",
        "uploads/test_plans/test_plan.csv": "Step,Action,Parameter\n1,Open Valve,50%",
    }
    for filepath, content in files.items():
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Created: {filepath}")

if __name__ == "__main__":
    print("Initializing test files...")
    create_dummy_files()
    print("Test file setup complete.")
