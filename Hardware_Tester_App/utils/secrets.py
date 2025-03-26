
# utils/secrets.py
def read_secret(file_path):
    """
    Reads the content of a secret file.
    
    Args:
        file_path (str): Path to the secret file.
    
    Returns:
        str: The content of the secret file.
    """
    try:
        with open(file_path, 'r') as secret_file:
            return secret_file.read().strip()
    except Exception as e:
        print(f"Failed to read secret from {file_path}: {e}")
        return None

