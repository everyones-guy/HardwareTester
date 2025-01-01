# cli.py: Main CLI Entrypoint
import click
from flask.cli import with_appcontext
from HardwareTester.utils.db_utils import init_db, migrate_db, upgrade_db
from HardwareTester.services.configuration_service import save_configuration, load_configuration, list_configurations
from HardwareTester.services.emulator_service import run_emulator
from HardwareTester.services.mqtt_client import FirmwareMQTTClient
from HardwareTester.services.test_service import execute_test_plan, list_tests, create_test_plan
from HardwareTester.utils.firmware_utils import validate_firmware_file
from HardwareTester.models import db, bcrypt, User
import os

@click.group()
def cli():
    """Firmware CLI for device management and testing."""
    pass

# Database Commands
@cli.group()
def db():
    """Database management commands."""
    pass

@db.command("init")
def db_init():
    """Initialize the database."""
    init_db()
    click.echo("Database initialized.")

@db.command("migrate")
def db_migrate():
    """Generate migration scripts."""
    migrate_db()
    click.echo("Database migration scripts generated.")

@db.command("upgrade")
def db_upgrade():
    """Apply database migrations."""
    upgrade_db()
    click.echo("Database upgraded.")

@db.command("seed")
@with_appcontext
def seed_db():
    from HardwareTester.models import User  # Local import to avoid circular dependency
    click.echo("Seeding database...")
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

@db.command("create-admin")
@click.option("--username", prompt=True, help="Admin username")
@click.option("--password", prompt=True, hide_input=True, help="Admin password")
def create_admin(username, password):
    """Create an admin user."""
    click.echo(f"Creating admin user: {username}")
    
@db.command("init-db")
@with_appcontext
def init_db():
    """Initialize the database."""
    db.create_all()
    click.echo("Database initialized successfully.")
    # Add default admin
    if not User.query.filter_by(email="admin@example.com").first():
        hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
        admin = User(email="admin@example.com", password=hashed_password, role="admin")
        db.session.add(admin)
        db.session.commit()
        click.echo("Default admin user created.")
    else:
        click.echo("Admin user already exists.")

@db.command("drop-db")
@with_appcontext
def drop_db():
    """Drop all tables in the database."""
    db.drop_all()
    click.echo("Database dropped.")

# Configuration Commands
@cli.group()
def config():
    """Configuration management commands."""
    pass

@config.command("save")
@click.argument("name")
@click.argument("layout")
def save_config(name, layout):
    """Save a new configuration."""
    result = save_configuration(name, layout)
    if result["success"]:
        click.echo(result["message"])
    else:
        click.echo(f"Error: {result['error']}")

@config.command("load")
@click.argument("config_id", type=int)
def load_config(config_id):
    """Load a configuration by ID."""
    result = load_configuration(config_id)
    if result["success"]:
        click.echo(result["configuration"])
    else:
        click.echo(f"Error: {result['error']}")

@config.command("list")
def list_configs():
    """List all configurations."""
    result = list_configurations()
    if result["success"]:
        for config in result["configurations"]:
            click.echo(f"ID: {config['id']}, Name: {config['name']}")
    else:
        click.echo(f"Error: {result['error']}")

# Emulator Commands
@cli.group()
def emulator():
    """Hardware emulator commands."""
    pass

@emulator.command("run")
@click.option("--machine", required=True, help="Machine name to emulate.")
@click.option("--config", default=None, help="Path to configuration file for the emulator.")
def run_emulator_cli(machine, config):
    """Run the hardware emulator."""
    run_emulator(machine, config=config)
    click.echo(f"Emulator for {machine} started.")
    
@emulator.command("start")
def start_emulator():
    """Start the emulator."""
    click.echo("Starting the emulator...")

@emulator.command("stop")
def stop_emulator():
    """Stop the emulator."""
    click.echo("Stopping the emulator...")

# MQTT Commands
@cli.group()
def mqtt():
    """MQTT commands."""
    pass

@mqtt.command("publish")
@click.argument("topic")
@click.argument("message")
def mqtt_publish(topic, message):
    """Publish a message to an MQTT topic."""
    from HardwareTester.services.mqtt_service import publish_message

    result = publish_message(topic, message)
    if result["success"]:
        click.echo("Message published successfully.")
    else:
        click.echo(f"Error: {result['error']}")

@mqtt.command("subscribe")
@click.argument("topic")
def mqtt_subscribe(topic):
    """Subscribe to an MQTT topic."""
    from HardwareTester.services.mqtt_service import subscribe_to_topic

    result = subscribe_to_topic(topic)
    if result["success"]:
        click.echo(f"Subscribed to topic {topic}")
    else:
        click.echo(f"Error: {result['error']}")

# Testing Commands
@cli.group()
def test():
    """Testing commands."""
    pass

@test.command("run")
@click.argument("test_plan_id", type=int)
def run_test(test_plan_id):
    """Run a specific test plan."""
    result = execute_test_plan(test_plan_id)
    if result["success"]:
        click.echo("Test plan executed successfully.")
        for step_result in result["results"]:
            click.echo(f"{step_result['step']}: {step_result['result']}")
    else:
        click.echo(f"Error: {result['error']}")

@test.command("list")
def list_test_plans():
    """List all test plans."""
    result = list_tests()
    if result["success"]:
        click.echo("Available Test Plans:")
        for test in result["tests"]:
            click.echo(f"ID: {test['id']} Name: {test['name']}")
    else:
        click.echo(f"Error: {result['error']}")

@test.command("create")
@click.argument("name")
@click.argument("steps")
def create_test(name, steps):
    """Create a new test plan."""
    result = create_test_plan(name, steps)
    if result["success"]:
        click.echo(f"Test plan '{name}' created successfully.")
    else:
        click.echo(f"Error: {result['error']}")
        
@test.command("coverage")
def test_coverage():
    """Generate test coverage report."""
    click.echo("Generating test coverage report...")

# Firmware Commands
@cli.group()
def firmware():
    """Firmware management commands."""
    pass

@firmware.command("upload")
@click.argument("device_id")
@click.argument("firmware_path")
def upload_firmware(device_id, firmware_path):
    """Upload firmware to the device."""
    if not os.path.exists(firmware_path):
        click.echo(f"Firmware file {firmware_path} not found.")
        return
    client = FirmwareMQTTClient()
    client.connect()
    client.upload_firmware(device_id, firmware_path)
    client.disconnect()
    click.echo(f"Firmware uploaded to device {device_id}.")

@firmware.command("validate")
@click.argument("device_id")
def validate_firmware(device_id):
    """Validate firmware on the device."""
    client = FirmwareMQTTClient()
    client.connect()
    client.validate_firmware(device_id)
    client.disconnect()
    click.echo(f"Firmware validation for device {device_id} completed.")
    
# Register the master group
def register_commands(app):
    """Register CLI commands."""
    app.cli.add_command(cli)

if __name__ == "__main__":
    cli()
