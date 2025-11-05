"""
Goal management commands
"""

import click
import json
from datetime import datetime
from tabulate import tabulate
from sqlalchemy import or_
from leadsauce.utils.db import get_session
from leadsauce.utils.validators import parse_tags, validate_date
from leadsauce.utils.formatters import print_success, print_error, print_info, format_date
from leadsauce.utils.constants import REMINDER_PRIORITIES
from leadsauce.models.goal import Goal
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.task import Task
from leadsauce.models.tag import Tag


@click.group()
def goal():
    """Goal management commands"""
    pass


@goal.command('create')
@click.option('--title', required=True, help='Goal title')
@click.option('--description', help='Goal description')
@click.option('--priority', type=click.Choice(REMINDER_PRIORITIES, case_sensitive=False), default='medium', help='Priority level')
@click.option('--target-date', help='Target completion date (YYYY-MM-DD or relative like +30d)')
@click.option('--profiles', help='Comma-separated profile IDs or names')
@click.option('--companies', help='Comma-separated company IDs or names')
@click.option('--tasks', help='Comma-separated task IDs')
@click.option('--tags', help='Comma-separated tags')
@click.option('--interactive', is_flag=True, help='Interactive mode')
def create_goal(title, description, priority, target_date, profiles, companies, tasks, tags, interactive):
    """Create a new goal"""

    if interactive:
        title = click.prompt('Goal Title', default=title if title else '')
        description = click.prompt('Description (optional)', default=description if description else '', show_default=False)
        priority = click.prompt('Priority', type=click.Choice(REMINDER_PRIORITIES), default=priority if priority else 'medium')
        target_date = click.prompt('Target Date (optional, e.g., 2024-12-31 or +30d)', default=target_date if target_date else '', show_default=False)
        profiles = click.prompt('Profile IDs/names (comma-separated, optional)', default=profiles if profiles else '', show_default=False)
        companies = click.prompt('Company IDs/names (comma-separated, optional)', default=companies if companies else '', show_default=False)
        tasks = click.prompt('Task IDs (comma-separated, optional)', default=tasks if tasks else '', show_default=False)
        tags = click.prompt('Tags (comma-separated, optional)', default=tags if tags else '', show_default=False)

    # Parse target date
    parsed_target_date = None
    if target_date:
        parsed_target_date = validate_date(target_date)
        if not parsed_target_date:
            print_error("Invalid target date format. Use YYYY-MM-DD or relative format like +30d")
            raise click.Abort()

    try:
        session = get_session()

        # Create the goal
        new_goal = Goal(
            title=title,
            description=description,
            priority=priority.lower() if priority else 'medium',
            target_date=parsed_target_date
        )

        session.add(new_goal)
        session.flush()

        # Link profiles
        if profiles:
            profile_list = [p.strip() for p in profiles.split(',')]
            for profile_ref in profile_list:
                profile_obj = None
                if profile_ref.isdigit():
                    profile_obj = session.query(Profile).filter(Profile.id == int(profile_ref)).first()
                else:
                    profile_obj = session.query(Profile).filter(
                        or_(
                            Profile.name.ilike(f"%{profile_ref}%"),
                            Profile.email.ilike(f"%{profile_ref}%")
                        )
                    ).first()

                if profile_obj:
                    new_goal.profiles.append(profile_obj)
                    print_info(f"Linked profile: {profile_obj.name}")
                else:
                    print_error(f"Profile '{profile_ref}' not found")

        # Link companies
        if companies:
            company_list = [c.strip() for c in companies.split(',')]
            for company_ref in company_list:
                company_obj = None
                if company_ref.isdigit():
                    company_obj = session.query(Company).filter(Company.id == int(company_ref)).first()
                else:
                    company_obj = session.query(Company).filter(
                        Company.name.ilike(f"%{company_ref}%")
                    ).first()

                if company_obj:
                    new_goal.companies.append(company_obj)
                    print_info(f"Linked company: {company_obj.name}")
                else:
                    print_error(f"Company '{company_ref}' not found")

        # Link tasks
        if tasks:
            task_list = [t.strip() for t in tasks.split(',')]
            for task_id in task_list:
                if task_id.isdigit():
                    task_obj = session.query(Task).filter(Task.id == int(task_id)).first()
                    if task_obj:
                        new_goal.tasks.append(task_obj)
                        print_info(f"Linked task: {task_obj.title}")
                    else:
                        print_error(f"Task ID {task_id} not found")

        # Link tags
        if tags:
            tag_list = parse_tags(tags)
            for tag_name in tag_list:
                tag_obj = session.query(Tag).filter(Tag.name.ilike(tag_name)).first()
                if not tag_obj:
                    tag_obj = Tag(name=tag_name)
                    session.add(tag_obj)
                    session.flush()
                new_goal.tags.append(tag_obj)

        # Update progress based on linked tasks
        new_goal.update_progress()

        session.commit()

        print_success(f"Goal created successfully! ID: {new_goal.id}")
        print_info(f"Progress: {new_goal.progress}%")

    except Exception as e:
        session.rollback()
        print_error(f"Failed to create goal: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@goal.command('list')
@click.option('--status', help='Filter by status (active, completed, on_hold, cancelled)')
@click.option('--priority', type=click.Choice(REMINDER_PRIORITIES, case_sensitive=False), help='Filter by priority')
@click.option('--overdue', is_flag=True, help='Show only overdue goals')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
def list_goals(status, priority, overdue, output_format):
    """List all goals"""

    try:
        session = get_session()

        query = session.query(Goal)

        # Apply filters
        if status:
            query = query.filter(Goal.status == status)

        if priority:
            query = query.filter(Goal.priority == priority.lower())

        goals = query.order_by(Goal.created_at.desc()).all()

        # Filter overdue if requested
        if overdue:
            goals = [g for g in goals if g.is_overdue()]

        if not goals:
            print_info("No goals found")
            return

        # Format output
        if output_format == 'json':
            goal_data = [g.to_dict(include_relations=True) for g in goals]
            click.echo(json.dumps(goal_data, indent=2))
        elif output_format == 'csv':
            click.echo("ID,Title,Status,Priority,Progress,Target Date,Profiles,Companies,Tasks,Tags")
            for g in goals:
                profiles_count = len(g.profiles)
                companies_count = len(g.companies)
                tasks_count = len(g.tasks)
                tags_count = len(g.tags)
                target = format_date(g.target_date) if g.target_date else 'N/A'
                click.echo(f"{g.id},{g.title},{g.status},{g.priority},{g.progress}%,{target},{profiles_count},{companies_count},{tasks_count},{tags_count}")
        else:
            # Table format
            table_data = []
            for g in goals:
                summary = g.get_summary()
                target = format_date(g.target_date) if g.target_date else 'N/A'
                status_display = g.status
                if g.is_overdue():
                    status_display = f"{g.status} (OVERDUE)"

                table_data.append([
                    g.id,
                    g.title[:40] + '...' if len(g.title) > 40 else g.title,
                    status_display,
                    g.priority,
                    f"{g.progress}%",
                    f"{summary['completed_tasks']}/{summary['total_tasks']}",
                    summary['total_profiles'],
                    summary['total_companies'],
                    target
                ])

            headers = ['ID', 'Title', 'Status', 'Priority', 'Progress', 'Tasks', 'Profiles', 'Companies', 'Target Date']
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
            print_info(f"Total goals: {len(goals)}")

    except Exception as e:
        print_error(f"Failed to list goals: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@goal.command('show')
@click.argument('goal_id', type=int)
def show_goal(goal_id):
    """Show detailed information about a goal"""

    try:
        session = get_session()

        goal_obj = session.query(Goal).filter(Goal.id == goal_id).first()

        if not goal_obj:
            print_error(f"Goal ID {goal_id} not found")
            raise click.Abort()

        summary = goal_obj.get_summary()

        click.echo(f"\n{'='*60}")
        click.echo(f"Goal #{goal_obj.id}: {goal_obj.title}")
        click.echo(f"{'='*60}\n")

        click.echo(f"Description: {goal_obj.description or 'N/A'}")
        click.echo(f"Status: {goal_obj.status}")
        click.echo(f"Priority: {goal_obj.priority}")
        click.echo(f"Progress: {goal_obj.progress}%")
        click.echo(f"Target Date: {format_date(goal_obj.target_date) if goal_obj.target_date else 'N/A'}")
        if goal_obj.is_overdue():
            print_error("⚠ OVERDUE")

        click.echo(f"\n{'─'*60}")
        click.echo("RELATED ENTITIES:")
        click.echo(f"{'─'*60}\n")

        # Tasks
        click.echo(f"Tasks ({summary['total_tasks']} total):")
        if goal_obj.tasks:
            task_table = []
            for task in goal_obj.tasks:
                task_table.append([task.id, task.title[:40], task.status, task.priority])
            click.echo(tabulate(task_table, headers=['ID', 'Title', 'Status', 'Priority'], tablefmt='grid'))
            click.echo(f"  ✓ Completed: {summary['completed_tasks']}")
            click.echo(f"  ⟳ In Progress: {summary['in_progress_tasks']}")
            click.echo(f"  ○ Pending: {summary['pending_tasks']}")
        else:
            click.echo("  No tasks linked")

        # Profiles
        click.echo(f"\nProfiles ({summary['total_profiles']} total):")
        if goal_obj.profiles:
            profile_table = [[p.id, p.name, p.email or 'N/A'] for p in goal_obj.profiles]
            click.echo(tabulate(profile_table, headers=['ID', 'Name', 'Email'], tablefmt='grid'))
        else:
            click.echo("  No profiles linked")

        # Companies
        click.echo(f"\nCompanies ({summary['total_companies']} total):")
        if goal_obj.companies:
            company_table = [[c.id, c.name, c.industry or 'N/A'] for c in goal_obj.companies]
            click.echo(tabulate(company_table, headers=['ID', 'Name', 'Industry'], tablefmt='grid'))
        else:
            click.echo("  No companies linked")

        # Tags
        click.echo(f"\nTags ({summary['total_tags']} total):")
        if goal_obj.tags:
            tag_names = ', '.join([t.name for t in goal_obj.tags])
            click.echo(f"  {tag_names}")
        else:
            click.echo("  No tags linked")

        click.echo(f"\n{'─'*60}")
        click.echo(f"Created: {format_date(goal_obj.created_at)}")
        click.echo(f"Updated: {format_date(goal_obj.updated_at)}")
        if goal_obj.completed_at:
            click.echo(f"Completed: {format_date(goal_obj.completed_at)}")
        click.echo(f"{'='*60}\n")

    except Exception as e:
        print_error(f"Failed to show goal: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@goal.command('update')
@click.argument('goal_id', type=int)
@click.option('--title', help='Update title')
@click.option('--description', help='Update description')
@click.option('--status', type=click.Choice(['active', 'completed', 'on_hold', 'cancelled']), help='Update status')
@click.option('--priority', type=click.Choice(REMINDER_PRIORITIES, case_sensitive=False), help='Update priority')
@click.option('--target-date', help='Update target date')
@click.option('--refresh-progress', is_flag=True, help='Recalculate progress from tasks')
def update_goal(goal_id, title, description, status, priority, target_date, refresh_progress):
    """Update an existing goal"""

    try:
        session = get_session()

        goal_obj = session.query(Goal).filter(Goal.id == goal_id).first()

        if not goal_obj:
            print_error(f"Goal ID {goal_id} not found")
            raise click.Abort()

        # Update fields
        if title:
            goal_obj.title = title
        if description:
            goal_obj.description = description
        if status:
            goal_obj.status = status
            if status == 'completed':
                goal_obj.complete()
        if priority:
            goal_obj.priority = priority.lower()
        if target_date:
            parsed_date = validate_date(target_date)
            if parsed_date:
                goal_obj.target_date = parsed_date
            else:
                print_error("Invalid date format")
                raise click.Abort()

        # Refresh progress
        if refresh_progress or status or title or description:
            goal_obj.update_progress()

        session.commit()

        print_success(f"Goal ID {goal_id} updated successfully!")
        print_info(f"Current progress: {goal_obj.progress}%")

    except Exception as e:
        session.rollback()
        print_error(f"Failed to update goal: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@goal.command('delete')
@click.argument('goal_id', type=int)
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def delete_goal(goal_id, confirm):
    """Delete a goal"""

    try:
        session = get_session()

        goal_obj = session.query(Goal).filter(Goal.id == goal_id).first()

        if not goal_obj:
            print_error(f"Goal ID {goal_id} not found")
            raise click.Abort()

        if not confirm:
            if not click.confirm(f"Are you sure you want to delete goal '{goal_obj.title}'?"):
                print_info("Deletion cancelled")
                return

        session.delete(goal_obj)
        session.commit()

        print_success(f"Goal ID {goal_id} deleted successfully!")

    except Exception as e:
        session.rollback()
        print_error(f"Failed to delete goal: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@goal.command('link')
@click.argument('goal_id', type=int)
@click.option('--profile', 'profile_id', type=int, help='Link a profile by ID')
@click.option('--company', 'company_id', type=int, help='Link a company by ID')
@click.option('--task', 'task_id', type=int, help='Link a task by ID')
@click.option('--tag', 'tag_name', help='Link a tag by name')
def link_entity(goal_id, profile_id, company_id, task_id, tag_name):
    """Link a profile, company, task, or tag to a goal"""

    try:
        session = get_session()

        goal_obj = session.query(Goal).filter(Goal.id == goal_id).first()

        if not goal_obj:
            print_error(f"Goal ID {goal_id} not found")
            raise click.Abort()

        # Link profile
        if profile_id:
            profile_obj = session.query(Profile).filter(Profile.id == profile_id).first()
            if not profile_obj:
                print_error(f"Profile ID {profile_id} not found")
                raise click.Abort()

            if profile_obj in goal_obj.profiles:
                print_info(f"Profile '{profile_obj.name}' is already linked to this goal")
            else:
                goal_obj.profiles.append(profile_obj)
                print_success(f"Linked profile: {profile_obj.name}")

        # Link company
        if company_id:
            company_obj = session.query(Company).filter(Company.id == company_id).first()
            if not company_obj:
                print_error(f"Company ID {company_id} not found")
                raise click.Abort()

            if company_obj in goal_obj.companies:
                print_info(f"Company '{company_obj.name}' is already linked to this goal")
            else:
                goal_obj.companies.append(company_obj)
                print_success(f"Linked company: {company_obj.name}")

        # Link task
        if task_id:
            task_obj = session.query(Task).filter(Task.id == task_id).first()
            if not task_obj:
                print_error(f"Task ID {task_id} not found")
                raise click.Abort()

            if task_obj in goal_obj.tasks:
                print_info(f"Task '{task_obj.title}' is already linked to this goal")
            else:
                goal_obj.tasks.append(task_obj)
                print_success(f"Linked task: {task_obj.title}")
                # Update progress after linking a task
                goal_obj.update_progress()
                print_info(f"Updated progress: {goal_obj.progress}%")

        # Link tag
        if tag_name:
            tag_obj = session.query(Tag).filter(Tag.name.ilike(tag_name)).first()
            if not tag_obj:
                tag_obj = Tag(name=tag_name)
                session.add(tag_obj)
                session.flush()
                print_info(f"Created new tag: {tag_name}")

            if tag_obj in goal_obj.tags:
                print_info(f"Tag '{tag_obj.name}' is already linked to this goal")
            else:
                goal_obj.tags.append(tag_obj)
                print_success(f"Linked tag: {tag_obj.name}")

        session.commit()

    except Exception as e:
        session.rollback()
        print_error(f"Failed to link entity: {str(e)}")
        raise click.Abort()
    finally:
        session.close()


@goal.command('unlink')
@click.argument('goal_id', type=int)
@click.option('--profile', 'profile_id', type=int, help='Unlink a profile by ID')
@click.option('--company', 'company_id', type=int, help='Unlink a company by ID')
@click.option('--task', 'task_id', type=int, help='Unlink a task by ID')
@click.option('--tag', 'tag_name', help='Unlink a tag by name')
def unlink_entity(goal_id, profile_id, company_id, task_id, tag_name):
    """Unlink a profile, company, task, or tag from a goal"""

    try:
        session = get_session()

        goal_obj = session.query(Goal).filter(Goal.id == goal_id).first()

        if not goal_obj:
            print_error(f"Goal ID {goal_id} not found")
            raise click.Abort()

        # Unlink profile
        if profile_id:
            profile_obj = session.query(Profile).filter(Profile.id == profile_id).first()
            if profile_obj and profile_obj in goal_obj.profiles:
                goal_obj.profiles.remove(profile_obj)
                print_success(f"Unlinked profile: {profile_obj.name}")
            else:
                print_error(f"Profile not linked to this goal")

        # Unlink company
        if company_id:
            company_obj = session.query(Company).filter(Company.id == company_id).first()
            if company_obj and company_obj in goal_obj.companies:
                goal_obj.companies.remove(company_obj)
                print_success(f"Unlinked company: {company_obj.name}")
            else:
                print_error(f"Company not linked to this goal")

        # Unlink task
        if task_id:
            task_obj = session.query(Task).filter(Task.id == task_id).first()
            if task_obj and task_obj in goal_obj.tasks:
                goal_obj.tasks.remove(task_obj)
                print_success(f"Unlinked task: {task_obj.title}")
                # Update progress after unlinking a task
                goal_obj.update_progress()
                print_info(f"Updated progress: {goal_obj.progress}%")
            else:
                print_error(f"Task not linked to this goal")

        # Unlink tag
        if tag_name:
            tag_obj = session.query(Tag).filter(Tag.name.ilike(tag_name)).first()
            if tag_obj and tag_obj in goal_obj.tags:
                goal_obj.tags.remove(tag_obj)
                print_success(f"Unlinked tag: {tag_obj.name}")
            else:
                print_error(f"Tag not linked to this goal")

        session.commit()

    except Exception as e:
        session.rollback()
        print_error(f"Failed to unlink entity: {str(e)}")
        raise click.Abort()
    finally:
        session.close()
