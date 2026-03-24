# LeadSauce CLI — User Guide

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Core Concepts](#core-concepts)
5. [Commands Reference](#commands-reference)
   - [Profile Management](#profile-management)
   - [Company Management](#company-management)
   - [Goal & Task Management](#goal--task-management)
   - [Interaction Logging](#interaction-logging)
   - [Reminders](#reminders)
   - [Tags](#tags)
   - [Teams](#teams)
   - [Documents](#documents)
   - [Import & Export](#import--export)
   - [Analytics & Insights](#analytics--insights)
   - [Configuration](#configuration)
6. [Interactive TUI](#interactive-tui)
7. [AI Assistant](#ai-assistant)
8. [Configuration Reference](#configuration-reference)
9. [Data Models](#data-models)
10. [Tips & Workflows](#tips--workflows)
11. [Troubleshooting](#troubleshooting)

---

## Overview

LeadSauce CLI is a professional network management tool built for power users who prefer terminal-based workflows. It gives you a fast, keyboard-driven interface to manage contacts, companies, goals, tasks, reminders, and interactions — all stored locally in a SQLite database.

Key capabilities:
- Full CRUD for contacts (profiles) and companies
- Goal and task tracking linked to your network
- Interaction history (calls, meetings, emails, notes)
- Reminder system with recurrence and priority
- Tag-based organization
- Team collaboration with role-based access
- Document attachments per contact
- Data import/export (CSV, JSON)
- AI assistant for natural language commands
- Rich interactive TUI with color output

---

## Installation

**Requirements:** Python 3.9+

### From Source

```bash
git clone https://github.com/mzhekov/LS_CLI.git
cd LS_CLI
pip install -e .
```

### With Development Dependencies

```bash
pip install -e ".[dev]"
```

### From PyPI (when published)

```bash
pip install leadsauce-cli
```

---

## Getting Started

### 1. Initialize

Run this once to set up the database and default configuration:

```bash
leadsauce init
```

This creates `~/.leadsauce/` with:
- `database.db` — SQLite database
- `config.yaml` — configuration file

### 2. Launch the Interactive TUI

The recommended way to explore and use the tool:

```bash
leadsauce
# or explicitly:
leadsauce tui
```

### 3. Check the Dashboard

```bash
leadsauce dashboard
```

Shows an overview: total contacts, companies, open goals, upcoming reminders, and recent activity.

### 4. Add Your First Contact

```bash
leadsauce profile create --name "Jane Smith" --seniority director
```

---

## Core Concepts

| Concept | Description |
|---|---|
| **Profile** | A professional contact — the core unit of your network |
| **Company** | An organization; profiles can be linked to companies |
| **Goal** | A high-level objective (e.g. "Close deal with Acme Corp") |
| **Task** | A concrete action item, optionally linked to a goal |
| **Interaction** | A logged event — call, meeting, email, or note with a contact |
| **Reminder** | A scheduled notification, supports recurrence |
| **Tag** | A label used to categorize profiles and goals |
| **Team** | A shared workspace for collaborating on your network |
| **Document** | A file attachment stored against a profile |

---

## Commands Reference

All commands follow the pattern:

```
leadsauce <group> <action> [options]
```

Run `leadsauce --help` or `leadsauce <group> --help` for full option lists.

---

### Profile Management

Profiles represent your professional contacts.

```bash
# Create a contact
leadsauce profile create --name "John Doe" --seniority executive

# List all contacts (paginated)
leadsauce profile list

# View a contact's full details
leadsauce profile view <profile_id>

# Edit a contact
leadsauce profile edit <profile_id> --phone "+1-555-0100"

# Delete a contact
leadsauce profile delete <profile_id>
```

**Seniority levels:** `junior`, `mid`, `senior`, `manager`, `director`, `executive`, `c-level`

**Fields available on create/edit:**
- `--name` — Full name (required)
- `--seniority` — Career level
- `--email` — Email address
- `--phone` — Phone number
- `--company` — Company ID to link
- `--generation` — `boomer`, `gen-x`, `millennial`, `gen-z`, etc.
- `--tags` — Comma-separated tag names

---

### Company Management

```bash
# Create a company
leadsauce company create --name "Acme Corp" --industry "SaaS"

# List companies
leadsauce company list

# View company details (includes linked profiles)
leadsauce company view <company_id>

# Edit a company
leadsauce company edit <company_id> --website "https://acme.com"
```

**Fields available:**
- `--name` — Company name (required)
- `--industry` — Industry sector
- `--size` — Employee count range
- `--website` — Website URL
- `--location` — City / country

---

### Goal & Task Management

Goals are high-level objectives. Tasks are the concrete steps to reach them.

```bash
# Create a goal
leadsauce goal create --title "Close Q2 pipeline" --profile 12

# List goals
leadsauce goal list

# Update goal progress
leadsauce goal update <goal_id> --progress 60

# Mark a goal complete
leadsauce goal complete <goal_id>
```

**Goal status values:** `active`, `completed`, `on_hold`, `cancelled`

Tasks and reminders are managed through the TUI (`leadsauce tui` → Tasks / Reminders menu).

---

### Interaction Logging

Record every touchpoint with a contact.

```bash
# Log an interaction (interactive prompt in TUI)
leadsauce interaction add <profile_id> --type call --subject "Q2 check-in"
```

**Interaction types:** `meeting`, `call`, `email`, `note`, `event`

After logging, the contact's "last contacted" date is automatically updated.

---

### Reminders

Create reminders linked to contacts, with optional recurrence.

```bash
# List today's reminders
leadsauce reminder list --today

# Complete a reminder
leadsauce reminder complete <reminder_id> --add-note "Called, left voicemail"
```

Reminders are best managed through the TUI for full field access.

**Priority levels:** `low`, `medium`, `high`

**Categories:** `call`, `email`, `meeting`, `follow-up`, `birthday`, `general`

**Recurrence options:** `daily`, `weekly`, `monthly`, `yearly`

---

### Tags

Tags let you organize and filter contacts and goals.

```bash
# Create a tag
leadsauce tag create --name "VIP"

# List all tags
leadsauce tag list

# Apply a tag to a profile (via TUI or bulk operations)
leadsauce bulk tag --filter "company=Acme Corp" --tags "VIP"
```

---

### Teams

Share your network with collaborators using role-based access.

Team management is handled through the TUI (`leadsauce tui` → Teams).

**Roles:** `owner`, `admin`, `editor`, `viewer`, `member`

---

### Documents

Attach files to profiles for resumes, contracts, proposals, and more.

Document upload and management is handled through the TUI (`leadsauce tui` → Documents).

**Document types:** `resume`, `contract`, `presentation`, `proposal`, `report`, `other`

---

### Import & Export

```bash
# Export profiles to CSV
leadsauce export profiles --format csv --output contacts.csv

# Export companies to CSV
leadsauce export companies --format csv --output companies.csv

# Export to JSON
leadsauce export profiles --format json --output contacts.json

# Import contacts from CSV
leadsauce import profiles --file contacts.csv
```

Supported export targets: `profiles`, `companies`, `tasks`, `interactions`, `reminders`, `teams`, `documents`

---

### Analytics & Insights

```bash
# Overall dashboard
leadsauce dashboard

# Network health score
leadsauce insights health

# Find neglected contacts (no contact in > 60 days)
leadsauce insights neglected --threshold 60

# Contact statistics
leadsauce stats
```

---

### Configuration

```bash
# List all configuration values
leadsauce config list

# Set a configuration value
leadsauce config set output.format table
leadsauce config set output.color true
leadsauce config set reminders.check_interval 15
```

---

## Interactive TUI

Launch with:

```bash
leadsauce
```

The TUI provides a menu-driven interface for all features.

### Navigation

| Key | Action |
|---|---|
| Arrow keys / number | Navigate menu items |
| `Enter` | Select item |
| `Backspace` × 2 | Go back / quit menu |
| `Ctrl+K` | Quick command palette |
| `Ctrl+R` | View last results |
| Single letter shortcuts | Jump to section (shown in menu) |

### Main Menu Sections

- **Profiles** — Browse, create, and edit contacts
- **Companies** — Manage organizations
- **Goals** — Track objectives and progress
- **Tasks** — Manage individual action items
- **Reminders** — View and complete reminders
- **Interactions** — Log and browse communication history
- **Tags** — Manage labels
- **Teams** — Collaboration workspace
- **Relationships** — Visualize connections between profiles
- **Documents** — File management
- **Analytics** — Network insights and health

---

## AI Assistant

LeadSauce includes an AI assistant that understands natural language and can execute real commands on your behalf.

### Supported AI Tools

- Claude Code
- Codex CLI
- Aider

### Modes

**Conversational:** Ask questions about your network, get suggestions.

**System-Aware:** The AI can actually perform operations — create reminders, log interactions, add contacts — after your confirmation.

### Example

```
You: "Remind me to follow up with Sarah about the Q4 proposal next Tuesday"

AI: I'll create a reminder for you:
    leadsauce reminder create --profile 42 --title "Follow up with Sarah - Q4 proposal" --due "2026-03-31"

Execute? (y/n): y
✓ Created reminder #87
```

### Natural Language Date Support

The AI understands phrases like:
- "tomorrow"
- "next Friday"
- "in 3 days"
- "end of month"

### Launching

```bash
leadsauce ai
```

Or from the TUI, navigate to the AI Assistant option.

---

## Configuration Reference

Configuration is stored at `~/.leadsauce/config.yaml`.

```yaml
api:
  endpoint: https://api.leadsauce.com
  timeout: 30
  verify_ssl: true

database:
  type: sqlite
  path: ~/.leadsauce/database.db

output:
  format: table        # table | json | csv | text
  color: true
  pagination:
    enabled: true
    limit: 50

email:
  enabled: false
  smtp_server: smtp.gmail.com
  use_tls: true

reminders:
  notification_enabled: true
  notification_lead_time: 15   # minutes before due time
  check_interval: 15           # minutes between checks

ai:
  enabled: true
  default_tool: claude
  tools:
    claude: { enabled: true }
    codex: { enabled: true }
    aider: { enabled: true }

preferences:
  default_seniority: mid
  default_priority: medium
  confirm_delete: true
  auto_sync: false
```

### Environment Variables

| Variable | Description |
|---|---|
| `LEADSAUCE_API_ENDPOINT` | Override API endpoint |
| `LEADSAUCE_DB_URL` | Override database URL |
| `LEADSAUCE_OUTPUT_FORMAT` | Override output format |
| `LEADSAUCE_LOG_LEVEL` | Set log verbosity (`DEBUG`, `INFO`, `WARNING`) |
| `LEADSAUCE_EMAIL_PASSWORD` | SMTP email password |
| `OPENAI_API_KEY` | OpenAI API key for AI features |

---

## Data Models

### Profile Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Full name |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `seniority` | enum | Career level |
| `generation` | enum | Generational cohort |
| `company_id` | FK | Linked company |
| `last_contacted` | date | Date of last logged interaction |
| `ie_score` | int | Introvert/Extrovert score |
| `is_score` | int | Intuitive/Sensing score |
| `good_at` | text | Skills and strengths |
| `tags` | M2M | Associated tags |

### Company Fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Company name |
| `industry` | string | Industry sector |
| `size` | string | Employee count range |
| `website` | string | Website URL |
| `location` | string | Location |

### Relationship Types

`colleague`, `manager`, `reports_to`, `friend`, `mentor`, `mentee`, `client`, `vendor`, `partner`

---

## Tips & Workflows

### Daily Check-in

```bash
# See what's due today
leadsauce reminder list --today

# Review the dashboard
leadsauce dashboard
```

### After a Meeting

```bash
# Log the interaction
leadsauce interaction add <profile_id> --type meeting --subject "Q2 planning"

# Set a follow-up reminder
leadsauce reminder create --profile <profile_id> --title "Send meeting notes" --due "tomorrow"
```

### Network Health

```bash
# Find contacts you haven't spoken to in 60+ days
leadsauce insights neglected --threshold 60

# Check overall network health score
leadsauce insights health
```

### Bulk Operations

```bash
# Tag all contacts at a specific company
leadsauce bulk tag --filter "company=Acme Corp" --tags "Enterprise"

# Export all contacts for a backup
leadsauce export profiles --format csv --output backup_$(date +%Y%m%d).csv
```

---

## Troubleshooting

### "Database not found" error

Run `leadsauce init` to create the database and config directory.

### Migration errors after an update

```bash
leadsauce migrate
```

### Reminders not appearing

Check that `reminders.notification_enabled` is `true` in your config:

```bash
leadsauce config set reminders.notification_enabled true
```

### Output looks broken / missing colors

Ensure your terminal supports ANSI colors, or disable color output:

```bash
leadsauce config set output.color false
```

Or set the environment variable:

```bash
export LEADSAUCE_OUTPUT_FORMAT=text
```

### Verbose logging for debugging

```bash
LEADSAUCE_LOG_LEVEL=DEBUG leadsauce <command>
```

### Running Tests

```bash
pytest                          # All tests
pytest -v                       # Verbose
pytest --cov=leadsauce          # With coverage
pytest -k "profile"             # Match test names
```
