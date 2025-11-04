"""
CLI decorators for common functionality
"""

import functools
import click
from pathlib import Path
from leadsauce.utils.config import get_config
from leadsauce.utils.constants import SESSION_FILE


def require_auth(func):
    """Decorator to require authentication for a command"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()

        # Check if user is authenticated
        if not is_authenticated(ctx):
            click.secho("✗ Authentication required. Please login first.", fg='red')
            click.secho("  Run: leadsauce auth login", fg='yellow')
            raise click.Abort()

        # Load user ID into context
        user_id = get_current_user_id(ctx)
        if user_id is None:
            click.secho("✗ Invalid session. Please login again.", fg='red')
            raise click.Abort()

        ctx.obj['user_id'] = user_id

        return func(*args, **kwargs)

    return wrapper


def handle_errors(func):
    """Decorator to handle common errors"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except click.Abort:
            raise
        except KeyboardInterrupt:
            click.echo("\n\nOperation cancelled by user.")
            raise click.Abort()
        except Exception as e:
            click.secho(f"\n✗ Error: {str(e)}", fg='red')
            config = get_config()
            if config.get('logging.level') == 'DEBUG':
                import traceback
                click.echo(traceback.format_exc())
            raise click.Abort()

    return wrapper


def with_database(func):
    """Decorator to provide database session"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from leadsauce.utils.db import DatabaseSession

        ctx = click.get_current_context()

        with DatabaseSession() as session:
            ctx.obj['db'] = session
            return func(*args, **kwargs)

    return wrapper


def confirm_action(message: str = "Are you sure?"):
    """Decorator to confirm action before execution"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if --force flag is present
            ctx = click.get_current_context()
            if 'force' in kwargs and kwargs.get('force'):
                return func(*args, **kwargs)

            # Check config for confirmation setting
            config = get_config()
            if not config.get('preferences.confirm_delete', True):
                return func(*args, **kwargs)

            if not click.confirm(message):
                click.echo("Operation cancelled.")
                raise click.Abort()

            return func(*args, **kwargs)

        return wrapper

    return decorator


def is_authenticated(ctx) -> bool:
    """Check if user is authenticated"""
    if SESSION_FILE.exists():
        try:
            import json
            with open(SESSION_FILE, 'r') as f:
                session = json.load(f)
                return session.get('user_id') is not None
        except Exception:
            return False
    return False


def get_current_user_id(ctx) -> int:
    """Get current user ID from session"""
    if SESSION_FILE.exists():
        try:
            import json
            with open(SESSION_FILE, 'r') as f:
                session = json.load(f)
                return session.get('user_id')
        except Exception:
            return None
    return None


def save_session(user_id: int, email: str, token: str = None):
    """Save user session"""
    import json
    from datetime import datetime

    session = {
        'user_id': user_id,
        'email': email,
        'token': token,
        'created_at': datetime.utcnow().isoformat()
    }

    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, 'w') as f:
        json.dump(session, f, indent=2)


def clear_session():
    """Clear user session"""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def get_session():
    """Get current session"""
    if SESSION_FILE.exists():
        try:
            import json
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None
