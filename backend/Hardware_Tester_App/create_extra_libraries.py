#!/usr/bin/env python3
"""
create_extra_libraries.py — Build/Install extra native/python libs used by the project.

By default it scans ./extra_libs and tries, in order, for each subdir:
  1) ./build.sh
  2) Makefile -> `make`
  3) Python project -> `pip install -e .`

Creates a .build/ok stamp per library so repeated runs are idempotent.
Use --rebuild to force rebuilding.

Examples:
  python create_extra_libraries.py
  python create_extra_libraries.py --root ./third_party --rebuild
"""

import os
import sys
import shlex
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional

# Prefer your app logger if available; fall back to stdlib logging.
try:
    from Hardware_Tester_App.utils.custom_logger import CustomLogger
    logger = CustomLogger.get_logger("extra_libs")
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("extra_libs")

# Define required extra directories relative to project root
EXTRA_LIBRARIES = [
    "uploads/blueprints",
    "uploads/configs",
    "uploads/logs",
    "uploads/data",
    "instance/backups",
]

def run(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 600) -> bool:
    """Run a command in cwd; return True on success."""
    pretty = " ".join(shlex.quote(c) for c in cmd)
    logger.info("Running: %s%s", pretty, f" (cwd={cwd})" if cwd else "")
    try:
        proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.error("Timed out: %s", pretty)
        return False
    if proc.stdout:
        logger.info(proc.stdout.strip())
    if proc.stderr:
        logger.warning(proc.stderr.strip())
    return proc.returncode == 0


def is_python_project(dirpath: Path) -> bool:
    return (dirpath / "pyproject.toml").exists() or (dirpath / "setup.py").exists()


def build_library(lib_dir: Path, rebuild: bool = False) -> bool:
    """
    Build or install a single library directory.
    Produces lib_dir/.build/ok on success.
    """
    stamp_dir = lib_dir / ".build"
    stamp_file = stamp_dir / "ok"

    if stamp_file.exists() and not rebuild:
        logger.info("Skipping %s (already built). Use --rebuild to force.", lib_dir.name)
        return True

    # Ensure .build dir exists
    stamp_dir.mkdir(parents=True, exist_ok=True)

    # Strategy 1: build.sh
    build_sh = lib_dir / "build.sh"
    if build_sh.exists():
        logger.info("[build.sh] %s", lib_dir)
        # make sure it's executable on *nix
        try:
            os.chmod(build_sh, 0o755)
        except Exception:
            pass
        if not run([str(build_sh)], cwd=lib_dir):
            logger.error("build.sh failed in %s", lib_dir)
            return False
        stamp_file.write_text("ok\n", encoding="utf-8")
        return True

    # Strategy 2: Makefile
    makefile = lib_dir / "Makefile"
    if makefile.exists():
        logger.info("[make] %s", lib_dir)
        if not run(["make"], cwd=lib_dir):
            logger.error("'make' failed in %s", lib_dir)
            return False
        stamp_file.write_text("ok\n", encoding="utf-8")
        return True

    # Strategy 3: Python project
    if is_python_project(lib_dir):
        logger.info("[pip install -e .] %s", lib_dir)
        # Use current Python interpreter's pip
        py = sys.executable or "python"
        if not run([py, "-m", "pip", "install", "-e", "."], cwd=lib_dir):
            logger.error("Editable install failed in %s", lib_dir)
            return False
        stamp_file.write_text("ok\n", encoding="utf-8")
        return True

    logger.info("No recognized build strategy for %s - skipping.", lib_dir)
    return True  # Not a failure; just nothing to do.

def ensure_directories():
    """Ensure required extra library directories exist."""
    created = []
    for directory in EXTRA_LIBRARIES:
        abs_path = os.path.abspath(directory)
        if not os.path.exists(abs_path):
            os.makedirs(abs_path, exist_ok=True)
            created.append(abs_path)
            logger.info(f"Created missing directory: {abs_path}")
        else:
            logger.debug(f"Directory already exists: {abs_path}")
    return created


def main():
    parser = argparse.ArgumentParser(description="Build/Install extra libraries for the project.")
    parser.add_argument("--root", default=os.getenv("EXTRA_LIBS_DIR", "extra_libs"),
                        help="Directory containing extra libraries (default: extra_libs)")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild even if already built.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        logger.info("No extra libraries directory found at %s; nothing to do.", root)
        return

    logger.info("Scanning %s for libraries...", root)
    libs = sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")])

    if not libs:
        logger.info("No subdirectories found under %s; nothing to do.", root)
        return

    overall_ok = True
    for lib in libs:
        ok = build_library(lib, rebuild=args.rebuild)
        overall_ok = overall_ok and ok

    if not overall_ok:
        logger.error("One or more libraries failed to build.")
        sys.exit(1)

    logger.info("All extra libraries processed.")


if __name__ == "__main__":
    dirs = ensure_directories()
    if dirs:
        print("Created directories:", dirs)
    else:
        print("All required directories already exist.")

    main()
