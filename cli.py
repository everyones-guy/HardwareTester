import click
from flask.cli import with_appcontext
from HardwareTester.extensions import db
from HardwareTester.utils.bcrypt_utils import hash_password, check_password, is_strong_password
from HardwareTester.utils.custom_logger import CustomLogger
from HardwareTester.services.configuration_service import ConfigurationService
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.services.mqtt_service import MQTTService
from HardwareTester.services.test_service import TestService
from HardwareTester.services.test_plan_service import TestPlanService
from HardwareTester.models.user_models import User, UserRole
from HardwareTester.models.dashboard_models import DashboardData
from faker import Faker
import os

# initialize logger
logger = CustomLogger.get_logger("cli")


@click.group(help="CLI for Universal Hardware Tester.")
def cli():
    pass


# ----------------------
# Database Commands
# ----------------------
@cli.group(help="Database management commands.")
def db():
    pass


@db.command("init", help="Initialize the database.")
@with_appcontext
def init_db():
    try:
        db.create_all()
        logger.info("Database initialized.")
        click.echo("Database initialized successfully.")

        # Add default admin user
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "adminPassword1!")
        if not User.query.filter_by(email=admin_email).first():
            hashed_password = hash_password(admin_password)
            #hashed_password = hash_password(admin_password)

            admin = User(email=admin_email, username="admin", password=hashed_password, role="admin")
            db.session.add(admin)
            db.session.commit()
            click.echo("Default admin user created.")
        else:
            click.echo("Admin user already exists.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        click.echo(f"Error: {e}")


@db.command("drop", help="Drop all database tables.")
@with_appcontext
def drop_db():
    try:
        db.drop_all()
        logger.warning("Database tables dropped.")
        click.echo("Database dropped successfully.")
    except Exception as e:
        logger.error(f"Error dropping database: {e}")
        click.echo(f"Error: {e}")


@db.command("seed", help="Seed the database with initial data.")
@with_appcontext
def seed_data():
    try:
        click.echo("Seeding database...")
        if not User.query.filter_by(email="admin@example.com").first():
            admin = User(
                email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
                username="admin",
                role="admin",
            )
            admin.set_password("adminPassword1!")
            db.session.add(admin)
            db.session.commit()
            click.echo("Default admin user created.")
        else:
            click.echo("Admin user already exists.")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        click.echo(f"Error: {e}")

# ----------------------
# Configuration Commands
# ----------------------
@cli.group()
def config():
    """Manage configurations."""
    pass


@config.command("save")
@click.argument("name")
@click.argument("layout")
def save_config(name, layout):
    """Save a new configuration."""
    result = ConfigurationService.save_configuration(name, layout)
    click.echo(result["message"] if result["success"] else f"Error: {result['error']}")


@config.command("list")
def list_configs():
    """List all configurations."""
    result = ConfigurationService.list_configurations()
    if result["success"]:
        for config in result["configurations"]:
            click.echo(f"ID: {config['id']} | Name: {config['name']}")
    else:
        click.echo(f"Error: {result['error']}")


# ----------------------
# Emulator Commands
# ----------------------
@cli.group()
def emulator():
    """Emulator-related commands."""
    pass


@emulator.command("start")
@click.option("--machine", required=True)
def start_emulator(machine):
    """Start the emulator."""
    EmulatorService.start_emulation(machine)
    click.echo(f"Emulator started for {machine}.")


@emulator.command("stop")
def stop_emulator():
    """Stop the emulator."""
    EmulatorService.stop_emulation()
    click.echo("Emulator stopped.")


# ----------------------
# MQTT Commands
# ----------------------
@cli.group()
def mqtt():
    """MQTT-related commands."""
    pass


@mqtt.command("publish")
@click.argument("topic")
@click.argument("message")
def mqtt_publish(topic, message):
    """Publish a message to an MQTT topic."""
    service = MQTTService()
    service.connect()
    service.publish(topic, message)
    service.disconnect()
    click.echo(f"Message published to {topic}.")


# ----------------------
# Test Commands
# ----------------------
@cli.group()
def test():
    """Testing commands."""
    pass


@test.command("run", help="Run Test Commands.")
@click.argument("test_plan_id", type=int)
def run_test(test_plan_id):
    """Run a specific test plan."""
    result = TestService.run_test_plan(test_plan_id)
    click.echo(result["message"] if result["success"] else f"Error: {result['error']}")


@test.command("list", help="List Available Tests")
def list_tests():
    """List all test plans."""
    result = TestService.list_tests()
    if result["success"]:
        for test in result["tests"]:
            click.echo(f"ID: {test['id']} | Name: {test['name']}")
    else:
        click.echo(f"Error: {result['error']}")


# ----------------------
# Firmware Commands
# ----------------------
@cli.group(help="Firmware management commands.")
def firmware():
    """Firmware management commands."""
    pass


@firmware.command("upload")
@click.argument("device_id")
@click.argument("firmware_path")
def upload_firmware(device_id, firmware_path):
    """Upload firmware to a device."""
    if not os.path.exists(firmware_path):
        click.echo(f"Firmware file {firmware_path} not found.")
        return

    service = MQTTService()
    service.connect()
    service.upload_firmware(device_id, firmware_path)
    service.disconnect()
    click.echo(f"Firmware uploaded to device {device_id}.")

# ----------------------
# Data Mocking Commands
# ----------------------
@cli.group(help="Data Mocking Commands.")
def mock():
    """Mock data commands."""
    pass


@mock.command("users", help="Add mock users to the database.")
@with_appcontext
def mock_users():
    """Add mock users."""
    fake = Faker()
    try:
        click.echo("Adding mock users...")
        for _ in range(10):
            user = User(
                name=fake.name(),
                email=fake.email(),
                username=fake.user_name(),
                role=UserRole.USER,
                password_hash="mockhashedpassword",  # Replace with a hashed password if necessary
            )
            db.session.add(user)

        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN,
            password_hash="adminhashedpassword",  # Replace with a hashed password if necessary
        )
        db.session.add(admin_user)

        db.session.commit()
        click.echo("Mock users added successfully!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error adding mock users: {e}")


@mock.command("add-dashboard-data", help="Add mock dashboard data.")
@with_appcontext
def add_mock_dashboard_data():
    """Add mock dashboard data."""
    fake = Faker()
    try:
        click.echo("Adding mock dashboard data...")
        users = User.query.all()
        if not users:
            click.echo("No users found. Add mock users first using 'mock add-users'.")
            return

        for user in users:
            for _ in range(5):  # Add 5 items per user
                dashboard_data = DashboardData(
                    user_id=user.id,
                    name=fake.word(),
                    value=fake.random_int(min=0, max=100),
                    title=fake.sentence(nb_words=3),
                    description=fake.text(max_nb_chars=100),
                    type=fake.word(),
                )
                db.session.add(dashboard_data)

        db.session.commit()
        click.echo("Mock dashboard data added successfully!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error adding mock dashboard data: {e}")


@mock.command("clear-mock-data", help="Clear all mock data.")
@with_appcontext
def clear_mock_data():
    """Clear mock data from all tables."""
    try:
        click.echo("Clearing mock data...")
        db.session.query(DashboardData).delete()
        db.session.query(User).delete()
        db.session.commit()
        click.echo("All mock data cleared!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error clearing mock data: {e}")


# ----------------------
# CLI Registration
# ----------------------
def register_commands(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(cli)
    logger.info("CLI commands registered successfully.")
