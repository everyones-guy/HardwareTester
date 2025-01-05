from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
from flask import current_app

# Interpret the config file for Python logging.
fileConfig(context.config.config_file_name)

# Access the app's database models
from HardwareTester.models.db import db  # Import your `db` instance
from HardwareTester.models import User  # Import at least one model to expose metadata

# Set up target metadata for Alembic to use
target_metadata = db.metadata  # Correctly reference the metadata here

# Get database URL from app configuration
config = context.config
config.set_main_option(
    "sqlalchemy.url", current_app.config.get("SQLALCHEMY_DATABASE_URI")
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
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
