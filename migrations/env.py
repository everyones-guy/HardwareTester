from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
from flask import current_app

# Interpret the config file for Python logging.
fileConfig(context.config.config_file_name)

# Access the app's database models and metadata
from HardwareTester.models.db import db  # Import your `db` instance
from HardwareTester.models.user_models import User, Token, Role, UserRole  # Import models
from HardwareTester.models.device_models import Emulation, Device, Peripheral, Controller, Blueprint
from HardwareTester.models.report_models import Report
from HardwareTester.models.project_models import Project, Milestone
from HardwareTester.models.metric_models import Metric
from HardwareTester.models.log_models import ActivityLog, Notification
from HardwareTester.models.dashboard_models import DashboardData
from HardwareTester.models.configuration_models import Configuration, Settings, GlobalSettings

# Retrieve target metadata for Alembic
target_metadata = db.metadata

# Retrieve database URL from Flask app configuration
config = context.config
config.set_main_option(
    "sqlalchemy.url", current_app.config["SQLALCHEMY_DATABASE_URI"]
)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Enables type comparison for migrations
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
