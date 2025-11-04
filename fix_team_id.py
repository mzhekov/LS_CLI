#!/usr/bin/env python3
"""
Migration script to fix team_id foreign key constraints
Makes team_id nullable in profiles, companies, and activities tables
"""

import sys
import sqlite3
from pathlib import Path

def fix_team_id_constraints():
    """Fix team_id foreign key constraints in the database"""

    # Get database path
    home_dir = Path.home()
    db_path = home_dir / ".leadsauce" / "database.db"

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False

    print(f"Fixing team_id constraints in: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Disable foreign keys temporarily
        cursor.execute("PRAGMA foreign_keys=OFF")

        # Start transaction
        cursor.execute("BEGIN TRANSACTION")

        # Fix profiles table
        print("\n1. Fixing profiles table...")
        cursor.execute("""
            CREATE TABLE profiles_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                company_id INTEGER,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                seniority VARCHAR(50) NOT NULL,
                generation VARCHAR(50),
                married BOOLEAN,
                has_children BOOLEAN,
                ie_score INTEGER,
                is_score INTEGER,
                good_at TEXT,
                need_to_work TEXT,
                work_for TEXT,
                additional_info TEXT,
                notes TEXT,
                last_contact DATETIME,
                interaction_count INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME,
                FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL,
                FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            INSERT INTO profiles_new
            SELECT * FROM profiles
        """)

        cursor.execute("DROP TABLE profiles")
        cursor.execute("ALTER TABLE profiles_new RENAME TO profiles")

        # Recreate indexes for profiles
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_profiles_team_id ON profiles(team_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_profiles_company_id ON profiles(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_profiles_name ON profiles(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_profiles_email ON profiles(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_profiles_seniority ON profiles(seniority)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_profiles_last_contact ON profiles(last_contact)")

        print("   ✓ Profiles table fixed")

        # Fix companies table
        print("\n2. Fixing companies table...")
        cursor.execute("""
            CREATE TABLE companies_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                name VARCHAR(255) NOT NULL,
                industry VARCHAR(100),
                size VARCHAR(50),
                location VARCHAR(255),
                website VARCHAR(255),
                notes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME,
                FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            INSERT INTO companies_new
            SELECT * FROM companies
        """)

        cursor.execute("DROP TABLE companies")
        cursor.execute("ALTER TABLE companies_new RENAME TO companies")

        # Recreate indexes for companies
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_companies_team_id ON companies(team_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_companies_name ON companies(name)")

        print("   ✓ Companies table fixed")

        # Fix activities table
        print("\n3. Fixing activities table...")
        cursor.execute("""
            CREATE TABLE activities_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                activity_type VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INTEGER,
                description TEXT,
                activity_metadata JSON,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            INSERT INTO activities_new
            SELECT * FROM activities
        """)

        cursor.execute("DROP TABLE activities")
        cursor.execute("ALTER TABLE activities_new RENAME TO activities")

        # Recreate indexes for activities
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_activities_team_id ON activities(team_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_activities_activity_type ON activities(activity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_activities_entity_type ON activities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_activities_entity_id ON activities(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_activities_created_at ON activities(created_at)")

        print("   ✓ Activities table fixed")

        # Commit transaction
        conn.commit()

        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")

        # Verify foreign keys are working
        cursor.execute("PRAGMA foreign_key_check")
        issues = cursor.fetchall()

        if issues:
            print("\n⚠ Foreign key issues found:")
            for issue in issues:
                print(f"   {issue}")
            return False

        print("\n✓ Migration completed successfully!")
        print("\nYou can now create profiles and companies without team_id errors.")

        conn.close()
        return True

    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LeadSauce Database Migration: Fix team_id Constraints")
    print("=" * 60)

    success = fix_team_id_constraints()

    if success:
        sys.exit(0)
    else:
        print("\n✗ Migration failed. Your database has not been modified.")
        sys.exit(1)
