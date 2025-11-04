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


@cli.command()
@click.option('--backup', is_flag=True, help='Create a backup before migrating')
def migrate(backup):
    """Migrate database to remove authentication-related columns

    This command removes user_id and related columns from the database
    schema after the authentication system was removed. Safe to run
    multiple times.

    Example:
        leadsauce migrate
        leadsauce migrate --backup
    """
    import sqlite3
    import shutil
    from datetime import datetime

    click.echo("LeadSauce Database Migration")
    click.echo("=" * 60)
    click.echo(f"Database: {DATABASE_FILE}")

    if not DATABASE_FILE.exists():
        click.secho("✗ Database not found. Nothing to migrate.", fg='yellow')
        return

    # Create backup if requested
    if backup:
        backup_path = DATABASE_FILE.parent / f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        click.echo(f"\nCreating backup at: {backup_path}")
        shutil.copy2(DATABASE_FILE, backup_path)
        click.secho(f"✓ Backup created", fg='green')

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Tables and columns to remove
    tables_to_fix = {
        'companies': 'user_id',
        'profiles': 'user_id',
        'tags': 'user_id',
        'interactions': 'user_id',
        'reminders': 'user_id',
        'documents': 'uploaded_by_id',
        'activities': 'user_id',
        'teams': 'created_by_id',
    }

    migrated = []
    skipped = []

    click.echo("\nMigrating tables...")

    for table_name, column_name in tables_to_fix.items():
        try:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                skipped.append(f"{table_name} (table doesn't exist)")
                continue

            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            if column_name not in column_names:
                skipped.append(f"{table_name}.{column_name}")
                continue

            # Get columns to keep
            columns_to_keep = [col for col in columns if col[1] != column_name]

            # Build new schema
            column_defs = []
            for col in columns_to_keep:
                col_name, col_type, not_null, default_val, pk = col[1], col[2], col[3], col[4], col[5]
                not_null_str = " NOT NULL" if not_null else ""
                default_str = f" DEFAULT {default_val}" if default_val is not None else ""
                pk_str = " PRIMARY KEY" if pk else ""
                column_defs.append(f"{col_name} {col_type}{not_null_str}{default_str}{pk_str}")

            # Create new table
            cursor.execute(f"CREATE TABLE {table_name}_new ({', '.join(column_defs)})")

            # Copy data
            keep_column_names = [col[1] for col in columns_to_keep]
            cursor.execute(f"""
                INSERT INTO {table_name}_new ({', '.join(keep_column_names)})
                SELECT {', '.join(keep_column_names)}
                FROM {table_name}
            """)

            # Replace old table
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

            migrated.append(f"{table_name}.{column_name}")
            click.secho(f"  ✓ {table_name}.{column_name}", fg='green')

        except Exception as e:
            click.secho(f"  ✗ Error migrating {table_name}: {e}", fg='red')
            conn.rollback()
            conn.close()
            sys.exit(1)

    conn.commit()
    conn.close()

    click.echo("\n" + "=" * 60)
    click.secho("Migration complete!", fg='green', bold=True)
    click.echo("=" * 60)

    if migrated:
        click.echo(f"\n✓ Migrated {len(migrated)} columns")

    if skipped:
        click.echo(f"\n✓ Already correct: {len(skipped)} columns")

    click.echo("\nYou can now use LeadSauce CLI normally:")
    click.echo("  leadsauce tui")


# Import and register command groups
from leadsauce.commands import profile, company
cli.add_command(profile.profile)
cli.add_command(company.company)

# Note: Additional command groups will be added as they are implemented:
# from leadsauce.commands import interaction, reminder, tag, team, etc.


if __name__ == '__main__':
    cli(obj={})
