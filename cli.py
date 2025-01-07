import click
from flask.cli import with_appcontext
from HardwareTester.extensions import db, logger
from HardwareTester.services.configuration_service import ConfigurationService
from HardwareTester.services.emulator_service import EmulatorService
from HardwareTester.services.mqtt_service import MQTTService
from HardwareTester.services.test_service import TestService
from HardwareTester.services.test_plan_service import TestPlanService
from HardwareTester.models.user_models import User
from HardwareTester.utils.bcrypt_utils import bcrypt
import os


@click.group()
def cli():
    """CLI for Universal Hardware Tester."""
    pass


# ----------------------
# Database Commands
# ----------------------
@cli.group()
def db_commands():
    """Database management commands."""
    pass


@db_commands.command("init")
@with_appcontext
def init_db():
    """Initialize the database."""
    db.create_all()
    logger.info("Database initialized.")
    click.echo("Database initialized successfully.")

    # Add default admin user
    if not User.query.filter_by(email="admin@example.com").first():
        hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
        admin = User(email="admin@example.com", username="admin", password=hashed_password, role="admin")
        db.session.add(admin)
        db.session.commit()
        click.echo("Default admin user created.")
    else:
        click.echo("Admin user already exists.")


@db_commands.command("drop")
@with_appcontext
def drop_db():
    """Drop all database tables."""
    db.drop_all()
    logger.warning("Database tables dropped.")
    click.echo("Database dropped successfully.")

@db_commands.command("seed")
@with_appcontext
def seed_data():
    """Seed the database with initial data."""
    click.echo("Seeding database...")

    # Create a default admin user if not exists
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(
            email="admin@example.com",
            username="admin",
            role="admin",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        click.echo("Default admin user created.")
    else:
        click.echo("Admin user already exists.")    

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
@click.option("--machine", required=True, help="Machine name to emulate.")
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


@test.command("run")
@click.argument("test_plan_id", type=int)
def run_test(test_plan_id):
    """Run a specific test plan."""
    result = TestService.run_test_plan(test_plan_id)
    click.echo(result["message"] if result["success"] else f"Error: {result['error']}")


@test.command("list")
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
@cli.group()
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
# CLI Registration
# ----------------------
def register_commands(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(cli)
    logger.info("CLI commands registered successfully.")
