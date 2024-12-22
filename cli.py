# cli.py: Main CLI Entrypoint
import click
from HardwareTester.utils.db_utils import init_db, migrate_db, upgrade_db
from HardwareTester.services.configuration_service import save_configuration, load_configuration, list_configurations
from HardwareTester.services.emulator_service import run_emulator

@click.group()
def cli():
    """Hardware Tester CLI"""
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
def run_emulator_cli(machine):
    """Run the hardware emulator."""
    run_emulator(machine)
    click.echo(f"Emulator for {machine} started.")

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
    from HardwareTester.services.test_service import execute_test_plan

    result = execute_test_plan(test_plan_id)
    if result["success"]:
        click.echo("Test plan executed successfully.")
    else:
        click.echo(f"Error: {result['error']}")

if __name__ == "__main__":
    cli()
