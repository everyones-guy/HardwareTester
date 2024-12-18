import click
from HardwareTester.services.valve_service import list_valves, add_valve, delete_valve

@click.group()
def cli():
    """Command-line interface for HardwareTester."""
    pass

@cli.command()
def list_valves_cli():
    """List all valves."""
    result = list_valves()
    if result["success"]:
        for valve in result["valves"]:
            click.echo(f"ID: {valve['id']}, Name: {valve['name']}, Type: {valve['type']}")
    else:
        click.echo(f"Error: {result['error']}")

@cli.command()
@click.argument("name")
@click.argument("valve_type")
@click.option("--api_endpoint", default=None, help="Optional API endpoint for the valve.")
def add_valve_cli(name, valve_type, api_endpoint):
    """Add a new valve."""
    result = add_valve(name, valve_type, api_endpoint)
    if result["success"]:
        click.echo(f"Valve added successfully: {result['valve']}")
    else:
        click.echo(f"Error: {result['error']}")

@cli.command()
@click.argument("valve_id", type=int)
def delete_valve_cli(valve_id):
    """Delete a valve."""
    result = delete_valve(valve_id)
    if result["success"]:
        click.echo(f"Valve ID {valve_id} deleted successfully.")
    else:
        click.echo(f"Error: {result['error']}")

if __name__ == "__main__":
    cli()

