#!/usr/bin/env python3
"""
db_setup.py - Safe database bootstrapper for Universal Hardware Tester.

Usage examples:
  python db_setup.py
  python db_setup.py --message "init schema"
  python db_setup.py --only-upgrade
  DATABASE_URL=postgresql+psycopg2://... python db_setup.py
"""

import os
import sys
import shlex
import subprocess
import argparse
from typing import List, Optional

# Prefer your app logger if available; fall back to stdlib logging.
try:
    from Hardware_Tester_App.utils.custom_logger import CustomLogger
    logger = CustomLogger.get_logger("db_setup")
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("db_setup")


def run(cmd: List[str], ok_if_contains: Optional[str] = None, timeout: int = 120) -> bool:
    """
    Run a command and return True on success.
    If ok_if_contains is provided, treat a nonzero return as OK if stderr/stdout contains that text.
    """
    logger.info("Running: %s", " ".join(shlex.quote(c) for c in cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.error("Timed out: %s", " ".join(cmd))
        return False

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if stdout:
        logger.info(stdout)
    if stderr:
        # don't treat any stderr as fatal - many alembic logs go to stderr
        logger.warning(stderr)

    if proc.returncode == 0:
        return True

    if ok_if_contains:
        hay = f"{stdout}\n{stderr}".lower()
        if ok_if_contains.lower() in hay:
            logger.info("Non-zero exit deemed OK due to message match: %r", ok_if_contains)
            return True

    return False


def ensure_migrations_initialized() -> None:
    """Run `flask db init` if the migrations/ folder is missing."""
    if not os.path.isdir("migrations"):
        logger.info("No migrations/ folder detected - initializing Alembic.")
        if not run(["flask", "db", "init"]):
            # If this fails because it already exists (race/etc), just continue.
            logger.warning("`flask db init` reported an error; continuing (it may already exist).")
    else:
        logger.info("migrations/ already present; skipping `flask db init`.")


def main():
    parser = argparse.ArgumentParser(description="Initialize/upgrade the database via Alembic.")
    parser.add_argument("--message", "-m", default="auto migration", help="Message for `flask db migrate`.")
    parser.add_argument("--only-upgrade", action="store_true", help="Skip migrate; just run `flask db upgrade`.")
    parser.add_argument("--no-init", action="store_true", help="Do not run `flask db init` automatically.")
    args = parser.parse_args()

    # Ensure DATABASE_URL is set for both runtime and Alembic env.
    db_url = os.getenv("DATABASE_URL") or "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/hardware_tester"
    os.environ["DATABASE_URL"] = db_url
    logger.info("Using DATABASE_URL=%s", db_url)

    if not args.no_init:
        ensure_migrations_initialized()

    if not args.only-upgrade:
        # Allow the classic Alembic message when nothing changed:
        # "No changes in schema detected."
        ok_phrase = "No changes in schema detected."
        if not run(["flask", "db", "migrate", "-m", args.message], ok_if_contains=ok_phrase):
            logger.error("Migration step failed.")
            sys.exit(1)
    else:
        logger.info("Skipping migrate step due to --only-upgrade.")

    if not run(["flask", "db", "upgrade"]):
        logger.error("Upgrade step failed.")
        sys.exit(1)

    logger.info("Database setup complete.")


if __name__ == "__main__":
    main()
