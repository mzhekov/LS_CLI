# Database Encryption

LeadSauce now supports **AES-256 database encryption** to protect your high-value contact and relationship data.

## Overview

- **Encryption**: AES-256 bit encryption using SQLCipher
- **Password Required**: You must enter a password every time you launch LeadSauce
- **No Recovery**: There is no password recovery mechanism - keep your password safe!
- **Automatic**: All database operations are transparently encrypted/decrypted

## For New Installations

When you initialize LeadSauce for the first time, you'll be prompted to create an encryption password:

```bash
leadsauce init
```

You will see:
1. Password creation prompt (with confirmation)
2. Minimum 8 characters required
3. Password stored only in memory (never written to disk)

## For Existing Databases

If you already have a LeadSauce database and want to encrypt it:

```bash
leadsauce encrypt
```

This command will:
1. Create automatic backups of your database
2. Prompt you to create an encryption password
3. Convert your database to use AES-256 encryption
4. Verify the encrypted database works correctly

**Backups created:**
- `database_backup_YYYYMMDD_HHMMSS.db` - Timestamped backup
- `database_original_unencrypted.db` - Original unencrypted version

## Daily Usage

Every time you launch LeadSauce, you'll be prompted for your password:

```bash
leadsauce
# or
leadsauce tui
```

You will see:
```
Enter database password:
```

**Security Features:**
- Maximum 3 password attempts before access is denied
- Password stored only in memory during the session
- Password cleared when the application exits

## Security Best Practices

1. **Choose a Strong Password**: Use at least 8 characters with a mix of letters, numbers, and symbols
2. **Keep It Safe**: Store your password in a secure password manager
3. **No Recovery**: If you forget your password, you'll need to restore from an unencrypted backup
4. **Backups**: Keep your backup files in a secure location

## Technical Details

- **Encryption Algorithm**: AES-256 in CBC mode
- **Key Derivation**: PBKDF2 (SQLCipher default: 64,000 iterations)
- **Library**: SQLCipher via pysqlcipher3
- **Performance**: Minimal overhead - encryption/decryption is transparent

## Troubleshooting

### "Incorrect password" error
- Make sure you're entering the correct password
- Check for caps lock
- You have 3 attempts before the application exits

### "Database appears to be already encrypted"
- Your database is already encrypted
- Just launch LeadSauce normally and enter your password

### "sqlcipher3-binary is not installed"
- Install dependencies: `pip install -r requirements.txt`

### Lost Password
If you've lost your password:
1. Check if you have unencrypted backups
2. Look for `database_original_unencrypted.db` or timestamped backups
3. Restore from backup and optionally re-encrypt with a new password

## Migration Path

### From Unencrypted to Encrypted

```bash
# 1. Backup your data (optional, but recommended)
cp ~/.leadsauce/database.db ~/leadsauce_backup.db

# 2. Encrypt the database
leadsauce encrypt

# 3. Launch LeadSauce
leadsauce
```

### From Encrypted to Unencrypted (Not Recommended)

If you need to remove encryption:

```bash
# 1. Locate your unencrypted backup
ls ~/.leadsauce/database_original_unencrypted.db

# 2. Stop LeadSauce if running

# 3. Replace encrypted database with unencrypted backup
cp ~/.leadsauce/database_original_unencrypted.db ~/.leadsauce/database.db

# 4. Update the code to not use encryption (modify source)
```

## FAQ

**Q: Can I change my password?**
A: Not directly. You would need to decrypt to a backup and re-encrypt with a new password.

**Q: Is my password stored anywhere?**
A: No. The password is only stored in memory during your session and is cleared when you exit.

**Q: What if someone gets access to my database file?**
A: Without your password, the database file is encrypted and unreadable.

**Q: Does this slow down the application?**
A: The performance impact is minimal. SQLCipher's encryption/decryption is highly optimized.

**Q: Can I share my database with teammates?**
A: Yes, but you'll need to share the password securely. Consider using a secure password sharing tool.

## Support

If you encounter issues with database encryption:
1. Check this documentation
2. Review the troubleshooting section
3. Check your backups in `~/.leadsauce/`
4. Open an issue on GitHub with error details (but never include your password!)
