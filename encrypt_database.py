#!/usr/bin/env python3
"""
Database Encryption Migration Script

This script encrypts an existing unencrypted LeadSauce database.
It creates a backup of the original database and then creates an encrypted copy.

Usage:
    python encrypt_database.py
"""

import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
import click


def encrypt_existing_database():
    """Migrate existing unencrypted database to encrypted format"""

    # Import after ensuring we're in the right directory
    try:
        from leadsauce.utils.constants import DATABASE_FILE, APP_DIR
        from leadsauce.utils.encryption import prompt_for_password
    except ImportError:
        click.secho("Error: Could not import LeadSauce modules. Make sure you're in the project directory.", fg='red')
        sys.exit(1)

    click.echo()
    click.secho("LeadSauce Database Encryption Migration", fg='cyan', bold=True)
    click.echo("=" * 60)
    click.echo()

    # Check if database exists
    if not DATABASE_FILE.exists():
        click.secho("✗ No database found at: " + str(DATABASE_FILE), fg='yellow')
        click.echo("Nothing to migrate. Run 'leadsauce init' to create a new encrypted database.")
        sys.exit(0)

    # Check if database is already encrypted
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        # If we can open it without password, it's not encrypted
    except sqlite3.DatabaseError:
        click.secho("✗ Database appears to be already encrypted or corrupted.", fg='red')
        click.echo("If you've forgotten your password, you'll need to restore from a backup.")
        sys.exit(1)

    click.echo(f"Database location: {DATABASE_FILE}")
    click.echo()

    # Warn user
    click.secho("⚠ WARNING: This will encrypt your database with AES-256 encryption.", fg='yellow', bold=True)
    click.echo("You will need to enter a password every time you launch LeadSauce.")
    click.secho("\nIMPORTANT: There is no password recovery. Keep it safe!", fg='yellow', bold=True)
    click.echo()

    if not click.confirm("Do you want to continue?"):
        click.echo("Migration cancelled.")
        sys.exit(0)

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
        click.echo("Please install it with: pip install sqlcipher3-binary")
        sys.exit(1)

    # Create encrypted database
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

        # Get the database dump
        for line in source_conn.iterdump():
            if line not in ('BEGIN;', 'COMMIT;'):
                try:
                    dest_cursor.execute(line)
                except Exception as e:
                    # Skip sqlite_sequence and other internal tables
                    if 'sqlite_sequence' not in line:
                        click.secho(f"Warning: {e}", fg='yellow')

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
        click.echo(f"  - Timestamped backup: {backup_path}")
        click.echo(f"  - Original unencrypted: {original_backup}")
        click.echo()
        click.secho("You will now need to enter your password every time you launch LeadSauce.", fg='cyan')
        click.echo()

    except Exception as e:
        click.secho(f"\n✗ Encryption failed: {str(e)}", fg='red')

        # Clean up
        if encrypted_path.exists():
            encrypted_path.unlink()

        click.echo("\nYour original database is still intact.")
        click.echo(f"A backup was created at: {backup_path}")
        sys.exit(1)


if __name__ == '__main__':
    encrypt_existing_database()
