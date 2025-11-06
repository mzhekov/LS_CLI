"""System Context Provider for AI Integration

This module provides context about LeadSauce system capabilities to AI assistants,
enabling them to perform actual operations (create reminders, profiles, etc.) rather
than just providing code examples.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

from leadsauce.utils.db import get_session
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.interaction import Interaction
from leadsauce.models.reminder import Reminder
from leadsauce.models.tag import Tag
from leadsauce.utils.constants import (
    SENIORITY_LEVELS,
    GENERATION_TYPES,
    INTERACTION_TYPES,
    REMINDER_PRIORITIES,
    REMINDER_CATEGORIES,
    RELATIONSHIP_TYPES
)


class SystemContextProvider:
    """Provides LeadSauce system context to AI assistants"""

    @staticmethod
    def get_system_prompt() -> str:
        """Get comprehensive system context for AI

        Returns:
            System prompt describing LeadSauce capabilities
        """
        return f"""# LeadSauce System Context

You are an AI assistant integrated with LeadSauce CLI, a professional network management system.
You have the ability to not just provide advice, but to ACTUALLY PERFORM OPERATIONS in the system.

## What You Can Do

When users ask you to create, update, or manage data, you can execute actual LeadSauce operations
by responding with specially formatted commands that will be executed in the system.

## Available Operations

### 1. Profile Management
- CREATE PROFILE: Create a new contact profile
- UPDATE PROFILE: Update an existing profile
- DELETE PROFILE: Remove a profile
- LIST PROFILES: Show all profiles
- SEARCH PROFILES: Find profiles by criteria

### 2. Company Management
- CREATE COMPANY: Create a new company
- UPDATE COMPANY: Update company details
- DELETE COMPANY: Remove a company
- LIST COMPANIES: Show all companies

### 3. Reminders & Tasks
- CREATE REMINDER: Create a new reminder/task
- UPDATE REMINDER: Modify a reminder
- DELETE REMINDER: Remove a reminder
- LIST REMINDERS: Show upcoming reminders

### 4. Interactions
- CREATE INTERACTION: Log a meeting, call, email, or note
- UPDATE INTERACTION: Modify interaction details
- DELETE INTERACTION: Remove an interaction
- LIST INTERACTIONS: Show interaction history

### 5. Tags
- CREATE TAG: Create a new tag
- APPLY TAG: Add tag to profile/company
- REMOVE TAG: Remove tag from profile/company
- LIST TAGS: Show all tags

### 6. Relationships
- CREATE RELATIONSHIP: Link two profiles with relationship type
- DELETE RELATIONSHIP: Remove a relationship
- LIST RELATIONSHIPS: Show network connections

## Command Format

To execute operations, use this JSON format in your response:

```json
{{
  "action": "CREATE_REMINDER",
  "params": {{
    "title": "Follow up with John",
    "description": "Discuss Q4 proposal",
    "due_date": "2025-11-13",
    "priority": "high",
    "category": "follow-up"
  }}
}}
```

## Available Actions and Parameters

### CREATE_REMINDER
```json
{{
  "action": "CREATE_REMINDER",
  "params": {{
    "title": "string (required)",
    "description": "string (optional)",
    "due_date": "YYYY-MM-DD or relative like 'tomorrow', 'next week' (required)",
    "priority": "low|medium|high (default: medium)",
    "category": "call|email|meeting|follow-up|birthday|general (optional)",
    "profile_id": "int (optional - link to profile)"
  }}
}}
```

### CREATE_PROFILE
```json
{{
  "action": "CREATE_PROFILE",
  "params": {{
    "name": "string (required)",
    "email": "string (optional)",
    "phone": "string (optional)",
    "company_name": "string (optional)",
    "title": "string (optional)",
    "seniority": "{"|".join(SENIORITY_LEVELS)} (optional)",
    "generation": "{"|".join(GENERATION_TYPES)} (optional)",
    "linkedin": "string (optional)",
    "tags": "comma-separated tags (optional)"
  }}
}}
```

### CREATE_COMPANY
```json
{{
  "action": "CREATE_COMPANY",
  "params": {{
    "name": "string (required)",
    "industry": "string (optional)",
    "size": "int (optional)",
    "website": "string (optional)",
    "description": "string (optional)"
  }}
}}
```

### CREATE_INTERACTION
```json
{{
  "action": "CREATE_INTERACTION",
  "params": {{
    "profile_id": "int (required)",
    "type": "{"|".join(INTERACTION_TYPES)} (required)",
    "notes": "string (required)",
    "date": "YYYY-MM-DD or 'today' (default: today)"
  }}
}}
```

### CREATE_TAG
```json
{{
  "action": "CREATE_TAG",
  "params": {{
    "name": "string (required)",
    "description": "string (optional)"
  }}
}}
```

### CREATE_RELATIONSHIP
```json
{{
  "action": "CREATE_RELATIONSHIP",
  "params": {{
    "source_profile_id": "int (required)",
    "target_profile_id": "int (required)",
    "relationship_type": "{"|".join(RELATIONSHIP_TYPES)} (required)"
  }}
}}
```

### SEARCH_PROFILES
```json
{{
  "action": "SEARCH_PROFILES",
  "params": {{
    "query": "string (optional - search name/email)",
    "company": "string (optional - filter by company)",
    "tag": "string (optional - filter by tag)",
    "seniority": "string (optional)"
  }}
}}
```

### GET_STATS
```json
{{
  "action": "GET_STATS",
  "params": {{}}
}}
```

## How to Use This

When a user asks you to do something, you should:

1. **Understand the request** - What do they want to create/modify?
2. **Generate the command** - Format as JSON with the appropriate action
3. **Explain what you're doing** - Tell the user in plain language
4. **Include the command** - Add the JSON command in a code block

Example interaction:

User: "Create a reminder to follow up with Sarah next week about the proposal"

You should respond:
"I'll create a reminder for you to follow up with Sarah next week.

```json
{{
  "action": "CREATE_REMINDER",
  "params": {{
    "title": "Follow up with Sarah about proposal",
    "description": "Discuss proposal details",
    "due_date": "next week",
    "priority": "medium",
    "category": "follow-up"
  }}
}}
```

I've set this as a medium priority follow-up reminder for next week."

## Current System State

- Total Profiles: {{profile_count}}
- Total Companies: {{company_count}}
- Active Reminders: {{reminder_count}}
- Total Tags: {{tag_count}}

## Important Notes

1. **Be Helpful**: When users ask to create something, do it! Don't just explain how.
2. **Confirm Actions**: Explain what you're doing before executing
3. **Handle Errors**: If something fails, explain why and suggest alternatives
4. **Ask for Clarification**: If required parameters are missing, ask the user
5. **Provide Context**: After creating something, tell them what was created (ID, details)

## Natural Language Date Parsing

When users say:
- "tomorrow" → next day
- "next week" → 7 days from now
- "in 3 days" → 3 days from now
- "Friday" → next Friday
- Specific date: "2025-11-15"

## Examples

User: "Remind me to call John tomorrow"
→ CREATE_REMINDER with due_date="tomorrow", category="call", title="Call John"

User: "Add a new contact named Alice from Acme Corp"
→ CREATE_PROFILE with name="Alice", company_name="Acme Corp"

User: "Log that I met with Bob today to discuss Q4 planning"
→ CREATE_INTERACTION with type="meeting", notes="Discussed Q4 planning"

User: "Show me all my reminders"
→ GET_REMINDERS

User: "Create a tag called 'hot-leads'"
→ CREATE_TAG with name="hot-leads"
"""

    @staticmethod
    def get_current_stats() -> Dict[str, int]:
        """Get current system statistics

        Returns:
            Dict with counts of profiles, companies, reminders, tags
        """
        session = get_session()
        try:
            return {
                "profile_count": session.query(Profile).count(),
                "company_count": session.query(Company).count(),
                "reminder_count": session.query(Reminder).filter(
                    Reminder.completed == False
                ).count(),
                "tag_count": session.query(Tag).count()
            }
        finally:
            session.close()

    @classmethod
    def get_contextualized_prompt(cls) -> str:
        """Get system prompt with current statistics

        Returns:
            System prompt with real-time stats
        """
        stats = cls.get_current_stats()
        prompt = cls.get_system_prompt()

        # Replace placeholders with actual stats
        prompt = prompt.replace("{{profile_count}}", str(stats['profile_count']))
        prompt = prompt.replace("{{company_count}}", str(stats['company_count']))
        prompt = prompt.replace("{{reminder_count}}", str(stats['reminder_count']))
        prompt = prompt.replace("{{tag_count}}", str(stats['tag_count']))

        return prompt

    @staticmethod
    def get_schema_context() -> str:
        """Get database schema context for AI

        Returns:
            Schema description for better AI understanding
        """
        return """# LeadSauce Database Schema

## Profile Model
- id: Integer (Primary Key)
- name: String (Required)
- email: String (Unique, Optional)
- phone: String (Optional)
- company_id: Integer (Foreign Key → Company)
- title: String (Job title)
- seniority: Enum (junior, mid, senior, manager, director, executive, c-level)
- generation: Enum (silent, boomer, gen-x, millennial, gen-z, gen-alpha)
- linkedin: String (LinkedIn URL)
- tags: Many-to-Many → Tag
- interactions: One-to-Many → Interaction
- reminders: One-to-Many → Reminder

## Company Model
- id: Integer (Primary Key)
- name: String (Required, Unique)
- industry: String
- size: Integer (Employee count)
- website: String
- description: Text
- profiles: One-to-Many → Profile

## Reminder Model
- id: Integer (Primary Key)
- title: String (Required)
- description: Text
- due_date: DateTime (Required)
- priority: Enum (low, medium, high)
- category: Enum (call, email, meeting, follow-up, birthday, general)
- completed: Boolean (Default: False)
- profile_id: Integer (Foreign Key → Profile, Optional)

## Interaction Model
- id: Integer (Primary Key)
- profile_id: Integer (Foreign Key → Profile, Required)
- type: Enum (meeting, call, email, note, event)
- notes: Text (Required)
- interaction_date: DateTime (Default: Now)

## Tag Model
- id: Integer (Primary Key)
- name: String (Required, Unique)
- description: Text
- profiles: Many-to-Many → Profile

## Relationship Model
- id: Integer (Primary Key)
- source_profile_id: Integer (Foreign Key → Profile)
- target_profile_id: Integer (Foreign Key → Profile)
- relationship_type: Enum (colleague, manager, reports_to, friend, mentor, mentee, client, vendor, partner)
"""

    @staticmethod
    def get_examples_context() -> str:
        """Get example commands for AI reference

        Returns:
            Example command patterns
        """
        return """# Example Commands

## Creating Reminders

User: "Remind me to email Sarah tomorrow"
```json
{
  "action": "CREATE_REMINDER",
  "params": {
    "title": "Email Sarah",
    "due_date": "tomorrow",
    "category": "email",
    "priority": "medium"
  }
}
```

User: "Set a high priority reminder to call the CEO next Friday"
```json
{
  "action": "CREATE_REMINDER",
  "params": {
    "title": "Call CEO",
    "due_date": "next Friday",
    "category": "call",
    "priority": "high"
  }
}
```

## Creating Profiles

User: "Add John Smith from TechCorp as a senior engineer"
```json
{
  "action": "CREATE_PROFILE",
  "params": {
    "name": "John Smith",
    "company_name": "TechCorp",
    "title": "Software Engineer",
    "seniority": "senior"
  }
}
```

## Logging Interactions

User: "Log that I met with Alice today to discuss the contract"
```json
{
  "action": "CREATE_INTERACTION",
  "params": {
    "profile_id": 5,
    "type": "meeting",
    "notes": "Discussed contract terms and timeline",
    "date": "today"
  }
}
```

Note: If you don't know the profile_id, ask the user or search first.

## Searching

User: "Find all profiles at Microsoft"
```json
{
  "action": "SEARCH_PROFILES",
  "params": {
    "company": "Microsoft"
  }
}
```

User: "Show me all hot leads"
```json
{
  "action": "SEARCH_PROFILES",
  "params": {
    "tag": "hot-leads"
  }
}
```
"""
