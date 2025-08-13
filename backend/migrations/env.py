# migrations/env.py
from __future__ import with_statement

from alembic import context
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool

# NEW: use the app's configured URL via Flask-Migrate/Flask
from flask import current_app

# Interpret the config file for Python logging.
config = context.config
fileConfig(config.config_file_name)

# Pull SQLAlchemy URL from the Flask app (single source of truth)
# Works with Flask-Migrate since it sets current_app during CLI runs.
db_uri = str(current_app.extensions["migrate"].db.engine.url)
config.set_main_option("sqlalchemy.url", db_uri)
print("🔹 Alembic is using:", db_uri)

# Target metadata from Flask-SQLAlchemy
db = current_app.extensions["migrate"].db
target_metadata = db.metadata

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

def run_migrations_offline():
    """Run migrations in 'offline' mode'."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=False,  # set True only for old SQLite
        naming_convention=NAMING_CONVENTION,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=False,  # set True only for old SQLite
            naming_convention=NAMING_CONVENTION,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

