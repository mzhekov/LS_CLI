"""
Main CLI application
"""

import click
import sys
from pathlib import Path
from leadsauce.utils.config import get_config, init_config
from leadsauce.utils.db import init_database
from leadsauce.utils.constants import APP_VERSION, APP_DIR, CONFIG_FILE, DATABASE_FILE


@click.group(invoke_without_command=True)
@click.version_option(version=APP_VERSION)
@click.option('--config', type=click.Path(), help='Path to config file')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, config, debug):
    """
    LeadSauce CLI - Professional Network Management

    A powerful command-line tool for managing your professional contacts,
    companies, interactions, and relationships.

    Run without arguments to see the dashboard.
    Use 'leadsauce COMMAND --help' for help on a specific command.
    """
    ctx.ensure_object(dict)

    # Load configuration
    if config:
        ctx.obj['config'] = get_config()
        ctx.obj['config'].config_path = Path(config)
        ctx.obj['config']._load_config()
    else:
        ctx.obj['config'] = get_config()

    # Set debug mode
    if debug:
        ctx.obj['config'].set('logging.level', 'DEBUG')

    # Ensure database is initialized
    try:
        init_database()
    except Exception as e:
        if debug:
            click.secho(f"Database initialization warning: {e}", fg='yellow')

    # If no subcommand is provided, show dashboard
    if ctx.invoked_subcommand is None:
        # Check if database exists (first run)
        if not DATABASE_FILE.exists():
            from leadsauce.utils.dashboard import show_welcome
            show_welcome()
            click.echo("Run 'leadsauce init' to set up the database.")
        else:
            from leadsauce.utils.dashboard import show_dashboard
            show_dashboard()


@cli.command()
@click.pass_context
def init(ctx):
    """
    Initialize LeadSauce CLI configuration

    This will create:
    - Configuration directory (~/.leadsauce/)
    - Default configuration file
    - Database schema
    - Required directories
    """
    try:
        click.echo("Initializing LeadSauce CLI...")

        # Create config
        config = init_config()
        click.secho(f"✓ Created configuration at {CONFIG_FILE}", fg='green')

        # Initialize database
        init_database()
        click.secho(f"✓ Initialized database", fg='green')

        # Create directories
        APP_DIR.mkdir(parents=True, exist_ok=True)
        (APP_DIR / "logs").mkdir(exist_ok=True)
        (APP_DIR / "plugins").mkdir(exist_ok=True)
        (APP_DIR / "workflows").mkdir(exist_ok=True)
        click.secho(f"✓ Created directories in {APP_DIR}", fg='green')

        click.echo()

        # Show welcome message
        from leadsauce.utils.dashboard import show_welcome
        show_welcome()

    except Exception as e:
        click.secho(f"✗ Initialization failed: {str(e)}", fg='red')
        raise click.Abort()


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.pass_context
def version(ctx, output_format):
    """Show version information"""

    if output_format == 'json':
        import json
        info = {
            'version': APP_VERSION,
            'app_name': 'LeadSauce CLI',
            'config_dir': str(APP_DIR)
        }
        click.echo(json.dumps(info, indent=2))
    else:
        click.echo(f"LeadSauce CLI version {APP_VERSION}")
        click.echo(f"Configuration directory: {APP_DIR}")


@cli.command()
@click.option('--mini', is_flag=True, help='Show mini dashboard')
@click.pass_context
def dashboard(ctx, mini):
    """Display dashboard with overview and statistics"""
    from leadsauce.utils.dashboard import show_dashboard, show_mini_dashboard

    if mini:
        show_mini_dashboard()
    else:
        show_dashboard()


@cli.command()
@click.pass_context
def tui(ctx):
    """Launch interactive TUI mode with menus and navigation

    Navigate using arrow keys, select with Enter, and interact
    with your network without typing commands.
    """
    from leadsauce.utils.interactive import interactive_main_menu
    interactive_main_menu()


# Import and register command groups
from leadsauce.commands import profile, company
cli.add_command(profile.profile)
cli.add_command(company.company)

# Note: Additional command groups will be added as they are implemented:
# from leadsauce.commands import interaction, reminder, tag, team, etc.


if __name__ == '__main__':
    cli(obj={})
