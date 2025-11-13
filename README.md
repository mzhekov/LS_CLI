# LeadSauce CLI

Professional Network Management from the Command Line

## Overview

LeadSauce CLI is a powerful command-line interface for managing professional contacts, companies, interactions, and relationships. Designed for power users, automation enthusiasts, and anyone who prefers terminal-based workflows.

## Features

- **Contact Management**: Create, update, search, and organize professional contacts
- **Company Tracking**: Manage companies and organizational relationships
- **Interaction Logging**: Track meetings, calls, emails, and notes
- **Smart Reminders**: Set reminders with recurring options and priority levels
- **Team Collaboration**: Share contacts and collaborate with team members
- **Analytics & Insights**: Network health scores, engagement analysis, and more
- **Bulk Operations**: Import/export data, batch updates, and mass operations
- **Document Management**: Upload and organize documents per contact
- **Relationship Mapping**: Visualize connections between contacts
- **Tag System**: Organize contacts with custom tags

## Installation

```bash
# Install from PyPI (when published)
pip install leadsauce-cli

# Or install from source
git clone https://github.com/mzhekov/LS_CLI.git
cd LS_CLI
pip install -e .
```

## Quick Start

```bash
# Initialize the database (first time only)
leadsauce init

# Launch the interactive TUI (recommended)
leadsauce

# Or use commands directly:

# Create your first contact
leadsauce profile create --name "John Doe" --seniority executive

# List contacts
leadsauce profile list

# View the dashboard
leadsauce dashboard

# Get help on any command
leadsauce --help
leadsauce profile --help
```

## Command Structure

```
leadsauce
├── init          # Initialize database and configuration
├── dashboard     # View overview dashboard
├── profile       # Contact management
├── company       # Company management
├── goal          # Goal management
├── task          # Task management
├── reminder      # Reminder management
├── interaction   # Interaction logging
├── tag           # Tag management
├── team          # Team collaboration
├── relationship  # Relationship mapping
├── export        # Export operations
├── import        # Import operations
└── config        # Configuration management
```

## Configuration

Configuration is stored in `~/.leadsauce/config.yaml`. You can edit it directly or use:

```bash
leadsauce config set output.format table
leadsauce config set output.color true
leadsauce config list
```

## Shell Completion

```bash
# Bash
leadsauce completion bash > /etc/bash_completion.d/leadsauce
source /etc/bash_completion.d/leadsauce

# Zsh
leadsauce completion zsh > ~/.zsh/completion/_leadsauce

# Fish
leadsauce completion fish > ~/.config/fish/completions/leadsauce.fish
```

## Examples

### Daily Workflow
```bash
# Check today's reminders
leadsauce reminder list --today

# Complete a reminder
leadsauce reminder complete 42 --add-note "Called, left voicemail"

# Log an interaction
leadsauce interaction add 15 --type call --subject "Follow-up call"
```

### Bulk Operations
```bash
# Export all contacts
leadsauce export profiles --format csv --output contacts.csv

# Import contacts
leadsauce import profiles --file contacts.csv

# Bulk tag
leadsauce bulk tag --filter "company=Tech Corp" --tags "VIP"
```

### Analytics
```bash
# Network health
leadsauce insights health

# Find neglected contacts
leadsauce insights neglected --threshold 60

# View statistics
leadsauce stats
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check coverage
pytest --cov=leadsauce --cov-report=html

# Format code
black leadsauce tests

# Lint
flake8 leadsauce tests

# Type checking
mypy leadsauce
```

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## License

MIT License - see LICENSE file for details

## Support

- Issues: https://github.com/mzhekov/LS_CLI/issues
- Repository: https://github.com/mzhekov/LS_CLI

## Authors

LeadSauce Development Team

---

**Version**: 1.0.0
**Last Updated**: 2025-11-04
