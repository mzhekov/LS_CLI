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
git clone https://github.com/yourusername/leadsauce-cli.git
cd leadsauce-cli
pip install -e .
```

## Quick Start

```bash
# Initialize configuration
leadsauce init

# Register/Login
leadsauce auth register --email user@example.com
leadsauce auth login --email user@example.com

# Create your first contact
leadsauce profile create --name "John Doe" --seniority executive

# List contacts
leadsauce profile list

# Add an interaction
leadsauce interaction add <profile_id> --type meeting --subject "Q4 Planning"

# Set a reminder
leadsauce reminder create <profile_id> --title "Follow up" --date "2025-11-15"

# View network insights
leadsauce insights dashboard
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Quick Start](docs/quick_start.md)
- [Command Reference](docs/commands.md)
- [Use Cases](docs/use_cases.md)

## Command Structure

```
leadsauce
├── auth          # Authentication and user management
├── profile       # Contact management
├── company       # Company management
├── interaction   # Interaction logging
├── reminder      # Reminder and task management
├── tag           # Tag management
├── team          # Team collaboration
├── document      # Document management
├── bulk          # Bulk operations
├── insights      # Analytics and insights
├── relationship  # Relationship mapping
├── search        # Global search
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

- Documentation: https://docs.leadsauce.com
- Issues: https://github.com/yourusername/leadsauce-cli/issues
- Email: support@leadsauce.com

## Authors

LeadSauce Development Team

---

**Version**: 1.0.0
**Last Updated**: 2025-11-04
