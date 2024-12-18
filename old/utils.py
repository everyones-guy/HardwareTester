def confirm_action(prompt):
    """Ask the user for confirmation."""
    response = input(f"{prompt} (yes/no): ").strip().lower()
    return response == "yes"
