"""
Constants used throughout the application
"""

import os
from pathlib import Path

# Application info
APP_NAME = "leadsauce"
APP_VERSION = "1.0.0"
APP_AUTHOR = "LeadSauce Development Team"

# Directories
HOME_DIR = Path.home()
APP_DIR = HOME_DIR / f".{APP_NAME}"
CONFIG_FILE = APP_DIR / "config.yaml"
DATABASE_FILE = APP_DIR / "database.db"
SESSION_FILE = APP_DIR / "session"
LOG_DIR = APP_DIR / "logs"
LOG_FILE = LOG_DIR / f"{APP_NAME}.log"
PLUGINS_DIR = APP_DIR / "plugins"
WORKFLOWS_DIR = APP_DIR / "workflows"

# Seniority levels
SENIORITY_LEVELS = [
    "junior",
    "mid",
    "senior",
    "manager",
    "director",
    "executive",
    "c-level"
]

# Generation types
GENERATION_TYPES = [
    "silent",
    "boomer",
    "gen-x",
    "millennial",
    "gen-z",
    "gen-alpha"
]

# Interaction types
INTERACTION_TYPES = [
    "meeting",
    "call",
    "email",
    "note",
    "event"
]

# Reminder priorities
REMINDER_PRIORITIES = [
    "low",
    "medium",
    "high"
]

# Reminder categories
REMINDER_CATEGORIES = [
    "call",
    "email",
    "meeting",
    "follow-up",
    "birthday",
    "general"
]

# Recurrence patterns
RECURRENCE_PATTERNS = [
    "daily",
    "weekly",
    "monthly",
    "yearly"
]

# Team roles
TEAM_ROLES = [
    "owner",
    "admin",
    "editor",
    "viewer",
    "member"
]

# Document types
DOCUMENT_TYPES = [
    "resume",
    "contract",
    "presentation",
    "proposal",
    "report",
    "other"
]

# Visibility options
VISIBILITY_OPTIONS = [
    "private",
    "team",
    "shared"
]

# Output formats
OUTPUT_FORMATS = [
    "table",
    "json",
    "csv",
    "text"
]

# Subscription tiers
SUBSCRIPTION_TIERS = [
    "free",
    "pro",
    "enterprise"
]

# Relationship types
RELATIONSHIP_TYPES = [
    "colleague",
    "manager",
    "reports_to",
    "friend",
    "mentor",
    "mentee",
    "client",
    "vendor",
    "partner"
]

# Default configuration
DEFAULT_CONFIG = {
    "api": {
        "endpoint": "https://api.leadsauce.com",
        "timeout": 30,
        "verify_ssl": True
    },
    "database": {
        "type": "sqlite",
        "path": str(DATABASE_FILE)
    },
    "output": {
        "format": "table",
        "color": True,
        "pager": "auto",
        "pagination": {
            "enabled": True,
            "limit": 50
        }
    },
    "email": {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "sender": f"noreply@{APP_NAME}.com"
    },
    "reminders": {
        "notification_enabled": True,
        "notification_lead_time": 15,
        "check_interval": 15,
        "email_summary": False,
        "summary_time": "09:00"
    },
    "openai": {
        "enabled": False,
        "model": "gpt-4",
        "max_tokens": 500
    },
    "subscription": {
        "tier": "free",
        "features": {
            "ai_insights": False,
            "bulk_operations": True,
            "team_features": True
        }
    },
    "preferences": {
        "default_seniority": "mid",
        "default_priority": "medium",
        "confirm_delete": True,
        "auto_sync": False,
        "sync_interval": 3600
    },
    "logging": {
        "level": "INFO",
        "file": str(LOG_FILE),
        "max_size": 10485760,
        "backup_count": 5
    }
}

# API endpoints (if using remote backend)
API_ENDPOINTS = {
    "auth": {
        "register": "/auth/register",
        "login": "/auth/login",
        "logout": "/auth/logout",
        "refresh": "/auth/refresh",
        "reset_password": "/auth/reset-password"
    },
    "profiles": "/profiles",
    "companies": "/companies",
    "interactions": "/interactions",
    "reminders": "/reminders",
    "tags": "/tags",
    "teams": "/teams",
    "documents": "/documents",
    "insights": "/insights"
}

# HTTP status codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500

# Colored output
COLOR_SUCCESS = "green"
COLOR_ERROR = "red"
COLOR_WARNING = "yellow"
COLOR_INFO = "cyan"
COLOR_PRIMARY = "blue"

# Date formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M"
