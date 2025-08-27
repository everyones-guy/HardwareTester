import os
import click
from faker import Faker
from dotenv import load_dotenv
from flask.cli import with_appcontext

from Hardware_Tester_App.extensions import db
from Hardware_Tester_App.utils.bcrypt_utils import hash_password
from Hardware_Tester_App.utils.custom_logger import CustomLogger

# Services
from Hardware_Tester_App.services.configuration_service import ConfigurationService
from Hardware_Tester_App.services.emulator_service import EmulatorService
from Hardware_Tester_App.services.mqtt_service import MQTTService
from Hardware_Tester_App.services.test_service import TestService
from Hardware_Tester_App.services.test_plan_service import TestPlanService  # (kept import; not used directly)

# Models
from Hardware_Tester_App.models.user_models import User, UserRole
from Hardware_Tester_App.models.dashboard_models import DashboardData

# Load .env variables
load_dotenv()

# initialize logger
logger = CustomLogger.get_logger("cli")


@click.group(help="CLI for Universal Hardware Tester.")
def cli():
    """Root CLI group."""
    pass


# ----------------------
# Database Commands (SAFE)
# ----------------------
@cli.group(help="Database management (use Flask-Migrate: `flask db upgrade`, etc.).")
def dbcli():
    """Database management commands."""
    pass


@dbcli.command("seed", help="Seed the database with an admin user (idempotent).")
@with_appcontext
def seed_data():
    """
    Creates a default admin user if it doesn't exist.
    Uses ADMIN_EMAIL / ADMIN_PASSWORD from environment when present.
    """
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "adminPassword1!")

        click.echo(f"Seeding database (admin: {admin_email})...")
        existing = User.query.filter_by(email=admin_email).first()
        if existing:
            click.echo("Admin user already exists. ")
            return

        # Prefer model's own password API if present; else use bcrypt util
        admin = User(
            email=admin_email,
            username="admin",
            role=UserRole.ADMIN.value if hasattr(UserRole, "ADMIN") else "admin",
        )
        if hasattr(admin, "set_password"):
            admin.set_password(admin_password)
        else:
            admin.password = hash_password(admin_password)

        db.session.add(admin)
        db.session.commit()
        click.echo("Default admin user created. ")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding database: {e}")
        click.echo(f"Error: {e}")


@dbcli.command("drop-all", help="Drop ALL tables (DANGEROUS). Requires --force.")
@click.option("--force", is_flag=True, help="Actually drop all tables.")
@with_appcontext
def drop_db(force: bool):
    """Dangerous: drops all tables. Prefer using Alembic migrations for schema changes."""
    if not force:
        click.echo("Refusing to drop DB without --force. (This is destructive.)")
        return
    try:
        db.drop_all()
        db.session.commit()
        logger.warning("Database tables dropped.")
        click.echo("Database dropped successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error dropping database: {e}")
        click.echo(f"Error: {e}")


# ----------------------
# Configuration Commands
# ----------------------
@cli.group(help="Manage configurations.")
def config():
    """Manage configurations."""
    pass


@config.command("save")
@click.argument("name")
@click.argument("layout")
@with_appcontext
def save_config(name, layout):
    """Save a new configuration."""
    result = ConfigurationService.save_configuration(name, layout)
    click.echo(result.get("message") if result.get("success") else f"Error: {result.get('error')}")


@config.command("list")
@with_appcontext
def list_configs():
    """List all configurations."""
    result = ConfigurationService.list_configurations()
    if result.get("success"):
        for c in result.get("configurations", []):
            click.echo(f"ID: {c.get('id')} | Name: {c.get('name')}")
    else:
        click.echo(f"Error: {result.get('error')}")


# ----------------------
# Emulator Commands
# ----------------------
@cli.group(help="Emulator-related commands.")
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
@cli.group(help="MQTT-related commands.")
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
    try:
        service.publish(topic, message)
        click.echo(f"Message published to {topic}.")
    finally:
        service.disconnect()


# ----------------------
# Test Commands
# ----------------------
@cli.group(help="Testing commands.")
def test():
    """Testing commands."""
    pass


@test.command("run", help="Run a Test Plan by ID.")
@click.argument("test_plan_id", type=int)
@with_appcontext
def run_test(test_plan_id):
    """Run a specific test plan."""
    result = TestService.run_test_plan(test_plan_id)
    click.echo(result.get("message") if result.get("success") else f"Error: {result.get('error')}")


@test.command("list", help="List available Test Plans.")
@with_appcontext
def list_tests():
    """List all test plans."""
    result = TestService.list_tests()
    if result.get("success"):
        for t in result.get("tests", []):
            click.echo(f"ID: {t.get('id')} | Name: {t.get('name')}")
    else:
        click.echo(f"Error: {result.get('error')}")


@test.command("generate-tests", help="Generate test files from blueprints/commands.")
@click.option("--output-dir", default="generated_tests", help="Directory to save generated test files.")
@click.option(
    "--method",
    type=click.Choice(["firmware", "mqtt"], case_sensitive=False),
    default="firmware",
    help="Method to fetch commands: 'firmware' or 'mqtt'."
)
@click.option(
    "--mqtt-topic",
    default="hardware/commands",
    help="MQTT topic for fetching commands (only for method=mqtt)."
)
@with_appcontext
def generate_tests(output_dir, method, mqtt_topic):
    """
    Generate test files dynamically based on available commands + blueprints.
    """
    click.echo("Fetching blueprints from the system...")
    blueprints = EmulatorService.fetch_blueprints().get("blueprints", [])

    if not blueprints:
        click.echo("No blueprints available. Cannot generate tests.")
        return

    all_test_files = []

    for blueprint in blueprints:
        blueprint_name = blueprint.get("name")
        if not blueprint_name:
            continue
        click.echo(f"Processing blueprint: {blueprint_name}")

        # Fetch commands dynamically based on the method
        if method == "firmware":
            commands = EmulatorService.fetch_commands_from_firmware(blueprint_name)
        elif method == "mqtt":
            commands = EmulatorService.fetch_commands_via_mqtt(mqtt_topic)
        else:
            commands = []

        if not commands:
            click.echo(f"No commands for blueprint: {blueprint_name}. Skipping...")
            continue

        from Hardware_Tester_App.utils.test_generator import TestGenerator
        generator = TestGenerator([blueprint], commands, output_dir=output_dir)
        test_files = generator.generate_test_suite()
        all_test_files.extend(test_files)

    click.echo("Generated test files:")
    for file in all_test_files:
        click.echo(f" - {file}")


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
    """Upload firmware to a device via MQTT."""
    if not os.path.exists(firmware_path):
        click.echo(f"Firmware file {firmware_path} not found.")
        return

    service = MQTTService()
    service.connect()
    try:
        service.upload_firmware(device_id, firmware_path)
        click.echo(f"Firmware uploaded to device {device_id}.")
    finally:
        service.disconnect()


# ----------------------
# Data Mocking Commands
# ----------------------
@cli.group(help="Data mocking commands.")
def mock():
    """Mock data commands."""
    pass


@mock.command("users", help="Add mock users to the database.")
@with_appcontext
def mock_users():
    """Add mock users (10 users + 1 admin)."""
    fake = Faker()
    try:
        click.echo("Adding mock users...")
        for _ in range(10):
            user = User(
                name=fake.name(),
                email=fake.email(),
                username=fake.user_name(),
                role=UserRole.USER.value if hasattr(UserRole, "USER") else "user",
                password_hash=hash_password("mockpassword"),
            )
            db.session.add(user)

        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN.value if hasattr(UserRole, "ADMIN") else "admin",
            password_hash=hash_password("adminpassword"),
        )
        db.session.add(admin_user)

        db.session.commit()
        click.echo("Mock users added successfully!")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding mock users: {e}")
        click.echo(f"Error adding mock users: {e}")


@mock.command("dashboard", help="Add mock dashboard data.")
@with_appcontext
def add_mock_dashboard_data():
    """Add mock dashboard data for each user."""
    fake = Faker()
    try:
        click.echo("Adding mock dashboard data...")
        users = User.query.all()
        if not users:
            click.echo("No users found. Run 'flask cli mock users' first.")
            return

        for user in users:
            for _ in range(5):  # 5 items per user
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
        logger.error(f"Error adding mock dashboard data: {e}")
        click.echo(f"Error adding mock dashboard data: {e}")


@mock.command("clear", help="Clear mock data (DashboardData + User).")
@with_appcontext
def clear_mock_data():
    """Clear mock data from the database."""
    try:
        click.echo("Clearing mock data...")
        db.session.query(DashboardData).delete()
        db.session.query(User).delete()
        db.session.commit()
        click.echo("All mock data cleared!")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error clearing mock data: {e}")
        click.echo(f"Error clearing mock data: {e}")
