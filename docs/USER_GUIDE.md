# LeadSauce CLI — User Guide

A professional command-line tool for managing contacts, companies, interactions, relationships, and network analytics — entirely from your terminal.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Dashboard](#2-dashboard)
3. [Profile Management](#3-profile-management)
4. [Company Management](#4-company-management)
5. [Goal Tracking](#5-goal-tracking)
6. [Task Management](#6-task-management)
7. [Interaction Logging](#7-interaction-logging)
8. [Reminder System](#8-reminder-system)
9. [Tag Organization](#9-tag-organization)
10. [Relationship Mapping](#10-relationship-mapping)
11. [Search](#11-search)
12. [Import & Export](#12-import--export)
13. [AI Assistant (Claude Integration)](#13-ai-assistant-claude-integration)
14. [Interactive TUI Mode](#14-interactive-tui-mode)
15. [Configuration](#15-configuration)
16. [Use Case Scenarios](#16-use-case-scenarios)

---

## 1. Getting Started

### Installation

```bash
# From source
git clone https://github.com/mzhekov/ls_cli.git
cd ls_cli
pip install -e .
```

### First-Time Setup

```bash
leadsauce init
```

This creates:
- `~/.leadsauce/config.yaml` — your configuration file
- `~/.leadsauce/database.db` — your local SQLite database
- `~/.leadsauce/logs/` — log directory

### Launching LeadSauce

```bash
leadsauce          # Opens the interactive TUI dashboard (default)
leadsauce tui      # Explicitly launch TUI mode
leadsauce version  # Show version info
```

---

## 2. Dashboard

The dashboard gives you a real-time overview of your network and workload.

```bash
leadsauce dashboard         # Full dashboard
leadsauce dashboard --mini  # Compact one-line summary
```

### What It Shows

- Total profiles, companies, tasks, and goals
- Recent profiles added
- Pending tasks with due dates
- Upcoming reminders
- Quick action shortcuts

### Use Cases

**Morning check-in:**
```bash
leadsauce dashboard
```
See everything at a glance — who you need to follow up with, what tasks are due, and how your network has grown.

**Terminal status bar integration:**
```bash
leadsauce dashboard --mini
```
Embed a compact summary in scripts or shell prompts.

---

## 3. Profile Management

Profiles are your contacts — people you know, work with, or want to track.

### Commands

```bash
leadsauce profile create
leadsauce profile list
leadsauce profile show <id>
leadsauce profile update <id>
leadsauce profile delete <id>
leadsauce profile search
```

### Creating a Profile

```bash
leadsauce profile create \
  --name "Jane Smith" \
  --email "jane@example.com" \
  --phone "+1-555-0100" \
  --seniority senior \
  --company-id 3 \
  --generation millennial \
  --tags "engineering,leadership" \
  --notes "Met at PyCon 2024. Interested in distributed systems."
```

**Seniority levels:** `junior`, `mid`, `senior`, `manager`, `director`, `executive`, `c-level`

**Generations:** `silent`, `boomer`, `gen-x`, `millennial`, `gen-z`, `gen-alpha`

### Listing & Filtering Profiles

```bash
leadsauce profile list                            # All profiles
leadsauce profile list --limit 20 --offset 0     # Paginate
leadsauce profile list --tag engineering          # Filter by tag
leadsauce profile list --company "Acme Corp"     # Filter by company
leadsauce profile list --seniority senior         # Filter by seniority
leadsauce profile list --sort name               # Sort by name
leadsauce profile list --format json             # Output as JSON
leadsauce profile list --format csv              # Output as CSV
```

### Searching Profiles

```bash
leadsauce profile search --query "Jane"
leadsauce profile search --email "jane@example.com"
leadsauce profile search --phone "+1-555"
```

### Profile Fields Reference

| Field | Description |
|-------|-------------|
| `name` | Full name |
| `email` | Email address |
| `phone` | Phone number |
| `seniority` | Career level |
| `generation` | Generational cohort |
| `company` | Associated company |
| `marital_status` | Marital status |
| `has_children` | Whether they have children |
| `good_at` | Skills and strengths |
| `need_to_work` | Areas for improvement |
| `work_for` | Motivations and drivers |
| `tags` | Custom organizational labels |
| `notes` | Free-text notes |

### Use Cases

**Sales prospecting:**
```bash
# Add a new lead from a conference
leadsauce profile create --name "Alex Rivera" --email "alex@startup.io" \
  --seniority director --tags "lead,fintech" --notes "Decision maker for Q2 budget"

# List all director-level leads
leadsauce profile list --seniority director --tag lead
```

**Recruiting pipeline:**
```bash
# Track candidates
leadsauce profile create --name "Sam Lee" --seniority senior \
  --good-at "Python,Kubernetes" --tags "candidate,backend"

# Review all candidates
leadsauce profile list --tag candidate --sort seniority
```

**Personal networking:**
```bash
# Track mentors and their expertise
leadsauce profile create --name "Dr. Chen" --seniority c-level \
  --tags "mentor,ai-research" --notes "Weekly 1:1 on Fridays"
```

---

## 4. Company Management

Organize your contacts by the companies they work at.

### Commands

```bash
leadsauce company create
leadsauce company list
leadsauce company show <id>
leadsauce company update <id>
leadsauce company delete <id>
```

### Creating a Company

```bash
leadsauce company create \
  --name "Acme Corp" \
  --industry "Technology" \
  --size "500-1000" \
  --location "San Francisco, CA" \
  --website "https://acme.com" \
  --notes "Key enterprise client. Fiscal year ends in March."
```

### Listing & Filtering Companies

```bash
leadsauce company list                        # All companies
leadsauce company list --industry Technology  # Filter by industry
```

### Viewing a Company

```bash
leadsauce company show 3
```

Shows company details plus all associated profiles.

### Use Cases

**Account management:**
```bash
# Set up a key account
leadsauce company create --name "BigBank Ltd" --industry "Finance" \
  --size "10000+" --notes "Renewal in Q4. Main contact: Jane Smith (ID 5)"

# View all contacts at that company
leadsauce company show <id>
```

**Market research:**
```bash
# Track all companies in a target industry
leadsauce company list --industry "Healthcare"
```

**Competitive intelligence:**
```bash
leadsauce company create --name "CompetitorX" --industry "SaaS" \
  --notes "Launched new pricing tier in Jan 2025. Watch for hiring signals."
```

---

## 5. Goal Tracking

Goals are high-level objectives. They can link to profiles, companies, tasks, and tags to track complex multi-step work.

### Commands

```bash
leadsauce goal create
leadsauce goal list
leadsauce goal show <id>
leadsauce goal update <id>
leadsauce goal delete <id>
leadsauce goal link-task <goal-id> <task-id>
leadsauce goal update-progress <id> --progress <0-100>
```

### Creating a Goal

```bash
leadsauce goal create \
  --title "Close enterprise deal with Acme Corp" \
  --description "Reach signed contract by end of Q2" \
  --priority high \
  --target-date "2025-06-30" \
  --tags "sales,enterprise"
```

**Priority levels:** `low`, `medium`, `high`, `urgent`

**Status options:** `active`, `completed`, `on_hold`, `cancelled`

### Tracking Progress

```bash
# Manually set progress
leadsauce goal update-progress 4 --progress 65

# Link a task to a goal (progress auto-aggregates from linked tasks)
leadsauce goal link-task 4 12

# View goal with all linked entities
leadsauce goal show 4
```

### Use Cases

**Sales deal management:**
```bash
leadsauce goal create --title "Land Acme Corp deal" --priority urgent \
  --target-date "2025-06-30"

# Link follow-up tasks
leadsauce goal link-task 1 5   # Product demo task
leadsauce goal link-task 1 6   # Legal review task
leadsauce goal link-task 1 7   # Pricing negotiation task
```

**Career development:**
```bash
leadsauce goal create --title "Expand ML network to 50 senior contacts" \
  --priority medium --target-date "2025-12-31" --tags "networking,ml"
```

**Recruiting:**
```bash
leadsauce goal create --title "Hire 3 backend engineers by Q3" \
  --priority high --target-date "2025-09-30"
leadsauce goal update-progress 2 --progress 33   # 1 out of 3 hired
```

---

## 6. Task Management

Tasks are actionable to-do items linked to contacts, companies, or goals.

### Task Fields

| Field | Options |
|-------|---------|
| `status` | `pending`, `in_progress`, `completed`, `cancelled` |
| `priority` | `low`, `medium`, `high`, `urgent` |
| `due_date` | Date string (YYYY-MM-DD) |
| `linked_profile` | Profile ID |
| `linked_company` | Company ID |
| `tags` | Comma-separated tags |

### Use Cases

**Follow-up reminders after meetings:**
```bash
# Created via TUI or goal link-task
# Track: "Send proposal to Jane Smith by Friday"
```

**Onboarding checklist:**
```bash
# Link multiple tasks to a single onboarding goal
leadsauce goal link-task <goal-id> <task-id>
```

**Batch task review:**
```bash
# View in TUI: Tasks screen shows all pending items sorted by due date
leadsauce tui
# Navigate to Tasks section
```

---

## 7. Interaction Logging

Record every meaningful touchpoint with your contacts — calls, emails, meetings, and notes.

### Interaction Types

- `meeting` — In-person or virtual meetings
- `call` — Phone or video calls
- `email` — Email exchanges
- `note` — General observations or reminders
- `event` — Events attended together

### Fields

| Field | Description |
|-------|-------------|
| `subject` | Brief title of the interaction |
| `notes` | Detailed notes |
| `interaction_date` | When it happened |
| `visibility` | `private`, `team`, `shared` |
| `linked_profile` | Which contact |

### Use Cases

**Sales call notes:**
After a sales call, log the outcome:
```
Subject: "Discovery call - Q2 needs"
Notes: "They need 500 seats. Budget approved. Wants demo next week."
Type: call
```

**Meeting recap:**
```
Subject: "Kickoff meeting with Acme"
Notes: "Agreed on 3-month roadmap. Key contact is Jane. Next review: April 15."
Type: meeting
```

**Track email threads:**
```
Subject: "Sent pricing proposal"
Notes: "Attached v2 pricing deck. Waiting for legal review."
Type: email
```

---

## 8. Reminder System

Reminders ensure you never miss a follow-up, birthday, or deadline.

### Reminder Fields

| Field | Options |
|-------|---------|
| `category` | `call`, `email`, `meeting`, `follow-up`, `birthday`, `general` |
| `priority` | `low`, `medium`, `high` |
| `recurrence` | `daily`, `weekly`, `monthly`, `yearly` |
| `linked_to` | Profile, company, task, or goal |

### Use Cases

**Weekly follow-up with a lead:**
```
Title: "Check in with Alex Rivera"
Category: follow-up
Recurrence: weekly
Linked profile: Alex Rivera (ID 12)
```

**Birthday reminder:**
```
Title: "Jane's birthday"
Category: birthday
Recurrence: yearly
Reminder date: 1985-03-14
```

**Contract renewal alert:**
```
Title: "Acme Corp renewal — 60-day notice"
Category: general
Priority: high
Reminder date: 2025-10-01
Linked company: Acme Corp
```

**Post-conference follow-up:**
```
Title: "Follow up with PyCon contacts"
Category: email
Priority: medium
Reminder date: 3 days after conference
```

---

## 9. Tag Organization

Tags are free-form labels you can apply to profiles, tasks, and goals for flexible organization.

### Usage

```bash
# Apply tags when creating
leadsauce profile create --name "Jordan Kim" --tags "vip,partner,nyc"

# Filter by tag
leadsauce profile list --tag vip
leadsauce profile list --tag nyc
```

### Common Tag Patterns

| Tag Group | Example Tags |
|-----------|-------------|
| Pipeline stage | `lead`, `prospect`, `qualified`, `closed-won`, `churned` |
| Role/function | `engineering`, `sales`, `hr`, `finance` |
| Geography | `nyc`, `sf`, `remote`, `emea` |
| Relationship type | `mentor`, `investor`, `partner`, `candidate` |
| Interest | `ai`, `fintech`, `saas`, `open-source` |
| Priority | `vip`, `warm`, `cold` |

### Use Cases

**Multi-dimensional filtering:**
```bash
# Senior engineers in NYC who are warm leads
leadsauce profile list --tag senior --tag nyc --tag warm
```

**Campaign targeting:**
```bash
# Export all fintech contacts for an email campaign
leadsauce profile list --tag fintech --format csv > fintech_contacts.csv
```

---

## 10. Relationship Mapping

Visualize and track how your contacts are connected to each other and to companies.

### Relationship Types

- `colleague` — Work together at the same company
- `manager` / `reports_to` — Reporting hierarchy
- `friend` — Personal connection
- `mentor` / `mentee` — Mentorship relationship
- `client` / `vendor` / `partner` — Business relationships

### Network Visualization

The TUI provides a circular network map showing:
- All connected profiles as nodes
- Relationship type as edge labels
- Company groupings
- Connection strength

**Access via TUI:**
```bash
leadsauce tui
# Navigate to: Network & Relationships
```

### Use Cases

**Mapping an organization before a sales call:**
Understand reporting chains at a target account — who influences the decision, who signs off, who uses the product.

**Finding warm introductions:**
See if any of your contacts knows someone at a company you're targeting.

**Mentorship network:**
Track who introduced you to whom and navigate multi-hop connections.

---

## 11. Search

Global full-text search across all your data.

```bash
leadsauce search --query "kubernetes"
leadsauce search --query "Jane" --type profile
leadsauce search --query "Acme" --type company
leadsauce search --query "proposal" --type interaction
leadsauce search --query "Q2" --type task
```

**Search types:** `profile`, `company`, `interaction`, `task` (or omit for all)

### Use Cases

**Before a call:**
```bash
leadsauce search --query "Acme Corp"
```
Pulls up all contacts, past interactions, tasks, and notes related to Acme Corp in one view.

**Finding a contact you half-remember:**
```bash
leadsauce search --query "distributed systems"
```
Searches across notes, tags, and skills fields to surface the right person.

---

## 12. Import & Export

Move data in and out of LeadSauce using CSV or JSON.

### Export

```bash
leadsauce export profiles                     # Export contacts to CSV
leadsauce export companies                    # Export companies to CSV
leadsauce export tasks                        # Export tasks
leadsauce export all                          # Export everything

leadsauce export profiles --format json       # Export as JSON
leadsauce export profiles --format table      # Display as table
```

### Import

```bash
leadsauce import profiles contacts.csv        # Import contacts
leadsauce import companies companies.csv      # Import companies
```

**Import features:**
- Duplicate detection — skips existing records by email
- Company auto-linking — matches by company name
- Tag creation — creates missing tags automatically
- Validation — reports errors row by row

### CSV Format for Profiles

```csv
name,email,phone,seniority,company,tags,notes
Jane Smith,jane@acme.com,+1-555-0100,senior,Acme Corp,"vip,engineering","Met at PyCon 2024"
Alex Rivera,alex@startup.io,,director,,"lead,fintech","Q2 decision maker"
```

### Use Cases

**Migrate from LinkedIn exports:**
Export LinkedIn contacts to CSV, clean up columns to match the format above, then:
```bash
leadsauce import profiles linkedin_export_cleaned.csv
```

**Backup your data:**
```bash
leadsauce export all
# Creates timestamped CSV files for each entity type
```

**Bulk onboarding from a CRM:**
Export contacts from Salesforce/HubSpot, map fields to LeadSauce format, import in bulk.

**Share a contact list:**
```bash
leadsauce export profiles --tag fintech --format csv > fintech_for_team.csv
```

---

## 13. AI Assistant (Claude Integration)

LeadSauce integrates with Claude CLI to delegate tasks and get AI assistance directly from the terminal.

### Prerequisites

- Claude CLI installed and authenticated (`claude` command available)

### Features

- Background Claude Code session management
- Quick command palette (`Ctrl+K` in TUI)
- Delegate tasks to Claude and view results
- Track AI task status

### Keyboard Shortcuts (in TUI)

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Open quick Claude command palette |
| `Ctrl+R` | View Claude task results |

### Use Cases

**Drafting an outreach email:**
Press `Ctrl+K` in TUI and type:
```
Draft a personalized follow-up email to Jane Smith at Acme Corp after our discovery call about Q2 needs.
```

**Summarizing meeting notes:**
```
Summarize these raw notes into a 3-bullet executive summary: [paste notes]
```

**Research assistance:**
```
What are the top 5 pain points for enterprise SaaS procurement teams in 2025?
```

**Data analysis:**
```
Analyze my contact list patterns: which industries are underrepresented?
```

---

## 14. Interactive TUI Mode

The TUI (Text User Interface) provides a full-screen, keyboard-driven interface for all LeadSauce features.

```bash
leadsauce       # Launch TUI (default)
leadsauce tui   # Explicit launch
```

### Main Screens

| Screen | Key | Description |
|--------|-----|-------------|
| Dashboard | `1` | Overview stats and recent activity |
| Profiles | `2` | Browse, search, and manage contacts |
| Companies | `3` | Manage organizations |
| Network & Relationships | `4` | Visualize connection maps |
| Search | `5` | Global search |
| Tags | `6` | Manage and browse tags |
| Workshop | `7` | Bulk operations |
| Import/Export | `8` | Load/save data |
| AI CLI Control | `9` | Claude AI assistant |
| Browser | `0` | Web session integration |

### Navigation

| Key | Action |
|-----|--------|
| `1`–`9`, `0` | Jump directly to a screen |
| Arrow keys | Navigate menu items |
| `Enter` | Select / confirm |
| Double backspace | Go back / exit screen |
| `Ctrl+K` | Quick Claude command |
| `Ctrl+R` | View Claude results |
| `q` | Quit |

### Use Cases

**Power user workflow:**
Launch TUI at the start of your day. Check the Dashboard (`1`), review pending tasks, browse new profiles (`2`), then jump to Network map (`4`) before a call to recall how contacts are connected.

**Live data entry:**
After a networking event, switch to Profiles (`2`) and quickly add all new contacts you met, tagging them appropriately, without leaving the terminal.

---

## 15. Configuration

LeadSauce is highly configurable via `~/.leadsauce/config.yaml` or CLI commands.

### CLI Configuration

```bash
leadsauce config list                          # Show all settings
leadsauce config get output.format            # Get a specific setting
leadsauce config set output.format json       # Set a value
leadsauce config set output.color true        # Enable color output
```

### Key Configuration Options

```yaml
database:
  path: ~/.leadsauce/database.db

output:
  format: table        # table | json | csv | text
  color: true
  pagination: true

reminders:
  notification_enabled: true
  check_interval: 300  # seconds

ai:
  enabled: true
  default_tool: claude
  tools:
    claude:
      enabled: true

preferences:
  confirm_delete: true
  default_priority: medium
```

### Database Migration

If upgrading from an older version:
```bash
leadsauce migrate --backup
```

Creates a backup before migrating the schema.

---

## 16. Use Case Scenarios

### Scenario A: Sales Professional — Managing a Pipeline

**Goal:** Track 50+ prospects across 20 companies with follow-ups and deal goals.

```bash
# 1. Add target companies
leadsauce company create --name "TechCorp" --industry "SaaS" --size "200-500"

# 2. Add key contacts
leadsauce profile create --name "Chris Doe" --seniority director \
  --company-id 1 --tags "lead,qualified" --notes "Budget owner for Q3"

# 3. Create a deal goal
leadsauce goal create --title "Close TechCorp deal" --priority high \
  --target-date "2025-09-30"

# 4. Log interactions
# (via TUI Interactions screen after each call/email)

# 5. Set follow-up reminders
# (via TUI Reminders — set weekly recurrence)

# 6. Daily workflow
leadsauce dashboard          # Start the day with an overview
leadsauce tui                # Work through tasks and contacts
```

---

### Scenario B: Recruiter — Candidate Pipeline

**Goal:** Track 100 candidates across 5 open roles.

```bash
# Tag candidates by role and stage
leadsauce profile create --name "Sam Park" --seniority senior \
  --good-at "Go,Kubernetes,System Design" \
  --tags "candidate,backend-eng,phone-screen"

# List candidates at phone-screen stage
leadsauce profile list --tag phone-screen --sort name

# Update stage after interview
leadsauce profile update 15 --tags "candidate,backend-eng,final-round"

# Export shortlist for hiring manager
leadsauce profile list --tag final-round --format csv > shortlist.csv
```

---

### Scenario C: Networker — Building a Professional Network

**Goal:** Systematically expand and nurture a professional network.

```bash
# After a conference, batch-add new contacts
leadsauce tui
# Navigate to Profiles → Create (repeat for each contact)

# Tag by event
# --tags "pycon2025,ai-track"

# Set follow-up reminders for warm contacts
# Reminder: "Coffee chat follow-up" — 1 week out

# Weekly review
leadsauce dashboard --mini    # Quick stats
leadsauce profile list --tag pycon2025  # Review conference contacts

# Track relationship depth
# Navigate to Network & Relationships in TUI to see map
```

---

### Scenario D: Freelancer — Client Relationship Management

**Goal:** Track clients, projects, and check-ins.

```bash
# Add clients as profiles + companies
leadsauce company create --name "ClientX" --industry "Media"
leadsauce profile create --name "Dana Reyes" --company-id 2 \
  --tags "client,active" --notes "Retainer project. Invoice on 1st of month."

# Set monthly billing reminder
# Reminder: "Invoice ClientX" — recurrence: monthly

# Log project check-ins
# Interaction: "Monthly check-in call" — type: call

# Track project goal
leadsauce goal create --title "Deliver ClientX rebrand" \
  --priority high --target-date "2025-07-01"

# Export client list
leadsauce profile list --tag client --format csv
```

---

### Scenario E: Power User — Automation & Scripting

**Goal:** Integrate LeadSauce into shell scripts and workflows.

```bash
# Export data for external tools
leadsauce profile list --format json | jq '.[] | select(.seniority == "director")'

# Pipe into notification systems
leadsauce dashboard --mini >> ~/.daily_briefing.txt

# Bulk import after scraping
python clean_scrape.py > contacts.csv
leadsauce import profiles contacts.csv

# Use in cron for daily reminders
# crontab: 0 9 * * * leadsauce dashboard --mini | mail -s "Daily briefing" me@email.com
```

---

## Quick Reference

```
leadsauce                          Launch TUI (default)
leadsauce dashboard                View dashboard
leadsauce profile create           Add a new contact
leadsauce profile list             Browse contacts
leadsauce profile search           Search contacts
leadsauce company create           Add a company
leadsauce company list             Browse companies
leadsauce goal create              Create a goal
leadsauce goal list                View goals
leadsauce export profiles          Export contacts to CSV
leadsauce import profiles <file>   Import contacts from CSV
leadsauce search --query <text>    Global search
leadsauce config list              View configuration
leadsauce init                     First-time setup
leadsauce migrate --backup         Upgrade database schema
```

---

*LeadSauce CLI v1.0.0 — MIT License*
