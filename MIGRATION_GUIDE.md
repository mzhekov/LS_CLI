# Database Migration Guide

## Issue: "NOT NULL constraint failed: companies.user_id"

If you see this error, it means your database was created with an older version that included authentication. The authentication system has been removed, but your database still has the old schema.

## Solution: Run the Migration Script

### Quick Fix

Run this command from the LS_CLI directory:

```bash
python migrate_db.py
```

This will automatically:
- Remove all `user_id` columns from tables
- Remove `uploaded_by_id` from documents
- Remove `created_by_id` from teams
- Preserve all your existing data

### What Gets Changed

The script modifies these tables:
- `companies` - removes user_id
- `profiles` - removes user_id
- `tags` - removes user_id
- `interactions` - removes user_id
- `reminders` - removes user_id
- `documents` - removes uploaded_by_id
- `activities` - removes user_id
- `teams` - removes created_by_id

### Alternative: Fresh Start

If you don't have important data and want to start fresh:

```bash
# Delete the old database
rm ~/.leadsauce/leadsauce.db

# Run LeadSauce - it will create a new database with correct schema
leadsauce tui
```

## Verify Migration

After migration, test by adding a new profile:

```bash
leadsauce tui
# Press [2] for Profiles
# Select "Add New Profile"
# Fill in the form
```

If it works without errors, migration was successful!
