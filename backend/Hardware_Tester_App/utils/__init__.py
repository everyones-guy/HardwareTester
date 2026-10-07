"""Utilities load individually; importing validators does not initialize hardware."""
from importlib import import_module
__all__ = [
    "test_runner",
    "test_utils",
    "testing",
    "token_utils",
    "validators",
    "api_manager",
    "auto_deploy",
    "bcrypt_utils",
    "custom_logger",
    "db_utils",
    "firmware_utils",
    "hardware_manager",
    "manage_test_plans",
    "manage_valves",
    "parsers",
    "run_test_plans",
    "secrets",
    "serial_comm",
    "test_generator",
]

def __getattr__(name):
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(name)
