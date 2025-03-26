from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
from flask import current_app

# Load Alembic config file
fileConfig(context.config.config_file_name)

# Import your application's `db` instance and models
from Hardware_Tester_App.extensions import db
from Hardware_Tester_App.models.user_models import User, Token, Role, UserSettings
from Hardware_Tester_App.models.device_models import Emulation, Device, Peripheral, Controller, Blueprint
from Hardware_Tester_App.models.report_models import Report
from Hardware_Tester_App.models.project_models import Project, Milestone
from Hardware_Tester_App.models.metric_models import Metric
from Hardware_Tester_App.models.log_models import ActivityLog, Notification
from Hardware_Tester_App.models.dashboard_models import DashboardData
from Hardware_Tester_App.models.configuration_models import Configuration, Settings, GlobalSettings
from Hardware_Tester_App.models.test_models import TestPlan, TestStep

# Set target metadata
target_metadata = db.metadata

config = context.config
config.set_main_option("sqlalchemy.url", current_app.config["SQLALCHEMY_DATABASE_URI"])

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        render_as_batch=True,  # Enable batch mode for SQLite
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        naming_convention={
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "pk": "pk_%(table_name)s"},
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
            render_as_batch=True,  # Enable batch mode for SQLite
            naming_convention={
                "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                "uq": "uq_%(table_name)s_%(column_0_name)s",
                "ix": "ix_%(table_name)s_%(column_0_name)s",
                "ck": "ck_%(table_name)s_%(constraint_name)s",
                "pk": "pk_%(table_name)s"},
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode(): 
    run_migrations_offline()
else:
    run_migrations_online()
