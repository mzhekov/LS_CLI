"""
Input validation utilities
"""

import re
from typing import Optional
from datetime import datetime
from leadsauce.utils.constants import (
    SENIORITY_LEVELS,
    GENERATION_TYPES,
    INTERACTION_TYPES,
    REMINDER_PRIORITIES,
    REMINDER_CATEGORIES,
    RECURRENCE_PATTERNS,
    TEAM_ROLES,
    DOCUMENT_TYPES,
    VISIBILITY_OPTIONS
)


def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Basic validation - can be enhanced
    pattern = r'^\+?[\d\s\-\(\)]+$'
    return bool(re.match(pattern, phone)) and len(re.sub(r'\D', '', phone)) >= 10


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s<>"]+|www\.[^\s<>"]+'
    return bool(re.match(pattern, url))


def validate_hex_color(color: str) -> bool:
    """Validate hex color code"""
    pattern = r'^#[0-9A-Fa-f]{6}$'
    return bool(re.match(pattern, color))


def validate_seniority(seniority: str) -> bool:
    """Validate seniority level"""
    return seniority.lower() in SENIORITY_LEVELS


def validate_generation(generation: str) -> bool:
    """Validate generation type"""
    return generation.lower() in GENERATION_TYPES


def validate_interaction_type(interaction_type: str) -> bool:
    """Validate interaction type"""
    return interaction_type.lower() in INTERACTION_TYPES


def validate_priority(priority: str) -> bool:
    """Validate priority level"""
    return priority.lower() in REMINDER_PRIORITIES


def validate_category(category: str) -> bool:
    """Validate reminder category"""
    return category.lower() in REMINDER_CATEGORIES


def validate_recurrence(recurrence: str) -> bool:
    """Validate recurrence pattern"""
    return recurrence.lower() in RECURRENCE_PATTERNS


def validate_team_role(role: str) -> bool:
    """Validate team role"""
    return role.lower() in TEAM_ROLES


def validate_document_type(doc_type: str) -> bool:
    """Validate document type"""
    return doc_type.lower() in DOCUMENT_TYPES


def validate_visibility(visibility: str) -> bool:
    """Validate visibility option"""
    return visibility.lower() in VISIBILITY_OPTIONS


def validate_date(date_str: str) -> Optional[datetime]:
    """
    Validate and parse date string

    Supported formats:
    - YYYY-MM-DD
    - YYYY-MM-DD HH:MM
    - YYYY-MM-DD HH:MM:SS
    - Relative: today, tomorrow, +7d, +2w, +1m

    Returns:
        datetime object or None if invalid
    """
    from datetime import timedelta

    if not date_str:
        return None

    date_str = date_str.strip().lower()

    # Handle relative dates
    if date_str == 'today':
        return datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    elif date_str == 'tomorrow':
        return datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    elif date_str.startswith('+'):
        # Parse relative date like +7d, +2w, +1m
        match = re.match(r'\+(\d+)([dwmy])$', date_str)
        if match:
            value = int(match.group(1))
            unit = match.group(2)

            base = datetime.now()
            if unit == 'd':
                return base + timedelta(days=value)
            elif unit == 'w':
                return base + timedelta(weeks=value)
            elif unit == 'm':
                return base + timedelta(days=value * 30)
            elif unit == 'y':
                return base + timedelta(days=value * 365)

    # Parse absolute dates
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d/%Y',
        '%m/%d/%Y %H:%M',
        '%d-%m-%Y',
        '%d-%m-%Y %H:%M'
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def validate_score(score: int, min_val: int = 0, max_val: int = 100) -> bool:
    """Validate score within range"""
    return isinstance(score, int) and min_val <= score <= max_val


def validate_required(value: any, field_name: str) -> str:
    """
    Validate required field

    Raises:
        ValueError if field is empty
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} is required")
    return value


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove dangerous characters"""
    # Remove any non-alphanumeric characters except dash, underscore, and period
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Remove leading/trailing dots and dashes
    filename = filename.strip('.-')
    return filename


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    return True, ""


def parse_tags(tags_str: str) -> list:
    """Parse comma-separated tags string into list"""
    if not tags_str:
        return []

    tags = [tag.strip() for tag in tags_str.split(',')]
    return [tag for tag in tags if tag]  # Remove empty strings


def parse_skills(skills_str: str) -> list:
    """Parse comma-separated skills string into list"""
    return parse_tags(skills_str)


def parse_filter(filter_str: str) -> tuple[str, str]:
    """
    Parse filter string in format 'key=value'

    Returns:
        Tuple of (key, value)

    Raises:
        ValueError if format is invalid
    """
    if '=' not in filter_str:
        raise ValueError(f"Invalid filter format: '{filter_str}'. Expected 'key=value'")

    parts = filter_str.split('=', 1)
    return parts[0].strip(), parts[1].strip()
