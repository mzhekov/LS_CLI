#!/usr/bin/env python3
"""
Database migration script to remove user_id columns from all tables.
This fixes the schema after removing the authentication system.
"""

import sqlite3
import sys
from pathlib import Path

# Import database path from config
try:
    from leadsauce.utils.db import DATABASE_FILE
    DB_PATH = DATABASE_FILE
except ImportError:
    # Fallback to default path
    DB_PATH = Path.home() / '.leadsauce' / 'database.db'

if not DB_PATH.exists():
    print(f"Database not found at {DB_PATH}")
    print("Nothing to migrate.")
    sys.exit(0)

print(f"Migrating database at: {DB_PATH}")
print("Removing user_id columns from all tables...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List of tables and their user_id columns to remove
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

migrated_tables = []
skipped_tables = []

for table_name, column_name in tables_to_fix.items():
    try:
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            skipped_tables.append(f"{table_name} (table doesn't exist)")
            continue

        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if column_name not in column_names:
            skipped_tables.append(f"{table_name}.{column_name} (column doesn't exist)")
            continue

        print(f"\nMigrating {table_name}...")

        # Get all column definitions except the user_id column
        columns_to_keep = [col for col in columns if col[1] != column_name]

        # Build new table schema
        column_defs = []
        for col in columns_to_keep:
            col_name = col[1]
            col_type = col[2]
            not_null = " NOT NULL" if col[3] else ""
            default = f" DEFAULT {col[4]}" if col[4] is not None else ""
            pk = " PRIMARY KEY" if col[5] else ""
            column_defs.append(f"{col_name} {col_type}{not_null}{default}{pk}")

        # Create new table with fixed schema
        new_table_sql = f"""
        CREATE TABLE {table_name}_new (
            {', '.join(column_defs)}
        )
        """
        cursor.execute(new_table_sql)

        # Copy data from old table to new table
        keep_column_names = [col[1] for col in columns_to_keep]
        cursor.execute(f"""
            INSERT INTO {table_name}_new ({', '.join(keep_column_names)})
            SELECT {', '.join(keep_column_names)}
            FROM {table_name}
        """)

        # Drop old table and rename new one
        cursor.execute(f"DROP TABLE {table_name}")
        cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")

        migrated_tables.append(f"{table_name}.{column_name}")
        print(f"  ✓ Removed {column_name} from {table_name}")

    except Exception as e:
        print(f"  ✗ Error migrating {table_name}: {e}")
        conn.rollback()
        conn.close()
        sys.exit(1)

# Commit all changes
conn.commit()
conn.close()

print("\n" + "="*60)
print("Migration complete!")
print("="*60)

if migrated_tables:
    print("\nMigrated columns:")
    for item in migrated_tables:
        print(f"  ✓ {item}")

if skipped_tables:
    print("\nSkipped (already correct):")
    for item in skipped_tables:
        print(f"  - {item}")

print("\nYou can now use LeadSauce CLI normally.")
print("Run: leadsauce tui")
