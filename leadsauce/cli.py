"""
Main CLI application
"""

import click
import sys
from pathlib import Path
from leadsauce.utils.config import get_config, init_config
from leadsauce.utils.db import init_database
from leadsauce.utils.constants import APP_VERSION, APP_DIR, CONFIG_FILE, DATABASE_FILE
from leadsauce.utils.encryption import DatabasePasswordManager, prompt_for_password, verify_password_works


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

    Run without arguments to launch the interactive TUI.
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

    # Check if database exists
    db_exists = DATABASE_FILE.exists()

    # Prompt for database password (required for encrypted databases)
    if db_exists:
        # Database exists - prompt for password to unlock
        max_attempts = 10
        for attempt in range(max_attempts):
            password = prompt_for_password(confirm=False, is_first_time=False)
            DatabasePasswordManager.set_password(password)

            # Verify password works
            try:
                init_database()
                break  # Success!
            except Exception as e:
                if attempt < max_attempts - 1:
                    attempts_remaining = max_attempts - attempt - 1

                    # Basic error message
                    click.secho(f"\n✗ Incorrect password. {attempts_remaining} attempts remaining.", fg='red')

                    # Special warnings at different thresholds
                    if attempt + 1 == 5:
                        click.secho("⚠ WARNING: You have used 5 attempts. Please ensure you're entering the correct password.", fg='yellow', bold=True)
                    elif attempt + 1 >= 6:
                        click.secho(f"⚠ CRITICAL: Only {attempts_remaining} attempts left before lockout!", fg='yellow', bold=True)
                        if attempts_remaining <= 2:
                            click.echo("Tip: Make sure Caps Lock is off and you're using the correct password.")

                    DatabasePasswordManager.clear_password()
                else:
                    click.echo()
                    click.secho("=" * 60, fg='red')
                    click.secho("✗ MAXIMUM ATTEMPTS EXCEEDED - ACCESS DENIED", fg='red', bold=True)
                    click.secho("=" * 60, fg='red')
                    click.echo("\nYou have exceeded the maximum number of password attempts.")
                    click.echo("If you've forgotten your password, check for unencrypted backups in:")
                    click.echo(f"  {DATABASE_FILE.parent}/")
                    click.echo("\nLook for files like:")
                    click.echo("  - database_original_unencrypted.db")
                    click.echo("  - database_backup_*.db")
                    click.echo()
                    sys.exit(1)
    else:
        # First run - database doesn't exist yet
        # Password will be set during 'init' command
        pass

    # If no subcommand is provided, launch TUI
    if ctx.invoked_subcommand is None:
        # Check if database exists (first run)
        if not DATABASE_FILE.exists():
            from leadsauce.utils.dashboard import show_welcome
            show_welcome()
            click.echo("Run 'leadsauce init' to set up the database.")
        else:
            from leadsauce.utils.interactive import interactive_main_menu
            interactive_main_menu()


@cli.command()
@click.pass_context
def init(ctx):
    """
    Initialize LeadSauce CLI configuration

    This will create:
    - Configuration directory (~/.leadsauce/)
    - Default configuration file
    - Encrypted database with AES-256 encryption
    - Required directories
    """
    try:
        click.echo("Initializing LeadSauce CLI...")

        # Create config
        config = init_config()
        click.secho(f"✓ Created configuration at {CONFIG_FILE}", fg='green')

        # Prompt for database encryption password
        password = prompt_for_password(confirm=True, is_first_time=True)
        DatabasePasswordManager.set_password(password)
        click.secho("✓ Database password set", fg='green')

        # Initialize encrypted database
        init_database()
        click.secho(f"✓ Initialized encrypted database", fg='green')

        # Create directories
        APP_DIR.mkdir(parents=True, exist_ok=True)
        (APP_DIR / "logs").mkdir(exist_ok=True)
        (APP_DIR / "plugins").mkdir(exist_ok=True)
        (APP_DIR / "workflows").mkdir(exist_ok=True)
        click.secho(f"✓ Created directories in {APP_DIR}", fg='green')

        click.echo()
        click.secho("Your database is now encrypted with AES-256!", fg='green', bold=True)
        click.echo("You will need to enter your password every time you launch LeadSauce.")
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
def encrypt():
    """Encrypt an existing unencrypted database

    This command will convert your existing unencrypted database to use
    AES-256 encryption. A backup will be automatically created.

    After encryption, you will need to enter a password every time you
    launch LeadSauce.

    Example:
        leadsauce encrypt
    """
    import shutil
    from datetime import datetime

    click.echo()
    click.secho("LeadSauce Database Encryption", fg='cyan', bold=True)
    click.echo("=" * 60)
    click.echo()

    # Check if database exists
    if not DATABASE_FILE.exists():
        click.secho("✗ No database found. Nothing to encrypt.", fg='yellow')
        click.echo("Run 'leadsauce init' to create a new encrypted database.")
        return

    # Check if database is already encrypted (try to open without password)
    try:
        import sqlite3
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        # If we can open it without password, it's not encrypted
    except Exception:
        click.secho("✗ Database appears to be already encrypted.", fg='red')
        click.echo("You don't need to encrypt it again.")
        return

    click.echo(f"Database location: {DATABASE_FILE}")
    click.echo()
    click.secho("⚠ WARNING: This will encrypt your database with AES-256 encryption.", fg='yellow', bold=True)
    click.echo("You will need to enter a password every time you launch LeadSauce.")
    click.secho("\nIMPORTANT: There is no password recovery. Keep it safe!", fg='yellow', bold=True)
    click.echo()

    if not click.confirm("Do you want to continue?"):
        click.echo("Encryption cancelled.")
        return

    # Create backup
    backup_path = DATABASE_FILE.parent / f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    click.echo(f"\nCreating backup at: {backup_path}")
    shutil.copy2(DATABASE_FILE, backup_path)
    click.secho("✓ Backup created successfully", fg='green')

    # Get password for encryption
    click.echo()
    password = prompt_for_password(confirm=True, is_first_time=True)

    # Try to import sqlcipher3
    try:
        from pysqlcipher3 import dbapi2 as sqlcipher
    except ImportError:
        click.secho("\n✗ Error: sqlcipher3-binary is not installed.", fg='red')
        click.echo("Please install it with: pip install -r requirements.txt")
        return

    # Create encrypted database
    import sqlite3
    encrypted_path = DATABASE_FILE.parent / "database_encrypted.db"

    try:
        click.echo("\nEncrypting database...")

        # Connect to unencrypted database
        source_conn = sqlite3.connect(DATABASE_FILE)

        # Connect to new encrypted database
        dest_conn = sqlcipher.connect(str(encrypted_path))
        dest_cursor = dest_conn.cursor()

        # Set encryption key
        dest_cursor.execute(f"PRAGMA key = '{password}'")

        # Copy schema and data
        click.echo("Copying database schema and data...")

        for line in source_conn.iterdump():
            if line not in ('BEGIN;', 'COMMIT;'):
                try:
                    dest_cursor.execute(line)
                except Exception as e:
                    if 'sqlite_sequence' not in str(e):
                        pass  # Ignore internal tables

        dest_conn.commit()
        dest_conn.close()
        source_conn.close()

        click.secho("✓ Database encrypted successfully", fg='green')

        # Verify encrypted database
        click.echo("\nVerifying encrypted database...")
        verify_conn = sqlcipher.connect(str(encrypted_path))
        verify_cursor = verify_conn.cursor()
        verify_cursor.execute(f"PRAGMA key = '{password}'")
        verify_cursor.execute("SELECT count(*) FROM sqlite_master")
        table_count = verify_cursor.fetchone()[0]
        verify_conn.close()

        click.secho(f"✓ Verification successful ({table_count} tables found)", fg='green')

        # Replace original with encrypted version
        click.echo("\nReplacing original database with encrypted version...")
        original_backup = DATABASE_FILE.parent / "database_original_unencrypted.db"
        shutil.move(DATABASE_FILE, original_backup)
        shutil.move(encrypted_path, DATABASE_FILE)

        click.echo()
        click.secho("=" * 60, fg='green')
        click.secho("✓ Database encryption complete!", fg='green', bold=True)
        click.secho("=" * 60, fg='green')
        click.echo()
        click.echo("Backups created:")
        click.echo(f"  - Timestamped backup: {backup_path.name}")
        click.echo(f"  - Original unencrypted: {original_backup.name}")
        click.echo()
        click.secho("You will now need to enter your password every time you launch LeadSauce.", fg='cyan')
        click.echo()

    except Exception as e:
        click.secho(f"\n✗ Encryption failed: {str(e)}", fg='red')
        if encrypted_path.exists():
            encrypted_path.unlink()
        click.echo("\nYour original database is still intact.")
        click.echo(f"A backup was created at: {backup_path}")
        sys.exit(1)


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
from leadsauce.commands import profile, company, export, import_data, goal
cli.add_command(profile.profile)
cli.add_command(company.company)
cli.add_command(export.export)
cli.add_command(import_data.import_cmd)
cli.add_command(goal.goal)

# Note: Additional command groups will be added as they are implemented:
# from leadsauce.commands import interaction, reminder, tag, team, etc.


if __name__ == '__main__':
    cli(obj={})
