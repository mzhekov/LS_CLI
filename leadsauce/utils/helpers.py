"""
Helper utilities
"""

import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def generate_token(length: int = 32) -> str:
    """Generate random token"""
    import secrets
    return secrets.token_urlsafe(length)


def calculate_days_ago(dt: datetime) -> int:
    """Calculate number of days ago from a datetime"""
    if dt is None:
        return float('inf')
    delta = datetime.utcnow() - dt
    return delta.days


def parse_relative_date(date_str: str) -> Optional[datetime]:
    """Parse relative date string like '+7d', 'tomorrow', 'today'"""
    from leadsauce.utils.validators import validate_date
    return validate_date(date_str)


def calculate_next_occurrence(date: datetime, pattern: str) -> datetime:
    """Calculate next occurrence based on recurrence pattern"""
    if pattern == 'daily':
        return date + timedelta(days=1)
    elif pattern == 'weekly':
        return date + timedelta(weeks=1)
    elif pattern == 'monthly':
        # Approximate month as 30 days
        return date + timedelta(days=30)
    elif pattern == 'yearly':
        return date + timedelta(days=365)
    else:
        return date


def ensure_directory(path: str):
    """Ensure directory exists"""
    from pathlib import Path
    Path(path).mkdir(parents=True, exist_ok=True)


def get_editor() -> str:
    """Get preferred text editor from environment"""
    return os.getenv('EDITOR', os.getenv('VISUAL', 'nano'))


def open_in_editor(file_path: str) -> bool:
    """Open file in editor"""
    import subprocess

    editor = get_editor()
    try:
        subprocess.run([editor, file_path], check=True)
        return True
    except Exception:
        return False


def pluralize(count: int, singular: str, plural: str = None) -> str:
    """Pluralize word based on count"""
    if plural is None:
        plural = singular + 's'

    return singular if count == 1 else plural


def format_count(count: int, singular: str, plural: str = None) -> str:
    """Format count with pluralized word"""
    word = pluralize(count, singular, plural)
    return f"{count} {word}"


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def dict_diff(old: Dict, new: Dict) -> Dict:
    """Calculate difference between two dictionaries"""
    diff = {}
    all_keys = set(old.keys()) | set(new.keys())

    for key in all_keys:
        old_val = old.get(key)
        new_val = new.get(key)

        if old_val != new_val:
            diff[key] = {'old': old_val, 'new': new_val}

    return diff


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def unflatten_dict(d: Dict, sep: str = '.') -> Dict:
    """Unflatten dictionary with dot notation keys"""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (ZeroDivisionError, TypeError):
        return default


def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage"""
    return safe_divide(part * 100, total, 0.0)


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format value as percentage"""
    return f"{value:.{decimals}f}%"


def get_time_ago(dt: datetime) -> str:
    """Get human-readable time ago string"""
    if dt is None:
        return "Never"

    now = datetime.utcnow()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def remove_none_values(d: Dict) -> Dict:
    """Remove None values from dictionary"""
    return {k: v for k, v in d.items() if v is not None}


def get_nested(d: Dict, *keys, default=None):
    """Safely get nested dictionary value"""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


def set_nested(d: Dict, *keys, value):
    """Set nested dictionary value"""
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


