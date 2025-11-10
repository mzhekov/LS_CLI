"""
Database encryption and password management

This module handles secure password prompts and database encryption key management.
The password is stored only in memory and is required on every app launch for encrypted databases.
Encryption is optional - users can choose to use an unencrypted database if preferred.
"""

import sys
import getpass
from typing import Optional
import click


class DatabasePasswordManager:
    """Manages database encryption password in memory only"""

    _password: Optional[str] = None
    _is_initialized: bool = False

    @classmethod
    def set_password(cls, password: str):
        """Set the database password (stored in memory only)"""
        cls._password = password
        cls._is_initialized = True

    @classmethod
    def get_password(cls) -> Optional[str]:
        """Get the database password"""
        return cls._password

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if password has been set"""
        return cls._is_initialized

    @classmethod
    def clear_password(cls):
        """Clear the password from memory"""
        cls._password = None
        cls._is_initialized = False


def is_database_encrypted(database_path) -> bool:
    """
    Check if a database file is encrypted

    Args:
        database_path: Path to the database file

    Returns:
        True if encrypted, False if unencrypted or doesn't exist
    """
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path(database_path)
        if not db_path.exists():
            return False

        # Try to open with standard SQLite
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        # If we can open it, it's not encrypted
        return False
    except Exception:
        # If we can't open it, it's likely encrypted (or corrupted)
        return True


def prompt_for_password(confirm: bool = False, is_first_time: bool = False) -> str:
    """
    Prompt user for database password

    Args:
        confirm: If True, ask for password twice to confirm
        is_first_time: If True, show first-time setup message

    Returns:
        The password entered by user
    """
    try:
        if is_first_time:
            click.echo()
            click.secho("Database Encryption Setup", fg='cyan', bold=True)
            click.echo("Your database will be encrypted with AES-256 encryption.")
            click.echo("You will need to enter this password every time you launch LeadSauce.")
            click.secho("\nIMPORTANT: There is no password recovery. Keep it safe!", fg='yellow', bold=True)
            click.echo()

        while True:
            if is_first_time:
                password = getpass.getpass("Create database password: ")
            else:
                password = getpass.getpass("Enter database password: ")

            if not password:
                click.secho("Password cannot be empty. Please try again.", fg='red')
                continue

            if is_first_time and len(password) < 8:
                click.secho("Password must be at least 8 characters. Please try again.", fg='red')
                continue

            if confirm:
                password_confirm = getpass.getpass("Confirm database password: ")
                if password != password_confirm:
                    click.secho("Passwords do not match. Please try again.", fg='red')
                    continue

            return password

    except (KeyboardInterrupt, EOFError):
        click.echo("\n\nPassword prompt cancelled. Exiting...")
        sys.exit(0)


def verify_password_works(database_url: str, password: str) -> bool:
    """
    Verify that the password can decrypt the database

    Args:
        database_url: SQLite database URL
        password: Password to test

    Returns:
        True if password is correct, False otherwise
    """
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import StaticPool

        # Extract file path from URL
        if database_url.startswith('sqlite:///'):
            db_path = database_url.replace('sqlite:///', '')
        else:
            return False

        # Try to open with password
        engine = create_engine(
            f'sqlite+pysqlcipher://:{password}@/{db_path}',
            connect_args={
                "check_same_thread": False,
            },
            poolclass=StaticPool,
            echo=False
        )

        # Try a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        engine.dispose()
        return True

    except Exception:
        return False
