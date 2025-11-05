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

        # Make profile_id nullable by recreating the table
        # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
        print("\nMaking profile_id nullable (this requires recreating the table)...")

        # Check if profile_id has NOT NULL constraint
        cursor.execute("PRAGMA table_info(reminders)")
        columns_info = cursor.fetchall()
        profile_id_notnull = False
        for col in columns_info:
            if col[1] == 'profile_id' and col[3] == 1:  # col[3] is notnull flag
                profile_id_notnull = True
                break

        if profile_id_notnull:
            print("  - Recreating reminders table with nullable profile_id...")

            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE reminders_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER,
                    company_id INTEGER,
                    task_id INTEGER,
                    goal_id INTEGER,
                    parent_reminder_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    message TEXT,
                    reminder_date DATETIME NOT NULL,
                    priority VARCHAR(50) DEFAULT 'medium',
                    category VARCHAR(50) DEFAULT 'general',
                    completed BOOLEAN DEFAULT 0,
                    completed_at DATETIME,
                    completion_note TEXT,
                    notification_sent BOOLEAN DEFAULT 0,
                    is_recurring BOOLEAN DEFAULT 0,
                    recurrence_pattern VARCHAR(50),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_reminder_id) REFERENCES reminders(id) ON DELETE SET NULL
                )
            """)

            # Copy data from old table
            print("  - Copying existing data...")
            cursor.execute("""
                INSERT INTO reminders_new
                SELECT * FROM reminders
            """)

            # Drop old table
            print("  - Dropping old table...")
            cursor.execute("DROP TABLE reminders")

            # Rename new table
            print("  - Renaming new table...")
            cursor.execute("ALTER TABLE reminders_new RENAME TO reminders")

            # Recreate indexes
            print("  - Recreating indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_profile_id ON reminders(profile_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_company_id ON reminders(company_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_task_id ON reminders(task_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_goal_id ON reminders(goal_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_reminder_date ON reminders(reminder_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_priority ON reminders(priority)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_category ON reminders(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_reminders_completed ON reminders(completed)")

            print("  - ✓ profile_id is now nullable")
        else:
            print("  - profile_id is already nullable")

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
