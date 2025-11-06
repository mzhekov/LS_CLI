# Reminders Table Migration

## Overview

This migration adds new columns to the `reminders` table to support linking reminders to multiple entity types (companies, tasks, and goals), in addition to the existing profile links.

## What's Changed

### New Columns Added:
- `company_id` - Link reminders to companies
- `task_id` - Link reminders to tasks
- `goal_id` - Link reminders to goals

### Behavior Changes:
- `profile_id` is now **optional** (nullable)
- Reminders can now be linked to any combination of: profiles, companies, tasks, or goals
- At least one entity can be linked, or none (standalone reminders)

## Running the Migration

### Method 1: Using the Migration Script (Recommended)

```bash
cd /home/user/LS_CLI
python migrate_reminders.py
```

This script will:
1. Check your database configuration
2. Verify which columns need to be added
3. Add missing columns safely
4. Create appropriate indexes
5. Verify the migration succeeded

### Method 2: Manual SQL (Advanced Users)

If you need to run the migration manually:

```sql
-- Add new columns
ALTER TABLE reminders ADD COLUMN company_id INTEGER;
ALTER TABLE reminders ADD COLUMN task_id INTEGER;
ALTER TABLE reminders ADD COLUMN goal_id INTEGER;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_reminders_company_id ON reminders(company_id);
CREATE INDEX IF NOT EXISTS ix_reminders_task_id ON reminders(task_id);
CREATE INDEX IF NOT EXISTS ix_reminders_goal_id ON reminders(goal_id);
```

## After Migration

Once the migration is complete, you can:

1. **Create reminders linked to companies**: Set meeting reminders for client companies
2. **Create reminders linked to tasks**: Set deadline reminders for specific tasks
3. **Create reminders linked to goals**: Set milestone reminders for goal tracking
4. **Create reminders linked to profiles**: Continue using the existing profile-based reminders

## Troubleshooting

### "Database file not found"
- Run the LeadSauce application first to create the database
- Check your database configuration in `~/.config/leadsauce/config.yaml`

### "Column already exists"
- The migration script checks for existing columns and skips them
- This is safe and means your database is already up to date

### "Permission denied"
- Ensure you have write access to the database file
- Check file permissions: `ls -l ~/.local/share/leadsauce/leadsauce.db`

### Migration fails partway through
- The script creates columns one at a time
- If it fails, you can safely re-run it - it will skip columns that already exist
- Check the error message for specific issues

## Rollback

To revert this migration (if needed):

**⚠️ WARNING: This will delete all reminders linked to companies, tasks, and goals**

```sql
-- Remove indexes
DROP INDEX IF EXISTS ix_reminders_company_id;
DROP INDEX IF EXISTS ix_reminders_task_id;
DROP INDEX IF EXISTS ix_reminders_goal_id;

-- Note: SQLite doesn't support DROP COLUMN directly
-- You would need to recreate the table without these columns
-- It's recommended to backup your database before attempting rollback
```

## Support

If you encounter issues:
1. Check the error message carefully
2. Verify your database configuration
3. Ensure you have the latest code from the repository
4. Create an issue on GitHub with the error details
