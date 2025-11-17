# Debug Mode - LeadSauce CLI

## Overview

The LeadSauce CLI now includes a comprehensive debug logging system that helps you track and understand all operations happening in the system. This is particularly useful for testing and troubleshooting bugs.

## Features

- **Keyboard Shortcut**: Toggle debug mode on/off with `Ctrl+D` in the TUI
- **CLI Flag**: Use `--debug` flag when launching from command line
- **Comprehensive Logging**: Logs all operations to file
- **Real-time Toggle**: Switch between DEBUG and INFO levels without restarting

## Usage

### Method 1: Keyboard Shortcut (TUI)

When running the interactive TUI:

1. Press **`Ctrl+D`** at any time to toggle debug mode
2. A confirmation message will appear showing the current state:
   - `✓ DEBUG MODE ENABLED` - All operations will be logged
   - `✓ DEBUG MODE DISABLED` - Logging level set to INFO
3. The log file location will be displayed when enabled

**Note**: The `Ctrl+D` shortcut works from any view in the TUI (Dashboard, Profiles, Companies, etc.)

### Method 2: Command Line Flag

Launch the CLI with debug mode enabled:

```bash
# Start TUI with debug mode
leadsauce --debug

# Run specific command with debug mode
leadsauce --debug profile list

# Any command works
leadsauce --debug company create --name "Test Company"
```

## Log File Location

Debug logs are written to:
```
~/.leadsauce/logs/leadsauce.log
```

## What Gets Logged

When debug mode is enabled, the following operations are logged:

### System Operations
- CLI initialization and startup
- Configuration loading
- Database initialization and connections

### Database Operations
- Session creation
- Table creation/verification
- Connection details (without passwords)
- Query executions (via SQLAlchemy)

### Profile Operations
- Profile creation with all details
- Company lookups and creation
- Tag processing and assignment
- Validation errors

### TUI Operations
- View navigation (Dashboard → Profiles, etc.)
- Menu rendering
- User interactions

### Error Handling
- Full stack traces for exceptions
- Error context and details

## Log Format

### File Log Format
```
2025-11-17 14:23:45 | DEBUG    | leadsauce.db:init_database:118 | Initializing database...
2025-11-17 14:23:45 | INFO     | leadsauce.cli:cli:46 | LeadSauce CLI started - Version 1.0.0
```

### Console Log Format
```
[DEBUG] Creating new database session
[INFO] Database initialized successfully
[ERROR] Failed to create profile: Invalid email
```

## Viewing Logs in Real-Time

Monitor logs as they're written:

```bash
# Tail the log file
tail -f ~/.leadsauce/logs/leadsauce.log

# Filter for specific operations
tail -f ~/.leadsauce/logs/leadsauce.log | grep "profile"

# Show only errors
tail -f ~/.leadsauce/logs/leadsauce.log | grep "ERROR"
```

## Log Levels

The system supports two primary log levels:

- **INFO** (default): Important events and operations
- **DEBUG**: Detailed information for debugging

Levels can be toggled between these two states.

## Examples

### Example 1: Debugging Profile Creation

1. Enable debug mode with `Ctrl+D` or `--debug` flag
2. Create a profile through TUI or CLI
3. Check the log file for detailed information:

```log
2025-11-17 14:25:10 | DEBUG    | leadsauce.commands.profile:create_profile:71 | Creating profile: John Doe, seniority: senior
2025-11-17 14:25:10 | DEBUG    | leadsauce.commands.profile:create_profile:79 | Looking up company: Acme Corp
2025-11-17 14:25:10 | DEBUG    | leadsauce.commands.profile:create_profile:94 | Found existing company: Acme Corp (ID: 5)
2025-11-17 14:25:10 | DEBUG    | leadsauce.commands.profile:create_profile:126 | Profile John Doe added to session (ID: 42)
2025-11-17 14:25:10 | DEBUG    | leadsauce.commands.profile:create_profile:131 | Processing 2 tags: ['tech', 'manager']
2025-11-17 14:25:10 | INFO     | leadsauce.commands.profile:create_profile:148 | Profile created successfully: John Doe (ID: 42)
```

### Example 2: Debugging Navigation Issues

1. Enable debug mode with `Ctrl+D`
2. Navigate through different views
3. Log shows navigation flow:

```log
2025-11-17 14:30:05 | INFO     | leadsauce.interactive:interactive_main_menu:314 | Starting interactive TUI main menu
2025-11-17 14:30:05 | DEBUG    | leadsauce.interactive:interactive_main_menu:319 | Rendering view: Dashboard
2025-11-17 14:30:15 | DEBUG    | leadsauce.interactive:interactive_main_menu:330 | Navigating from Dashboard to Profiles
2025-11-17 14:30:15 | DEBUG    | leadsauce.interactive:interactive_main_menu:319 | Rendering view: Profiles
```

## Keyboard Shortcuts Summary

In the TUI, the following global shortcuts are available:

- **`Ctrl+K`** - Quick Claude Command
- **`Ctrl+R`** - View Claude Results
- **`Ctrl+D`** - Toggle Debug Logging *(NEW)*
- **Number Keys (1-9, 0)** - Navigate to different sections

## Troubleshooting

### Debug Mode Doesn't Seem to Work

1. Check that you're using a recent version of LeadSauce
2. Verify the log file exists: `ls -la ~/.leadsauce/logs/`
3. Check file permissions: `ls -l ~/.leadsauce/logs/leadsauce.log`

### Log File Getting Too Large

The logging system includes rotation settings in `~/.leadsauce/config.yaml`:

```yaml
logging:
  level: "INFO"
  file: "~/.leadsauce/logs/leadsauce.log"
  max_size: 10485760    # 10MB
  backup_count: 5       # Keep 5 backup files
```

### Can't Find Specific Information in Logs

Use grep to filter logs:

```bash
# Find all profile-related logs
grep "profile" ~/.leadsauce/logs/leadsauce.log

# Find errors only
grep "ERROR" ~/.leadsauce/logs/leadsauce.log

# Find operations for specific profile
grep "John Doe" ~/.leadsauce/logs/leadsauce.log
```

## Tips for Testing

1. **Start Fresh**: Clear old logs before testing:
   ```bash
   rm ~/.leadsauce/logs/leadsauce.log
   ```

2. **Enable Debug First**: Turn on debug mode before performing the operation you want to test

3. **Compare Modes**: Run the same operation in both INFO and DEBUG mode to see the difference

4. **Share Logs**: When reporting bugs, include relevant log excerpts (remember to remove sensitive data!)

## Privacy Note

Debug logs may contain sensitive information such as:
- Email addresses
- Phone numbers
- Names and company information
- Database paths

Always review logs before sharing them, and remove or redact sensitive information.

## Configuration

Debug logging can also be configured via environment variables:

```bash
# Set default log level
export LEADSAUCE_LOG_LEVEL=DEBUG

# Then run normally
leadsauce
```

---

**Happy Debugging!** 🐛🔍
