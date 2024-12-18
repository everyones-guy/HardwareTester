# utils/__init__.py

from .testing import run_pytest
from .hardware_manager import get_system_info, print_system_info
from .auto_deploy import build_project, deploy_project, clean_build_directory, package_project

# Expose all utility functions/classes directly under `utils` package
__all__ = [
    "run_pytest",
    "get_system_info",
    "print_system_info",
    "build_project",
    "deploy_project",
    "clean_build_directory",
    "package_project",
    "confirm_action",
]
