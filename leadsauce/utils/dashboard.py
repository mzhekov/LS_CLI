"""
Dashboard utilities for displaying overview with rich TUI
"""

import click
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich import box
from leadsauce.utils.db import get_session
from leadsauce.models.profile import Profile
from leadsauce.models.company import Company
from leadsauce.models.tag import Tag
from leadsauce.models.interaction import Interaction
from leadsauce.models.reminder import Reminder
from leadsauce.models.goal import Goal
from leadsauce.models.task import Task

console = Console()


def show_dashboard():
    """Display main dashboard with stats and overview"""
    session = get_session()

    try:
        # Get stats
        total_profiles = session.query(Profile).count()
        total_companies = session.query(Company).count()
        total_tags = session.query(Tag).count()
        total_interactions = session.query(Interaction).count()

        # Get active reminders
        active_reminders = session.query(Reminder).filter(
            Reminder.completed == False
        ).count()

        # Get overdue reminders
        overdue_reminders = session.query(Reminder).filter(
            Reminder.completed == False,
            Reminder.reminder_date < datetime.utcnow()
        ).count()

        # Get today's reminders
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_reminders = session.query(Reminder).filter(
            Reminder.completed == False,
            Reminder.reminder_date >= today_start,
            Reminder.reminder_date < today_end
        ).count()

        # Recent profiles (last 5)
        recent_profiles = session.query(Profile).order_by(
            Profile.created_at.desc()
        ).limit(5).all()

        # Clear screen for better presentation
        console.clear()
        console.print()

        # Header
        header = Text("LeadSauce CLI", style="bold cyan", justify="center")
        subtitle = Text("Professional Network Management", style="dim", justify="center")
        console.print(Panel(
            Text.assemble(header, "\n", subtitle),
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()

        # Stats Section - Using Columns for side-by-side display
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_column(justify="left", style="cyan")
        stats_table.add_column(justify="right", style="bold white")
        stats_table.add_column(justify="left", style="cyan")
        stats_table.add_column(justify="right", style="bold white")

        stats_table.add_row("👥 Profiles", str(total_profiles), "🏢 Companies", str(total_companies))
        stats_table.add_row("💬 Interactions", str(total_interactions), "🏷️  Tags", str(total_tags))

        console.print(Panel(stats_table, title="[bold yellow]📊 Overview[/]", border_style="yellow"))
        console.print()

        # Goals Section
        total_goals = session.query(Goal).count()
        active_goals = session.query(Goal).filter(Goal.status == 'active').count()
        completed_goals = session.query(Goal).filter(Goal.status == 'completed').count()

        # Get overdue goals
        overdue_goals = session.query(Goal).filter(
            Goal.status == 'active',
            Goal.target_date < datetime.utcnow()
        ).count()

        # Get goals with their progress
        goals_in_progress = session.query(Goal).filter(
            Goal.status == 'active'
        ).order_by(Goal.target_date.asc()).limit(5).all()

        if total_goals > 0:
            goals_table = Table(show_header=True, box=box.SIMPLE_HEAD, padding=(0, 1))
            goals_table.add_column("Goal", style="cyan", width=30)
            goals_table.add_column("Progress", style="green", width=12)
            goals_table.add_column("Tasks", style="magenta", width=10)
            goals_table.add_column("Target", style="dim", width=12)

            for goal in goals_in_progress:
                # Format target date
                if goal.target_date:
                    days_until = (goal.target_date - datetime.utcnow()).days
                    if days_until < 0:
                        target_str = f"[red]{abs(days_until)}d ago[/]"
                    elif days_until == 0:
                        target_str = "[yellow]today[/]"
                    elif days_until == 1:
                        target_str = "[yellow]tomorrow[/]"
                    else:
                        target_str = f"[dim]{days_until}d[/]"
                else:
                    target_str = "N/A"

                # Format progress bar
                progress_bar = "█" * int(goal.progress / 10) + "░" * (10 - int(goal.progress / 10))
                progress_str = f"{progress_bar} {goal.progress:.0f}%"

                # Task summary
                summary = goal.get_summary()
                task_str = f"{summary['completed_tasks']}/{summary['total_tasks']}"

                # Truncate title if too long
                title = goal.title[:27] + "..." if len(goal.title) > 27 else goal.title

                goals_table.add_row(title, progress_str, task_str, target_str)

            # Add stats row
            stats_text = f"[bold]Total:[/] {total_goals} | [green]Completed:[/] {completed_goals} | [yellow]Active:[/] {active_goals}"
            if overdue_goals > 0:
                stats_text += f" | [red]Overdue:[/] {overdue_goals}"

            console.print(Panel(
                goals_table,
                title=f"[bold yellow]🎯 Goals[/]",
                subtitle=stats_text,
                border_style="yellow"
            ))
            console.print()
        else:
            # Show placeholder if no goals
            goals_placeholder = Table(show_header=False, box=None, padding=(0, 2))
            goals_placeholder.add_column(justify="center", style="dim")
            goals_placeholder.add_row("No goals yet. Create your first goal to get started!")
            goals_placeholder.add_row("[cyan]leadsauce goal create --interactive[/]")

            console.print(Panel(goals_placeholder, title="[bold yellow]🎯 Goals[/]", border_style="yellow"))
            console.print()

        # Upcoming Tasks Section
        from sqlalchemy import and_, or_

        # Get upcoming/pending tasks (not completed or cancelled)
        upcoming_tasks = session.query(Task).filter(
            Task.status.in_(['pending', 'in_progress'])
        ).order_by(
            Task.due_date.asc().nullslast(),
            Task.priority.desc(),
            Task.created_at.asc()
        ).limit(5).all()

        total_tasks = session.query(Task).count()
        pending_tasks = session.query(Task).filter(Task.status == 'pending').count()
        in_progress_tasks = session.query(Task).filter(Task.status == 'in_progress').count()
        completed_tasks = session.query(Task).filter(Task.status == 'completed').count()

        # Get overdue tasks
        overdue_tasks_count = session.query(Task).filter(
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date < datetime.utcnow()
        ).count()

        if total_tasks > 0:
            tasks_table = Table(show_header=True, box=box.SIMPLE_HEAD, padding=(0, 1))
            tasks_table.add_column("Task", style="cyan", width=35)
            tasks_table.add_column("Status", style="blue", width=12)
            tasks_table.add_column("Priority", style="yellow", width=8)
            tasks_table.add_column("Due", style="dim", width=12)
            tasks_table.add_column("Goals", style="green", width=6)

            for task in upcoming_tasks:
                # Format status
                status_str = task.status.replace('_', ' ').title()
                if task.is_overdue():
                    status_str = f"[red]{status_str} ⚠[/]"

                # Format due date
                if task.due_date:
                    days_until = (task.due_date - datetime.utcnow()).days
                    if days_until < 0:
                        due_str = f"[red]{abs(days_until)}d ago[/]"
                    elif days_until == 0:
                        due_str = "[yellow]Today[/]"
                    elif days_until == 1:
                        due_str = "[yellow]Tomorrow[/]"
                    elif days_until <= 7:
                        due_str = f"[yellow]{days_until}d[/]"
                    else:
                        due_str = f"[dim]{days_until}d[/]"
                else:
                    due_str = "-"

                # Count linked goals
                goals_count = len(task.goals) if hasattr(task, 'goals') else 0
                goals_str = str(goals_count) if goals_count > 0 else "-"

                # Truncate title
                title = task.title[:33] + "..." if len(task.title) > 33 else task.title

                tasks_table.add_row(
                    title,
                    status_str,
                    task.priority.title(),
                    due_str,
                    goals_str
                )

            # Add stats
            stats_text = f"[bold]Total:[/] {total_tasks} | [cyan]Pending:[/] {pending_tasks} | [yellow]In Progress:[/] {in_progress_tasks} | [green]Completed:[/] {completed_tasks}"
            if overdue_tasks_count > 0:
                stats_text += f" | [red]Overdue:[/] {overdue_tasks_count}"

            console.print(Panel(
                tasks_table,
                title="[bold yellow]📋 Upcoming Tasks[/]",
                subtitle=stats_text,
                border_style="yellow"
            ))
            console.print()
        else:
            # Show placeholder if no tasks
            tasks_placeholder = Table(show_header=False, box=None, padding=(0, 2))
            tasks_placeholder.add_column(justify="center", style="dim")
            tasks_placeholder.add_row("No tasks yet. Tasks can be linked to goals for progress tracking!")
            tasks_placeholder.add_row("[cyan]Create tasks in the TUI Workshop menu[/]")

            console.print(Panel(tasks_placeholder, title="[bold yellow]📋 Upcoming Tasks[/]", border_style="yellow"))
            console.print()

        # Reminders Section
        reminders_table = Table(show_header=False, box=None, padding=(0, 2))
        reminders_table.add_column(justify="left", width=20)
        reminders_table.add_column(justify="right", style="bold")

        if overdue_reminders > 0:
            reminders_table.add_row("⚠️  Overdue", f"[bold red]{overdue_reminders}[/]")
        else:
            reminders_table.add_row("✓ Overdue", f"[green]{overdue_reminders}[/]")

        if today_reminders > 0:
            reminders_table.add_row("📅 Today", f"[yellow]{today_reminders}[/]")
        else:
            reminders_table.add_row("📅 Today", f"[dim]{today_reminders}[/]")

        reminders_table.add_row("📝 Total Active", str(active_reminders))

        console.print(Panel(reminders_table, title="[bold yellow]⏰ Reminders[/]", border_style="yellow"))
        console.print()

        # Recent Profiles Section
        if recent_profiles:
            profiles_table = Table(show_header=True, box=box.SIMPLE_HEAD, padding=(0, 1))
            profiles_table.add_column("Name", style="cyan")
            profiles_table.add_column("Seniority", style="magenta")
            profiles_table.add_column("Company", style="blue")
            profiles_table.add_column("Added", style="dim")

            for profile in recent_profiles:
                # Format date
                days_ago = (datetime.utcnow() - profile.created_at).days
                if days_ago == 0:
                    date_str = "today"
                elif days_ago == 1:
                    date_str = "yesterday"
                else:
                    date_str = f"{days_ago}d ago"

                # Format company
                company_str = profile.company.name if profile.company else "-"

                profiles_table.add_row(
                    profile.name,
                    profile.seniority,
                    company_str,
                    date_str
                )

            console.print(Panel(profiles_table, title="[bold yellow]👥 Recent Profiles[/]", border_style="yellow"))
            console.print()

        # Quick Commands Section
        commands_table = Table(show_header=False, box=None, padding=(0, 1))
        commands_table.add_column(style="cyan", width=35)
        commands_table.add_column(style="dim")

        commands_table.add_row("leadsauce profile create", "Create a new profile")
        commands_table.add_row("leadsauce goal create", "Create a new goal")
        commands_table.add_row("leadsauce goal list", "List all goals")
        commands_table.add_row("leadsauce company list", "List all companies")
        commands_table.add_row("leadsauce --help", "Show all commands")

        console.print(Panel(commands_table, title="[bold yellow]💡 Quick Commands[/]", border_style="yellow"))
        console.print()

        # Status message
        if overdue_reminders > 0:
            console.print(Panel(
                "[bold red]⚠️  You have overdue reminders![/]\n"
                "[yellow]Run:[/] [cyan]leadsauce reminder list --overdue[/]",
                border_style="red",
                padding=(0, 2)
            ))
        elif total_profiles == 0:
            console.print(Panel(
                "[bold green]🚀 Get started by creating your first profile![/]\n"
                "[yellow]Run:[/] [cyan]leadsauce profile create --interactive[/]",
                border_style="green",
                padding=(0, 2)
            ))
        else:
            console.print("[dim]✨ Everything looks good! Keep building your network.[/]")

        console.print()

    except Exception as e:
        console.print(f"[red]Error loading dashboard: {str(e)}[/]")
    finally:
        session.close()


def show_mini_dashboard():
    """Display minimal dashboard (for quick view)"""
    session = get_session()

    try:
        total_profiles = session.query(Profile).count()
        total_companies = session.query(Company).count()
        overdue_reminders = session.query(Reminder).filter(
            Reminder.completed == False,
            Reminder.reminder_date < datetime.utcnow()
        ).count()

        console.print()
        console.print("[bold cyan]LeadSauce CLI[/]")
        console.print(f"[dim]📊 {total_profiles} profiles · {total_companies} companies[/]")

        if overdue_reminders > 0:
            console.print(f"[red]⚠️  {overdue_reminders} overdue reminders[/]")

        console.print()
        console.print("[dim]Run[/] [cyan]'leadsauce dashboard'[/] [dim]for full overview[/]")
        console.print("[dim]Run[/] [cyan]'leadsauce --help'[/] [dim]for all commands[/]")
        console.print()

    except Exception:
        pass
    finally:
        session.close()


def show_welcome():
    """Show welcome message for first-time users"""
    console.print()
    console.print(Panel(
        "[bold cyan]Welcome to LeadSauce CLI![/]\n\n"
        "Professional network management from your terminal.\n\n"
        "[yellow]Quick Start:[/]\n"
        "  1. [cyan]leadsauce profile create --interactive[/]\n"
        "  2. [cyan]leadsauce profile list[/]\n"
        "  3. [cyan]leadsauce dashboard[/]\n\n"
        "[dim]Run[/] [cyan]leadsauce --help[/] [dim]for all commands[/]",
        title="[bold green]🎉 Getting Started[/]",
        border_style="green",
        padding=(1, 2)
    ))
    console.print()
