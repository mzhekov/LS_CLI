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


def get_available_browsers() -> Dict[str, Optional[str]]:
    """Detect installed terminal browsers

    Returns:
        Dictionary mapping browser names to their paths (or None if not found)
    """
    import shutil

    browsers = {
        'w3m': shutil.which('w3m'),
        'lynx': shutil.which('lynx'),
        'links': shutil.which('links') or shutil.which('links2'),
        'elinks': shutil.which('elinks')
    }
    return {k: v for k, v in browsers.items() if v}


def get_preferred_browser() -> Optional[str]:
    """Get preferred browser from environment or auto-detect

    Returns:
        Browser command name or None if no browser found
    """
    import shutil

    # Check environment variable first
    env_browser = os.getenv('BROWSER')
    if env_browser and shutil.which(env_browser):
        return env_browser

    # Default priority: w3m > lynx > links > elinks
    for browser in ['w3m', 'lynx', 'links', 'elinks']:
        if shutil.which(browser):
            return browser

    return None


def launch_browser(url: Optional[str] = None, browser: Optional[str] = None) -> bool:
    """Launch terminal browser with optional URL

    Args:
        url: Optional URL to open
        browser: Optional browser command (auto-detected if None)

    Returns:
        True if browser launched successfully, False otherwise
    """
    import subprocess

    if browser is None:
        browser = get_preferred_browser()

    if not browser:
        return False

    try:
        cmd = [browser]
        if url:
            cmd.append(url)

        subprocess.run(cmd, check=False)
        return True
    except Exception:
        return False


def is_tmux_available() -> bool:
    """Check if tmux is installed and available"""
    import shutil
    return shutil.which('tmux') is not None


def is_in_tmux() -> bool:
    """Check if currently running inside a tmux session"""
    return os.getenv('TMUX') is not None


def get_tmux_browser_windows() -> List[str]:
    """Get list of tmux windows that contain browsers

    Returns:
        List of window names that start with 'browser-'
    """
    import subprocess

    if not is_in_tmux():
        return []

    try:
        result = subprocess.run(
            ['tmux', 'list-windows', '-F', '#{window_name}'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            windows = result.stdout.strip().split('\n')
            return [w for w in windows if w.startswith('browser-')]
        return []
    except Exception:
        return []


def launch_browser_in_tmux(browser: str, url: str = None) -> bool:
    """Launch browser in a new tmux window

    Args:
        browser: Browser command to run
        url: Optional URL to open

    Returns:
        True if browser launched successfully in tmux
    """
    import subprocess

    if not is_in_tmux():
        return False

    cmd = [browser]
    if url and url.strip():
        cmd.append(url.strip())

    # Create window name
    from datetime import datetime
    window_name = f"browser-{browser}"

    try:
        # Create new tmux window with the browser
        # -n: window name
        # -d: don't switch to the new window (stay in current window)
        subprocess.run(
            ['tmux', 'new-window', '-n', window_name] + cmd,
            check=False
        )
        return True
    except Exception:
        return False


def switch_to_tmux_window(window_name: str) -> bool:
    """Switch to a specific tmux window

    Args:
        window_name: Name of the window to switch to

    Returns:
        True if successfully switched
    """
    import subprocess

    if not is_in_tmux():
        return False

    try:
        subprocess.run(['tmux', 'select-window', '-t', window_name], check=False)
        return True
    except Exception:
        return False


class BrowserSession:
    """Manages browser session state and last used configuration"""

    def __init__(self):
        self.browser = None
        self.url = None
        self.last_used_time = None
        self.tmux_window = None

    def has_recent_session(self) -> bool:
        """Check if there's a recent browser session (within last hour)"""
        if self.browser is None or self.last_used_time is None:
            return False

        from datetime import datetime, timedelta
        # Consider session recent if used within last hour
        return datetime.now() - self.last_used_time < timedelta(hours=1)

    def has_active_tmux_window(self) -> bool:
        """Check if there's an active tmux window with browser"""
        if not self.tmux_window:
            return False

        active_windows = get_tmux_browser_windows()
        return self.tmux_window in active_windows

    def launch(self, browser: str, url: str = None, use_tmux: bool = False) -> bool:
        """Launch browser with direct terminal access or in tmux

        Args:
            browser: Browser command to run
            url: Optional URL to open
            use_tmux: If True and tmux is available, launch in new tmux window

        Returns:
            True if browser launched successfully
        """
        import subprocess
        from datetime import datetime

        # Try tmux launch if requested and available
        if use_tmux and is_in_tmux():
            if launch_browser_in_tmux(browser, url):
                self.browser = browser
                self.url = url if url and url.strip() else "Home page"
                self.last_used_time = datetime.now()
                self.tmux_window = f"browser-{browser}"
                return True

        # Fallback to regular launch
        cmd = [browser]
        if url and url.strip():
            cmd.append(url.strip())

        try:
            # Launch browser with direct terminal access (no pipe redirects)
            # This allows the browser to properly interact with the terminal
            subprocess.run(cmd, check=False)

            # Update session info after browser exits
            self.browser = browser
            self.url = url if url and url.strip() else "Home page"
            self.last_used_time = datetime.now()
            self.tmux_window = None
            return True
        except Exception:
            return False

    def switch_to_browser(self) -> bool:
        """Switch to the tmux window containing the browser

        Returns:
            True if successfully switched to browser window
        """
        if not self.tmux_window:
            return False

        return switch_to_tmux_window(self.tmux_window)

    def clear(self):
        """Clear session information"""
        self.browser = None
        self.url = None
        self.last_used_time = None
        self.tmux_window = None

    def get_info(self) -> Dict[str, Any]:
        """Get browser session information

        Returns:
            Dictionary with browser session info
        """
        if not self.has_recent_session():
            return {}

        from datetime import datetime
        time_ago = datetime.now() - self.last_used_time if self.last_used_time else None

        info = {
            'browser': self.browser,
            'url': self.url,
            'last_used': self.last_used_time,
            'time_ago': time_ago,
            'in_tmux': self.tmux_window is not None,
            'tmux_active': self.has_active_tmux_window()
        }

        return info


# Global browser session instance
_browser_session = None


def get_browser_session() -> BrowserSession:
    """Get the global browser session instance"""
    global _browser_session
    if _browser_session is None:
        _browser_session = BrowserSession()
    return _browser_session
