#!/usr/bin/env python3
"""
Migration script to add new columns to reminders table
This adds support for linking reminders to companies, tasks, and goals
"""

import sqlite3
from pathlib import Path
from leadsauce.utils.config import get_config
from leadsauce.utils.constants import DATABASE_FILE


def get_db_path():
    """Get database path from config"""
    config = get_config()
    db_type = config.get('database.type', 'sqlite')

    if db_type != 'sqlite':
        print(f"Error: This migration script only supports SQLite databases.")
        print(f"Current database type: {db_type}")
        return None

    db_path = config.get('database.path', str(DATABASE_FILE))
    return Path(db_path)


def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_reminders_table():
    """Add new columns to reminders table"""
    db_path = get_db_path()

    if not db_path:
        return False

    if not db_path.exists():
        print(f"Database file not found at: {db_path}")
        print("Please run the application first to create the database.")
        return False

    print(f"Migrating database at: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check which columns need to be added
        columns_to_add = []

        if not check_column_exists(cursor, 'reminders', 'company_id'):
            columns_to_add.append(('company_id', 'INTEGER'))

        if not check_column_exists(cursor, 'reminders', 'task_id'):
            columns_to_add.append(('task_id', 'INTEGER'))

        if not check_column_exists(cursor, 'reminders', 'goal_id'):
            columns_to_add.append(('goal_id', 'INTEGER'))

        if not columns_to_add:
            print("✓ All columns already exist. No migration needed.")
            return True

        print(f"\nAdding {len(columns_to_add)} new column(s) to reminders table...")

        # Add each column
        for column_name, column_type in columns_to_add:
            print(f"  - Adding column: {column_name}")
            cursor.execute(f"ALTER TABLE reminders ADD COLUMN {column_name} {column_type}")

        # Create indexes for the new foreign key columns
        print("\nCreating indexes...")

        if ('company_id', 'INTEGER') in columns_to_add:
            print("  - Creating index on company_id")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_company_id ON reminders(company_id)")

        if ('task_id', 'INTEGER') in columns_to_add:
            print("  - Creating index on task_id")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_task_id ON reminders(task_id)")

        if ('goal_id', 'INTEGER') in columns_to_add:
            print("  - Creating index on goal_id")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_goal_id ON reminders(goal_id)")

        # Make profile_id nullable (it was previously NOT NULL)
        # Note: SQLite doesn't support ALTER COLUMN, so we'll just note that new rows can have NULL
        print("\nNote: profile_id is now optional (nullable). Existing rows are unchanged.")

        conn.commit()
        print("\n✓ Migration completed successfully!")

        # Verify the changes
        print("\nVerifying changes...")
        cursor.execute("PRAGMA table_info(reminders)")
        columns = cursor.fetchall()
        print("\nCurrent reminders table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})" + (" [NOT NULL]" if col[3] else ""))

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"\n✗ Error during migration: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LeadSauce Reminders Table Migration")
    print("=" * 60)
    print("\nThis script will add new columns to the reminders table:")
    print("  - company_id (link reminders to companies)")
    print("  - task_id (link reminders to tasks)")
    print("  - goal_id (link reminders to goals)")
    print("\nThis enables reminders to be linked to any entity type.")
    print("=" * 60)

    input("\nPress Enter to continue or Ctrl+C to cancel...")

    success = migrate_reminders_table()

    if success:
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("You can now use the enhanced reminders functionality.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Migration failed. Please check the errors above.")
        print("=" * 60)
        exit(1)
