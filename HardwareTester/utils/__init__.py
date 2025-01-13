# utils/__init__.py

from HardwareTester.utils.testing import run_pytest
from HardwareTester.utils.hardware_manager import get_system_info, print_system_info
from HardwareTester.utils.auto_deploy import build_project, deploy_project, clean_build_directory, package_project
from HardwareTester.utils.db_utils import DatabaseManager, initialize_database  # Import database utilities
from HardwareTester.utils.custom_logger import CustomLogger  # Import Logger utility if you have a custom logger
from HardwareTester.utils.bcrypt_utils import hash_password, check_password, is_strong_password  # Import bcrypt utility functions

# Expose all utility functions/classes directly under `utils` package
__all__ = [
    "run_pytest",
    "get_system_info",
    "print_system_info",
    "build_project",
    "deploy_project",
    "clean_build_directory",
    "package_project",
    "DatabaseManager",
    "initialize_database", 
    "CustomLogger",
    "hash_password",
    "verify_password",
    "is_strong_password",
]