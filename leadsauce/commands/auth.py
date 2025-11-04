"""
Authentication commands
"""

import click
from datetime import datetime
from leadsauce.utils.db import get_session
from leadsauce.utils.helpers import hash_password, verify_password
from leadsauce.utils.validators import validate_email, validate_password
from leadsauce.utils.decorators import save_session, clear_session, get_session as get_session_data, require_auth
from leadsauce.utils.formatters import print_success, print_error, print_info
from leadsauce.models.user import User


@click.group()
def auth():
    """Authentication and user management"""
    pass


@auth.command('register')
@click.option('--email', prompt=True, help='Email address')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
@click.option('--first-name', help='First name')
@click.option('--last-name', help='Last name')
@click.pass_context
def register(ctx, email, password, first_name, last_name):
    """Register a new user account"""

    # Validate email
    if not validate_email(email):
        print_error("Invalid email address")
        raise click.Abort()

    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        print_error(error_msg)
        raise click.Abort()

    try:
        session = get_session()

        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            print_error(f"User with email '{email}' already exists")
            raise click.Abort()

        # Create new user
        hashed_password = hash_password(password)
        new_user = User(
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_verified=False
        )

        session.add(new_user)
        session.commit()

        print_success(f"Account created successfully for {email}")
        print_info("Please login to start using LeadSauce CLI")
        click.echo(f"  Run: leadsauce auth login --email {email}")

    except Exception as e:
        print_error(f"Registration failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@auth.command('login')
@click.option('--email', prompt=True, help='Email address')
@click.option('--password', prompt=True, hide_input=True, help='Password')
@click.pass_context
def login(ctx, email, password):
    """Login to your account"""

    try:
        session = get_session()

        # Find user
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print_error("Invalid email or password")
            raise click.Abort()

        # Verify password
        if not verify_password(password, user.password_hash):
            print_error("Invalid email or password")
            raise click.Abort()

        # Check if user is active
        if not user.is_active:
            print_error("Account is disabled. Please contact support.")
            raise click.Abort()

        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()

        # Save session
        save_session(user.id, user.email)

        print_success(f"Logged in as {email}")

        # Show quick start tips
        click.echo()
        print_info("Quick start:")
        click.echo("  • Create a profile:    leadsauce profile create --name 'John Doe' --seniority executive")
        click.echo("  • List profiles:       leadsauce profile list")
        click.echo("  • View dashboard:      leadsauce insights dashboard")
        click.echo("  • Get help:            leadsauce --help")

    except Exception as e:
        print_error(f"Login failed: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@auth.command('logout')
@require_auth
@click.pass_context
def logout(ctx):
    """Logout from your account"""

    try:
        session_data = get_session_data()
        email = session_data.get('email') if session_data else 'current user'

        clear_session()

        print_success(f"Logged out successfully")
        click.echo(f"Goodbye, {email}!")

    except Exception as e:
        print_error(f"Logout failed: {str(e)}")
        raise click.Abort()


@auth.command('whoami')
@require_auth
@click.pass_context
def whoami(ctx):
    """Show current user information"""

    try:
        session_data = get_session_data()
        if not session_data:
            print_error("No active session")
            raise click.Abort()

        db_session = get_session()
        user = db_session.query(User).filter(User.id == session_data['user_id']).first()

        if not user:
            print_error("User not found")
            raise click.Abort()

        click.echo()
        click.secho(f"Logged in as:", fg='cyan', bold=True)
        click.echo(f"  Email:             {user.email}")
        if user.first_name or user.last_name:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            click.echo(f"  Name:              {name}")
        click.echo(f"  User ID:           {user.id}")
        click.echo(f"  Subscription:      {user.subscription_tier}")
        click.echo(f"  Status:            {user.subscription_status}")
        click.echo(f"  Account created:   {user.created_at.strftime('%Y-%m-%d')}")
        if user.last_login:
            click.echo(f"  Last login:        {user.last_login.strftime('%Y-%m-%d %H:%M')}")
        click.echo()

        # Show statistics
        profile_count = len(user.profiles)
        company_count = len(user.companies)
        click.echo(f"  Profiles:          {profile_count}")
        click.echo(f"  Companies:         {company_count}")
        click.echo()

        db_session.close()

    except Exception as e:
        print_error(f"Error: {str(e)}")
        raise click.Abort()


@auth.command('status')
@click.pass_context
def status(ctx):
    """Check authentication status"""

    session_data = get_session_data()

    if session_data:
        email = session_data.get('email', 'Unknown')
        print_success(f"Authenticated as {email}")

        try:
            db_session = get_session()
            user = db_session.query(User).filter(User.id == session_data['user_id']).first()
            if user:
                click.echo(f"Subscription: {user.subscription_tier}")
            db_session.close()
        except Exception:
            pass
    else:
        print_info("Not authenticated")
        click.echo("Run: leadsauce auth login")


@auth.command('change-password')
@require_auth
@click.option('--old', 'old_password', prompt=True, hide_input=True, help='Current password')
@click.option('--new', 'new_password', prompt=True, hide_input=True, confirmation_prompt=True, help='New password')
@click.pass_context
def change_password(ctx, old_password, new_password):
    """Change your password"""

    # Validate new password
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        print_error(error_msg)
        raise click.Abort()

    try:
        session_data = get_session_data()
        db_session = get_session()

        user = db_session.query(User).filter(User.id == session_data['user_id']).first()
        if not user:
            print_error("User not found")
            raise click.Abort()

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            print_error("Current password is incorrect")
            raise click.Abort()

        # Update password
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db_session.commit()

        print_success("Password changed successfully")

        db_session.close()

    except Exception as e:
        print_error(f"Failed to change password: {str(e)}")
        raise click.Abort()


@auth.command('reset-password')
@click.option('--email', prompt=True, help='Email address')
@click.pass_context
def reset_password(ctx, email):
    """Request password reset (not implemented in CLI version)"""

    print_info("Password reset via CLI is not available")
    click.echo("For local installations, you can:")
    click.echo("  1. Create a new account")
    click.echo("  2. Manually reset the database")
    click.echo()
    click.echo("For cloud installations, please visit the web interface")
